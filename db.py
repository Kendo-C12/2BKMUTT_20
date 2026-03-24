"""
VAD Recorder v3 — Two-Phase Calibration + Live dB Meter
=========================================================
Calibration:
  Phase 1 — stay QUIET  → measures your background noise floor
  Phase 2 — SPEAK normally → measures your typical speech level
  → Computes a precise detection threshold at the midpoint (geometric mean)

Live monitor:
  Prints current dB level every 0.5 s with a bar-graph and SPEECH / silence tag
  so you can SEE the detector working in real time.

Detection layers:
  Layer 1 — WebRTC VAD        (Google's production VAD engine)
  Layer 2 — Adaptive Energy   (tracks noise floor continuously)
  Layer 3 — Zero-Crossing Rate (rejects impact noise / hum)

Dependencies:
    pip install webrtcvad-wheels pyaudio numpy

Usage:
    python vad_recorder.py                   # full calibration + adaptive
    python vad_recorder.py --no-calibration  # skip calibration, auto-adapt
    python vad_recorder.py --output-dir ./clips
    python vad_recorder.py --mode 1          # quieter WebRTC layer
    python vad_recorder.py --debug           # per-frame W/E/Z flags
"""

import argparse
import collections
import os
import sys
import time
import wave
from datetime import datetime

import io

from main import init_all, run_kmutt_assistant

try:
    import pyaudio
except ImportError:
    sys.exit("ERROR: pyaudio not found.  pip install pyaudio")

try:
    import webrtcvad
except ImportError:
    sys.exit("ERROR: webrtcvad not found.  pip install webrtcvad-wheels")

try:
    import numpy as np
except ImportError:
    sys.exit("ERROR: numpy not found.  pip install numpy")


# ─────────────────────────── Audio constants ────────────────────────────────
SAMPLE_RATE    = 16000
CHANNELS       = 1
SAMPLE_WIDTH   = 2
FRAME_DURATION = 30                                         # ms
FRAME_SIZE     = int(SAMPLE_RATE * FRAME_DURATION / 1000)  # samples
FRAME_BYTES    = FRAME_SIZE * SAMPLE_WIDTH                  # bytes

SPEECH_WIN_MS  = 300
SILENCE_WIN_MS = 1200
PRE_ROLL_MS    = 400

N_SPEECH  = SPEECH_WIN_MS  // FRAME_DURATION
N_SILENCE = SILENCE_WIN_MS // FRAME_DURATION
N_PREROLL = PRE_ROLL_MS    // FRAME_DURATION

NOISE_ALPHA_FAST = 0.15
NOISE_ALPHA_SLOW = 0.02
MIN_NOISE_RMS    = 30.0

ZCR_LOW  = 0.02
ZCR_HIGH = 0.35

# dB meter
DB_PRINT_INTERVAL = 0.5   # seconds
DB_BAR_WIDTH      = 30    # characters
DB_MIN            = -60   # dB floor for bar graph
DB_MAX            = 0     # dB ceiling (0 dBFS)

REF_RMS = 32768.0         # 16-bit full-scale reference for dBFS


# ─────────────────────────── Helpers ─────────────────────────────────────────
def rms_of(raw: bytes) -> float:
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    return float(np.sqrt(np.mean(samples ** 2))) if len(samples) else 0.0


def zcr_of(raw: bytes) -> float:
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
    signs = np.sign(samples)
    signs[signs == 0] = 1
    return float(np.sum(np.diff(signs) != 0) / len(samples))


def rms_to_db(rms: float) -> float:
    """Convert RMS amplitude to dBFS (0 dBFS = full scale)."""
    rms = max(rms, 1e-9)
    return 20.0 * np.log10(rms / REF_RMS)


def db_bar(db: float, width: int = DB_BAR_WIDTH) -> str:
    """Render a fixed-width ASCII bar for a dBFS value."""
    clipped = max(DB_MIN, min(DB_MAX, db))
    filled  = int((clipped - DB_MIN) / (DB_MAX - DB_MIN) * width)
    return "[" + "█" * filled + "░" * (width - filled) + "]"


