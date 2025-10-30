#!/usr/bin/env python3
"""
DEMO CHUYEN NGHIEP - Phuong an 1
Python Client -> MQTT Broker -> VictoriaMetrics
"""

import subprocess
import sys
import time
import requests
import json

def check_services():
    """Kiểm tra services"""
    print("="*70)
    print("KIEM TRA HE THONG")
    print("="*70)
    
    all_ok = True
    
    # Check MQTT
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 1883))
        sock.close()
        if result == 0:
            print("[OK] MQTT Broker (port 1883) - Dang chay")
        else:
            print("[ERROR] MQTT Broker chua chay!")
            print("  Chay: podman start emqx_broker")
            all_ok = False
    except:
        print("[ERROR] Khong the kiem tra MQTT Broker")
        all_ok = False
    
    # Check VictoriaMetrics
    try:
        response = requests.get('http://localhost:8428/', timeout=2)
        if response.status_code == 200:
            print("[OK] VictoriaMetrics (port 8428) - Dang chay")
            print("  Web UI: http://localhost:8428/vmui")
        else:
            print("[WARNING] VictoriaMetrics tra ve: " + str(response.status_code))
    except:
        print("[ERROR] VictoriaMetrics chua chay!")
        print("  Chay: podman start victoriametrics")
        all_ok = False
    
    print()
    return all_ok

def run_demo():
    """Chạy demo đầy đủ"""
    print("="*70)
    print("DEMO HE THONG: PYTHON -> MQTT -> VICTORIAMETRICS")
    print("="*70)
    print()
    print("Quy trinh:")
    print("  1. Python Publisher gui du lieu sensor qua MQTT broker")
    print("  2. Python Subscriber nhan du lieu tu MQTT")
    print("  3. Subscriber chuyen doi sang Prometheus format")
    print("  4. Subscriber gui HTTP POST vao VictoriaMetrics")
    print("  5. VictoriaMetrics luu tru du lieu time-series")
    print()
    print("Thoi gian demo: 30 giay")
    print("Tu dong bat dau sau 2 giay...")
    print()
    time.sleep(2)
    
    publisher_file = 'plan1_mqtt_vm/plan1_publisher.py'
    
    print("\n" + "="*70)
    print("[BAT DAU] Khoi dong Publisher...")
    print("="*70)
    
    # Start publisher trong background
    publisher = subprocess.Popen(
        [sys.executable, publisher_file, 'publisher'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    time.sleep(3)
    print("[OK] Publisher da khoi dong va dang gui du lieu...\n")
    
    print("="*70)
    print("[BAT DAU] Khoi dong Subscriber...")
    print("="*70)
    print("Subscriber se:")
    print("  - Nhan du lieu tu MQTT")
    print("  - Chuyen doi sang Prometheus format")
    print("  - Gui vao VictoriaMetrics")
    print()
    print("-"*70)
    
    # Start subscriber - hiển thị output real-time
    subscriber = subprocess.Popen(
        [sys.executable, publisher_file, 'subscriber'],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    
    try:
        print("\n[INFO] Demo dang chay trong 30 giay...")
        print("[INFO] Quan sat output ben tren de thay du lieu duoc gui...")
        time.sleep(30)
    except KeyboardInterrupt:
        print("\n[STOP] Demo bi dung boi user")
    finally:
        print("\n" + "-"*70)
        print("[STOP] Dang dung Publisher va Subscriber...")
        publisher.terminate()
        subscriber.terminate()
        publisher.wait()
        subscriber.wait()
        
        print("\n" + "="*70)
        print("DEMO HOAN THANH")
        print("="*70)
        print("\n[KIEM TRA] Kiem tra du lieu trong VictoriaMetrics:")
        print("  1. Web UI: http://localhost:8428/vmui")
        print("  2. Hoac chay: python plan1_mqtt_vm/query_vm.py")

def main():
    print("\n" + "="*70)
    print("CHUONG TRINH DEMO CHO SEP")
    print("Python Client -> MQTT Broker -> VictoriaMetrics")
    print("="*70)
    print()
    
    # Kiểm tra services
    if not check_services():
        print("\n[ERROR] Co services chua san sang!")
        print("\nDe khoi dong services:")
        print("  python podman_setup.py")
        print("\nHoac kiem tra:")
        print("  podman ps | findstr emqx victoriametrics")
        print("\n[INFO] Kiem tra chi tiet VictoriaMetrics:")
        print("  python check_vm.py")
        return
    
    print("[OK] Tat ca services san sang!\n")
    
    # Chạy demo
    try:
        run_demo()
    except Exception as e:
        print(f"\n[ERROR] Loi trong qua trinh demo: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
