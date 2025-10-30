#!/usr/bin/env python3
"""
Chạy Plan 1 - KHÔNG có bất kỳ input nào
"""

import subprocess
import sys
import time

print("="*70)
print("KHOI DONG PUBLISHER VA SUBSCRIBER")
print("="*70)
print()

# Chạy publisher trong background
print("[1] Bat dau Publisher...")
publisher_process = subprocess.Popen(
    [sys.executable, "plan1_mqtt_vm/plan1_publisher.py", "publisher"],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL
)

time.sleep(3)

print("[2] Bat dau Subscriber...")
print("="*70)
print()

# Chạy subscriber và hiển thị output
try:
    subscriber_process = subprocess.Popen(
        [sys.executable, "plan1_mqtt_vm/plan1_publisher.py", "subscriber"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    subscriber_process.wait()
except KeyboardInterrupt:
    print("\n[STOP] Dang dung...")
finally:
    publisher_process.terminate()
    subscriber_process.terminate()