# ─────────────────────────── Noise floor tracker ─────────────────────────────
class NoiseFloor:
    """
    Exponential moving average noise tracker.
    threshold_rms — hard midpoint set by two-phase calibration.
    Slowly blends toward the live adaptive value so it self-corrects
    if the environment changes after calibration.
    """
    def __init__(self, noise_rms: float, threshold_rms: float = None):
        self.rms   = max(noise_rms, MIN_NOISE_RMS)
        self._thr  = threshold_rms   # calibrated midpoint (may be None)

    def update(self, rms: float, is_speech: bool):
        alpha = NOISE_ALPHA_SLOW if is_speech else NOISE_ALPHA_FAST
        self.rms = alpha * rms + (1.0 - alpha) * self.rms
        self.rms = max(self.rms, MIN_NOISE_RMS)
        # Gently drift calibrated threshold toward the adaptive value
        if self._thr is not None:
            adaptive = self.rms * (10 ** (6.0 / 20.0))
            self._thr = 0.997 * self._thr + 0.003 * adaptive

    @property
    def threshold(self) -> float:
        if self._thr is not None:
            return max(self._thr, MIN_NOISE_RMS)
        return self.rms * (10 ** (6.0 / 20.0))   # 6 dB above noise floor


# ─────────────────────────── Frame classifier ────────────────────────────────
def classify(raw: bytes, vad: webrtcvad.Vad, noise: NoiseFloor,
             debug: bool = False):
    """
    Returns (is_speech, rms, db).
    Decision = WebRTC AND (energy_above_threshold OR zcr_in_speech_band)
    """
    rms = rms_of(raw)
    zcr = zcr_of(raw)
    db  = rms_to_db(rms)

    w = vad.is_speech(raw, SAMPLE_RATE)
    e = rms > noise.threshold
    z = ZCR_LOW <= zcr <= ZCR_HIGH

    decision = w and (e or z)
    noise.update(rms, decision)

    if debug:
        flags = ("W" if w else ".") + ("E" if e else ".") + ("Z" if z else ".")
        mark  = ">" if decision else " "
        print(f"  {mark}[{flags}] rms={rms:6.1f} thr={noise.threshold:6.1f} "
              f"db={db:5.1f} zcr={zcr:.3f}", end="\r")

    return decision, rms, db


# ─────────────────────────── Calibration ─────────────────────────────────────
def _record_phase(stream, label: str, prompt: str, duration_s: float) -> list:
    """Countdown then record `duration_s` seconds; return list of RMS values."""
    print(f"\n  {prompt}")
    input("  Press ENTER when ready... ")

    for n in (3, 2, 1):
        print(f"  {n}...", end=" ", flush=True)
        time.sleep(1)
    print(f"Recording {label}!\n")

    n_frames = int(duration_s * 1000 / FRAME_DURATION)
    rms_vals = []
    for i in range(n_frames):
        pct = int((i + 1) / n_frames * 30)
        bar = "#" * pct + "-" * (30 - pct)
        raw = stream.read(FRAME_SIZE, exception_on_overflow=False)
        rms  = rms_of(raw)
        db   = rms_to_db(rms)
        rms_vals.append(rms)
        print(f"  [{bar}] {db:+5.1f} dBFS", end="\r")

    print()
    return rms_vals


