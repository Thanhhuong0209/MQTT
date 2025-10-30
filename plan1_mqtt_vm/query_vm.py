#!/usr/bin/env python3
"""
Query dữ liệu từ VictoriaMetrics
Kiểm tra xem dữ liệu đã được lưu thành công chưa
"""

import requests
import json
import sys
from datetime import datetime, timedelta

# Tự động chọn endpoint: ưu tiên vmselect (cluster), fallback về single node
VM_SINGLE_URL = "http://localhost:8428"
VM_SELECT_URL = "http://localhost:8481"

def _pick_vm_endpoint():
    try:
        r = requests.get(VM_SELECT_URL, timeout=1.5)
        if r.status_code in (200, 401, 403):
            return VM_SELECT_URL
    except Exception:
        pass
    return VM_SINGLE_URL

VICTORIA_METRICS_URL = _pick_vm_endpoint()

def _api_base():
    # Nếu là vmselect (cluster) thì dùng đường dẫn Prometheus của cluster
    if VICTORIA_METRICS_URL.endswith(":8481"):
        return f"{VICTORIA_METRICS_URL}/select/0/prometheus/api/v1"
    # Single node API
    return f"{VICTORIA_METRICS_URL}/api/v1"

def query_metrics(metric_name):
    """Query một metric từ VictoriaMetrics"""
    try:
        url = f"{_api_base()}/query"
        params = {
            'query': metric_name,
            'time': datetime.now().timestamp()
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('result', [])
        else:
            print(f"[ERROR] Query loi: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] Khong the query: {e}")
        return []

def query_range(metric_name, minutes=5):
    """Query range của một metric"""
    try:
        url = f"{_api_base()}/query_range"
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=minutes)
        
        params = {
            'query': metric_name,
            'start': start_time.timestamp(),
            'end': end_time.timestamp(),
            'step': '15s'
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', {}).get('result', [])
        else:
            print(f"[ERROR] Query range loi: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERROR] Khong the query range: {e}")
        return []

def list_metrics():
    """Liệt kê tất cả metrics có trong VictoriaMetrics"""
    try:
        url = f"{_api_base()}/label/__name__/values"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('data', [])
        else:
            return []
    except:
        return []

def main():
    print("="*70)
    print("KIEM TRA DU LIEU TRONG VICTORIAMETRICS")
    print("="*70)
    print()
    
    # Kiểm tra connection
    try:
        response = requests.get(VICTORIA_METRICS_URL, timeout=2)
        if response.status_code != 200:
            print("[ERROR] VictoriaMetrics khong ket noi duoc!")
            return
    except:
        print("[ERROR] VictoriaMetrics chua chay!")
        print("Chay: podman start victoriametrics")
        return
    
    print("[OK] Da ket noi VictoriaMetrics\n")
    
    # List tất cả metrics
    print("[1] Danh sach metrics:")
    print("-"*70)
    all_metrics = list_metrics()
    sensor_metrics = [m for m in all_metrics if 'sensor' in m]
    
    if sensor_metrics:
        print(f"Tim thay {len(sensor_metrics)} sensor metrics:")
        for metric in sensor_metrics:
            print(f"  - {metric}")
    else:
        print("Chua co sensor metrics nao")
        print("(Co the chua co du lieu hoac metric khac ten)")
    
    print()
    
    # Query từng metric
    metrics_to_check = [
        'sensor_temperature',
        'sensor_humidity',
        'sensor_pressure',
        'sensor_battery_level'
    ]
    
    print("[2] Query gia tri moi nhat:")
    print("-"*70)
    
    for metric_name in metrics_to_check:
        results = query_metrics(metric_name)
        
        if results:
            print(f"\n{metric_name}:")
            for result in results[:3]:  # Chỉ hiển thị 3 kết quả đầu
                metric = result.get('metric', {})
                value = result.get('value', [])
                if value:
                    timestamp = datetime.fromtimestamp(float(value[0]))
                    val = value[1]
                    sensor_id = metric.get('sensor_id', 'N/A')
                    location = metric.get('location', 'N/A')
                    print(f"  Sensor: {sensor_id}, Location: {location}")
                    print(f"  Gia tri: {val}, Time: {timestamp}")
        else:
            print(f"{metric_name}: Chua co du lieu")
    
    print()
    print("[3] Query range (last 5 minutes):")
    print("-"*70)
    
    for metric_name in metrics_to_check[:2]:  # Chỉ query 2 metrics đầu
        results = query_range(metric_name, minutes=5)
        
        if results:
            print(f"\n{metric_name}:")
            for result in results[:1]:  # Chỉ hiển thị 1 kết quả đầu
                metric = result.get('metric', {})
                values = result.get('values', [])
                if values:
                    print(f"  Sensor: {metric.get('sensor_id', 'N/A')}")
                    print(f"  So luong diem du lieu: {len(values)}")
                    if values:
                        latest = values[-1]
                        timestamp = datetime.fromtimestamp(float(latest[0]))
                        print(f"  Diem moi nhat: {latest[1]} at {timestamp}")
        else:
            print(f"{metric_name}: Chua co du lieu trong 5 phut qua")
    
    print()
    print("="*70)
    print("HUONG DAN")
    print("="*70)
    print("Xem du lieu truc quan:")
    print("  Web UI: http://localhost:8428/vmui")
    print()
    print("Query truc tiep:")
    print('  curl "http://localhost:8428/api/v1/query?query=sensor_temperature"')
    print()

if __name__ == "__main__":
    main()
