#!/usr/bin/env python3
"""
Script khởi động VictoriaMetrics Cluster với Podman
"""

import subprocess
import sys
import time

def run_command(cmd, check=True):
    """Chạy command và hiển thị output"""
    print(f"[RUN] {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0 and check:
        print(f"[ERROR] {result.stderr}")
        return False
    return True

def check_container(name):
    """Kiểm tra container có đang chạy không"""
    result = subprocess.run(
        f'podman ps --format "{{{{.Names}}}}" | findstr /i "{name}"',
        shell=True,
        capture_output=True,
        text=True
    )
    return name in result.stdout

def start_vm_cluster():
    """Khởi động VictoriaMetrics Cluster"""
    print("="*70)
    print("KHOI DONG VICTORIAMETRICS CLUSTER")
    print("="*70)
    print()
    
    components = [
        ("vmstorage-0", 8482, "8401:8401"),
        ("vmstorage-1", 8483, "8401:8401"),
        ("vminsert", 8480, None),
        ("vmselect", 8481, None)
    ]
    
    # Kiểm tra và dừng containers cũ nếu có
    print("[1] Kiem tra containers cu...")
    for name, port, _ in components:
        if check_container(name):
            print(f"[STOP] Dang dung {name}...")
            run_command(f'podman stop {name}', check=False)
            run_command(f'podman rm {name}', check=False)
    
    print()
    
    # Tạo network dùng chung cho các container (nếu chưa có)
    print("[1.5] Tao network noi bo 'vm_net' (neu chua co)...")
    run_command('podman network inspect vm_net >NUL 2>&1 || podman network create vm_net', check=False)

    # Start VMStorage Node 0
    print("[2] Khoi dong vmstorage-0...")
    cmd = (
        'podman run -d --name vmstorage-0 --network vm_net '
        '-p 8482:8482 '
        '-v vm_storage1_data:/vmstorage-data '
        'victoriametrics/vmstorage:latest '
        '-storageDataPath=/vmstorage-data '
        '-retentionPeriod=12 '
        '-httpListenAddr=:8482'
    )
    run_command(cmd)
    time.sleep(2)
    
    # Start VMStorage Node 1
    print("[3] Khoi dong vmstorage-1...")
    cmd = (
        'podman run -d --name vmstorage-1 --network vm_net '
        '-p 8483:8482 '
        '-v vm_storage2_data:/vmstorage-data '
        'victoriametrics/vmstorage:latest '
        '-storageDataPath=/vmstorage-data '
        '-retentionPeriod=12 '
        '-httpListenAddr=:8482'
    )
    run_command(cmd)
    time.sleep(3)
    
    # Start VMInsert
    print("[4] Khoi dong vminsert...")
    cmd = (
        'podman run -d --name vminsert --network vm_net '
        '-p 8480:8480 '
        'victoriametrics/vminsert:latest '
        '-storageNode=vmstorage-0:8400 '
        '-storageNode=vmstorage-1:8400 '
        '-httpListenAddr=:8480'
    )
    run_command(cmd)
    time.sleep(2)
    
    # Start VMSelect
    print("[5] Khoi dong vmselect...")
    cmd = (
        'podman run -d --name vmselect --network vm_net '
        '-p 8481:8481 '
        'victoriametrics/vmselect:latest '
        '-storageNode=vmstorage-0:8401 '
        '-storageNode=vmstorage-1:8401 '
        '-httpListenAddr=:8481'
    )
    run_command(cmd)
    time.sleep(2)
    
    print()
    print("="*70)
    print("KHOI DONG HOAN TAT")
    print("="*70)
    print()
    print("Cac thanh phan:")
    print("  vmstorage-0: http://localhost:8482")
    print("  vmstorage-1: http://localhost:8483")
    print("  vminsert:    http://localhost:8480 (de gui du lieu)")
    print("  vmselect:    http://localhost:8481 (de query)")
    print()
    print("Kiem tra trang thai:")
    print("  podman ps | findstr vm")
    print()

def stop_vm_cluster():
    """Dừng VictoriaMetrics Cluster"""
    print("="*70)
    print("DUNG VICTORIAMETRICS CLUSTER")
    print("="*70)
    
    components = ["vmselect", "vminsert", "vmstorage-1", "vmstorage-0"]
    
    for component in components:
        if check_container(component):
            print(f"[STOP] Dang dung {component}...")
            run_command(f'podman stop {component}', check=False)
            run_command(f'podman rm {component}', check=False)
    
    print("[OK] Da dung tat ca components")

def status_vm_cluster():
    """Kiểm tra trạng thái cluster"""
    print("="*70)
    print("TRANG THAI VICTORIAMETRICS CLUSTER")
    print("="*70)
    print()
    
    components = [
        "vmstorage-0",
        "vmstorage-1",
        "vminsert",
        "vmselect"
    ]
    
    for comp in components:
        if check_container(comp):
            print(f"[OK] {comp} - Dang chay")
        else:
            print(f"[STOP] {comp} - Chua chay")
    
    print()
    print("Xem chi tiet: podman ps | findstr vm")

def main():
    if len(sys.argv) > 1:
        action = sys.argv[1]
        if action == "start":
            start_vm_cluster()
        elif action == "stop":
            stop_vm_cluster()
        elif action == "status":
            status_vm_cluster()
        else:
            print("Su dung: python vm_cluster_setup.py [start|stop|status]")
    else:
        print("Su dung: python vm_cluster_setup.py [start|stop|status]")
        print()
        print("start  - Khoi dong cluster")
        print("stop   - Dung cluster")
        print("status - Kiem tra trang thai")

if __name__ == "__main__":
    main()