def calibrate(stream, duration_s: float = 3.0):
    """
    Two-phase calibration.
    Returns NoiseFloor instance seeded with measured values.
    """
    print("\n" + "=" * 58)
    print("  CALIBRATION  —  2 phases")
    print("=" * 58)

    # ── Phase 1: Quiet ───────────────────────────────────────────
    print("\n  PHASE 1 / 2  —  Background noise")
    print("  We need to hear how quiet your room is.")
    silence_rms = _record_phase(
        stream,
        label="silence",
        prompt="Stay completely QUIET (no talking, minimize movement).",
        duration_s=duration_s,
    )
    n_avg  = float(np.mean(silence_rms))
    n_std  = float(np.std(silence_rms))
    n_p95  = float(np.percentile(silence_rms, 95))
    n_db   = rms_to_db(n_avg)
    print(f"  Noise  avg={n_avg:.1f} RMS  ({n_db:+.1f} dBFS)  "
          f"std={n_std:.1f}  95th-pct={n_p95:.1f}")

    # ── Phase 2: Speaking ────────────────────────────────────────
    print("\n  PHASE 2 / 2  —  Your speaking voice")
    print("  Speak at your NORMAL volume (e.g. read something aloud).")
    speech_rms = _record_phase(
        stream,
        label="speech",
        prompt="Start talking when the countdown ends.",
        duration_s=duration_s,
    )
    s_avg  = float(np.mean(speech_rms))
    s_p90  = float(np.percentile(speech_rms, 90))
    s_db   = rms_to_db(s_avg)
    print(f"  Speech avg={s_avg:.1f} RMS  ({s_db:+.1f} dBFS)  "
          f"90th-pct={s_p90:.1f}")

    # ── Compute midpoint threshold ───────────────────────────────
    n_avg = max(n_avg, 1.0)
    snr   = 20.0 * np.log10(s_avg / n_avg) if s_avg > n_avg else 0.0

    if n_p95 > 0 and s_p90 > n_p95:
        thr_rms = float(np.sqrt(n_p95 * s_p90))   # geometric mean
    else:
        thr_rms = n_avg * (10 ** (6.0 / 20.0))    # fallback: +6 dB

    thr_db = rms_to_db(thr_rms)

    # ── Summary ──────────────────────────────────────────────────
    print("\n" + "-" * 58)
    print(f"  Noise floor      : {n_avg:7.1f} RMS  ({n_db:+6.1f} dBFS)")
    print(f"  Speech level     : {s_avg:7.1f} RMS  ({s_db:+6.1f} dBFS)")
    print(f"  SNR              : {snr:+.1f} dB")
    print(f"  Detection cutoff : {thr_rms:7.1f} RMS  ({thr_db:+6.1f} dBFS)")

    if snr < 3:
        print("\n  !! WARNING: SNR < 3 dB — mic may be muted or room is very loud.")
        print("     Detection will be unreliable. Try recalibrating.")
    elif snr < 6:
        print(f"\n  NOTE: SNR is marginal ({snr:.1f} dB). Soft speech may be missed.")
    else:
        print(f"\n  OK — SNR {snr:.1f} dB. Detection should be reliable.")

    print("=" * 58 + "\n")
    return NoiseFloor(noise_rms=n_avg, threshold_rms=thr_rms)


