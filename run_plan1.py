#!/usr/bin/env python3
"""
Chạy trực tiếp Publisher và Subscriber - KHÔNG có input
"""

import subprocess
import sys
import time

publisher_file = 'plan1_mqtt_vm/plan1_publisher.py'

print("="*70)
print("KHOI DONG HE THONG")
print("="*70)
print()

# Start publisher
print("[1] Khoi dong Publisher...")
publisher = subprocess.Popen(
    [sys.executable, publisher_file, 'publisher'],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)
time.sleep(3)
print("[OK] Publisher da chay")
print()

# Start subscriber - hiển thị output
print("[2] Khoi dong Subscriber...")
print("="*70)
print()

subscriber = subprocess.Popen(
    [sys.executable, publisher_file, 'subscriber'],
    stdout=sys.stdout,
    stderr=sys.stderr
)

try:
    # Giữ chạy cho đến khi Ctrl+C
    print("\n[INFO] He thong dang chay... Nhan Ctrl+C de dung")
    subscriber.wait()
except KeyboardInterrupt:
    print("\n[STOP] Dang dung...")
finally:
    publisher.terminate()
    subscriber.terminate()
    publisher.wait()
    subscriber.wait()
    print("[OK] Da dung thanh cong")
