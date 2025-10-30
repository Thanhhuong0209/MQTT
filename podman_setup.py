#!/usr/bin/env python3
"""
Script khởi động tất cả services với Podman
Sử dụng podman run trực tiếp thay vì docker-compose
"""

import subprocess
import time
import sys

def run_podman_command():
    """Kiểm tra và chạy podman commands"""
    print("[PODMAN] Bat dau khoi dong services voi Podman...")
    
    # Kiểm tra podman có sẵn không
    try:
        result = subprocess.run(['podman', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("[ERROR] Podman chua duoc cai dat!")
            print("Cai dat: https://podman-desktop.io/")
            return False
        print(f"[OK] {result.stdout.strip()}")
    except FileNotFoundError:
        print("[ERROR] Podman khong tim thay!")
        print("Cai dat: https://podman-desktop.io/")
        return False
    
    services = [
        {
            'name': 'emqx_broker',
            'image': 'emqx/emqx:5.3.0',
            'ports': ['1883:1883', '18083:18083'],
            'env': {
                'EMQX_DASHBOARD__DEFAULT_USERNAME': 'admin',
                'EMQX_DASHBOARD__DEFAULT_PASSWORD': 'public'
            }
        },
        {
            'name': 'victoriametrics',
            'image': 'victoriametrics/victoria-metrics:latest',
            'ports': ['8428:8428'],
            'command': [
                '-storageDataPath=/victoria-metrics-data',
                '-httpListenAddr=:8428'
            ],
            'volumes': ['victoriametrics_data:/victoria-metrics-data']
        },
        {
            'name': 'nats_server',
            'image': 'nats:latest',
            'ports': ['4222:4222', '8222:8222'],
            'command': ['-js', '-m', '8222']
        },
        {
            'name': 'rabbitmq_server',
            'image': 'rabbitmq:3-management',
            'ports': ['5672:5672', '15672:15672'],
            'env': {
                'RABBITMQ_DEFAULT_USER': 'admin',
                'RABBITMQ_DEFAULT_PASS': 'admin'
            }
        }
    ]
    
    print("\n[PODMAN] Khoi dong cac services...")
    
    for service in services:
        try:
            # Build command
            cmd = ['podman', 'run', '-d']
            
            # Add name
            cmd.extend(['--name', service['name']])
            
            # Add ports
            for port in service.get('ports', []):
                cmd.extend(['-p', port])
            
            # Add environment variables
            for key, value in service.get('env', {}).items():
                cmd.extend(['-e', f'{key}={value}'])
            
            # Add volumes
            for volume in service.get('volumes', []):
                cmd.extend(['-v', volume])
            
            # Add image
            cmd.append(service['image'])
            
            # Add command if exists
            if 'command' in service:
                cmd.extend(service['command'])
            
            print(f"[PODMAN] Khoi dong {service['name']}...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[OK] {service['name']} da khoi dong")
            else:
                print(f"[ERROR] {service['name']} loi: {result.stderr}")
                
        except Exception as e:
            print(f"[ERROR] Loi khi khoi dong {service['name']}: {e}")
    
    # Riêng với Pulsar, cần command đặc biệt
    print("\n[PODMAN] Luu y: Apache Pulsar can khoi dong rieng voi command dac biet:")
    print("podman run -d --name pulsar_broker -p 6650:6650 -p 8080:8080 \\")
    print("  apachepulsar/pulsar:latest bash -c \"bin/pulsar standalone --no-functions-worker --no-stream-storage\"")
    
    print("\n[OK] Da khoi dong cac services")
    print("\n[INFO] Kiem tra: podman ps")
    print("[INFO] Xem logs: podman logs <container_name>")
    print("[INFO] Dung services: podman stop <container_name>")
    print("[INFO] Dung tat ca: podman stop $(podman ps -q)")
    
    return True

def stop_all_services():
    """Dừng tất cả services"""
    print("\n[PODMAN] Dang dung tat ca services...")
    try:
        result = subprocess.run(['podman', 'ps', '-q'], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            containers = result.stdout.strip().split('\n')
            for container in containers:
                if container:
                    subprocess.run(['podman', 'stop', container])
            print("[OK] Da dung tat ca services")
        else:
            print("[INFO] Khong co service nao dang chay")
    except Exception as e:
        print(f"[ERROR] Loi khi dung services: {e}")

def main():
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stop":
        stop_all_services()
    elif len(sys.argv) > 1 and sys.argv[1] == "status":
        print("[PODMAN] Trang thai services:")
        subprocess.run(['podman', 'ps'])
    else:
        print("=" * 70)
        print("KHOI DONG SERVICES VOI PODMAN")
        print("=" * 70)
        print("\nLua chon:")
        print("  python podman_setup.py          - Khoi dong services")
        print("  python podman_setup.py stop     - Dung tat ca services")
        print("  python podman_setup.py status   - Xem trang thai")
        
        if len(sys.argv) == 1:
            confirm = input("\nCo muon khoi dong ngay? (y/n): ").lower()
            if confirm == 'y':
                run_podman_command()
            else:
                print("[CANCEL] Da huy")

if __name__ == "__main__":
    main()