# ─────────────────────────── Save utterance ──────────────────────────────────
def save_utterance(frames: list, output_dir: str, idx: int) -> str:
    os.makedirs(output_dir, exist_ok=True)
    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(output_dir, f"speech_{ts}_{idx:04d}.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(b"".join(frames))
    dur = len(frames) * FRAME_DURATION / 1000
    print(f"\n  SAVED: {os.path.basename(path)}  ({dur:.2f}s)")

    with open(path, "rb") as f:
        wav_io = io.BytesIO(f.read())

    wav_io.seek(0)

    run_kmutt_assistant(wav_io, 0)
    
    return path


# ─────────────────────────── Main loop ───────────────────────────────────────
def run(vad_mode: int, output_dir: str, calibrate_first: bool, debug: bool):
    audio  = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=CHANNELS,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=FRAME_SIZE,
    )

    # ── Calibration / init ───────────────────────────────────────
    if calibrate_first:
        noise = calibrate(stream, duration_s=3.0)
    else:
        noise = NoiseFloor(noise_rms=200.0)
        print("Skipping calibration — noise floor adapts automatically.\n")

    vad = webrtcvad.Vad(vad_mode)
    print(f"Ready  |  WebRTC mode={vad_mode}  |  threshold={noise.threshold:.1f} RMS "
          f"({rms_to_db(noise.threshold):+.1f} dBFS)")
    print(f"Saving to : {os.path.abspath(output_dir)}")
    print("Listening... (Ctrl+C to stop)\n")
    print(f"  {'dB meter':8s}  {'bar':32s}  level / status")
    print("  " + "-" * 60)

    # ── Buffers ──────────────────────────────────────────────────
    pre_roll     = collections.deque(maxlen=N_PREROLL)
    speech_ring  = collections.deque(maxlen=N_SPEECH)
    silence_ring = collections.deque(maxlen=N_SILENCE)

    recording   = False
    current_utt = []
    utt_idx     = 0
    total_saved = 0

    # dB meter state
    db_window     = []         # RMS values accumulated since last print
    last_db_print = time.time()

    try:
        while True:
            raw = stream.read(FRAME_SIZE, exception_on_overflow=False)
            if len(raw) != FRAME_BYTES:
                continue

            is_sp, rms, db = classify(raw, vad, noise, debug)

            # ── Accumulate for dB meter ──────────────────────────
            db_window.append(rms)
            now = time.time()
            if now - last_db_print >= DB_PRINT_INTERVAL:
                avg_rms    = float(np.mean(db_window)) if db_window else 0.0
                avg_db     = rms_to_db(avg_rms)
                thr_db     = rms_to_db(noise.threshold)
                bar        = db_bar(avg_db)
                status     = "SPEECH  " if recording else "silence "
                indicator  = "<<<" if recording else "   "
                print(f"  {avg_db:+6.1f} dBFS  {bar}  thr={thr_db:+.1f}  "
                      f"{status} {indicator}", end="\r")
                db_window.clear()
                last_db_print = now

            # ── VAD state machine ────────────────────────────────
            if not recording:
                pre_roll.append(raw)
                speech_ring.append(is_sp)

                if len(speech_ring) == N_SPEECH:
                    if sum(speech_ring) / N_SPEECH >= 0.6:
                        recording   = True
                        utt_idx    += 1
                        current_utt = list(pre_roll)
                        silence_ring.clear()
                        print(f"\n  [{utt_idx}] Recording...", end="", flush=True)

            else:
                current_utt.append(raw)
                silence_ring.append(not is_sp)

                if len(silence_ring) == N_SILENCE:
                    if sum(silence_ring) / N_SILENCE >= 0.85:
                        dur = len(current_utt) * FRAME_DURATION / 1000
                        print(f"  {dur:.1f}s  [END]")
                        save_utterance(current_utt, output_dir, utt_idx)
                        total_saved += 1
                        recording    = False
                        current_utt  = []
                        speech_ring.clear()
                        silence_ring.clear()

    except KeyboardInterrupt:
        print("\n\nStopped.")
        if recording and current_utt:
            save_utterance(current_utt, output_dir, utt_idx)
            total_saved += 1
        print(f"Total saved : {total_saved} file(s)")
        print(f"Output dir  : {os.path.abspath(output_dir)}")

    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()


# ─────────────────────────── CLI ─────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(
        description="Two-phase VAD recorder with live dB meter.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
WebRTC aggressiveness (--mode):
  0 = permissive   1 = low   2 = medium [default]   3 = strict
        """
    )
    p.add_argument("--mode", type=int, choices=[0, 1, 2, 3], default=2)
    p.add_argument("--output-dir", default="./recordings")
    p.add_argument("--no-calibration", action="store_true",
                   help="Skip two-phase calibration")
    p.add_argument("--debug", action="store_true",
                   help="Print per-frame W/E/Z flags")
    return p.parse_args()


if __name__ == "__main__":
    init_all() 
    
    args = parse_args()
    run(
        vad_mode=args.mode,
        output_dir=args.output_dir,
        calibrate_first=not args.no_calibration,
        debug=args.debug,
    )
