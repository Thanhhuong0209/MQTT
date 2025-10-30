#!/usr/bin/env python3
"""
Chạy Plan 1 - HOÀN TOÀN TỰ ĐỘNG, KHÔNG INPUT
"""

import subprocess
import sys
import time
import os

# Tắt buffering để output hiển thị ngay
os.environ['PYTHONUNBUFFERED'] = '1'

publisher_file = "plan1_mqtt_vm/plan1_publisher.py"

# Start publisher
publisher = subprocess.Popen(
    [sys.executable, publisher_file, "publisher"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(2)

# Start subscriber - output trực tiếp
subscriber = subprocess.Popen(
    [sys.executable, publisher_file, "subscriber"],
    stdout=sys.stdout,
    stderr=sys.stderr,
    bufsize=0
)

# Giữ chạy
try:
    subscriber.wait()
except KeyboardInterrupt:
    pass
finally:
    publisher.terminate()
    subscriber.terminate()
