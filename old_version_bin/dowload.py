import os
from transformers import (
    AutoTokenizer, 
    AutoModelForQuestionAnswering, 
    VitsModel, 
    pipeline
)

def download_models():
    print("--- Starting Model Downloads ---")

    # 1. DOWNLOAD THE EARS (Whisper Base)
    print("\n[1/3] Downloading Whisper (Ears)...")
    # We use the pipeline to trigger the download of both model and processor
    pipeline("automatic-speech-recognition", model="openai/whisper-base")
    print("Done: Whisper base is ready.")

    # 2. DOWNLOAD THE BRAIN (WangchanBERTa QA)
    print("\n[2/3] Downloading WangchanBERTa (Brain)...")
    model_qa = "airesearch/wangchanberta-base-wiki-20210520-spm-finetune-qa"
    AutoTokenizer.from_pretrained(model_qa)
    AutoModelForQuestionAnswering.from_pretrained(model_qa)
    print("Done: WangchanBERTa is ready.")

    # 3. DOWNLOAD THE MOUTH (MMS-TTS Thai)
    print("\n[3/3] Downloading MMS-TTS (Mouth)...")
    model_tts = "facebook/mms-tts-tha"
    AutoTokenizer.from_pretrained(model_tts)
    VitsModel.from_pretrained(model_tts)
    print("Done: MMS-TTS Thai is ready.")

    print("\n" + "="*30)
    print("SUCCESS: All KMUTT AI models are downloaded!")
    print("You can now run your main scripts offline.")
    print("="*30)

if __name__ == "__main__":
    download_models()