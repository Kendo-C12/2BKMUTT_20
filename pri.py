import time
import sys

spinner = "|/-\\"
for i in range(20):
    print(f"\rLoading... {spinner[i % len(spinner)]}", flush=True, end="")
    # sys.stdout.flush()
    time.sleep(0.2)

print("\nDone!")