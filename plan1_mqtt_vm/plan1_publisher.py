#!/usr/bin/env python3
"""
Phương án 1: MQTT Broker + Python + VictoriaMetrics
Publisher gửi dữ liệu sensor qua MQTT, Subscriber nhận và lưu vào VictoriaMetrics
"""

import paho.mqtt.client as mqtt
import argparse
import json
import time
import random
import threading
import requests
import queue
from datetime import datetime

# Configuration
MQTT_BROKER_HOST = "localhost"
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = "sensor/data"

# VictoriaMetrics Configuration
# Mode: "single" hoặc "cluster"
VM_MODE = "cluster"  # Dùng cluster (vminsert:8480, vmselect:8481)

# Single Node Configuration
VM_SINGLE_URL = "http://localhost:8428"

# Cluster Configuration
VM_INSERT_URL = "http://localhost:8480"  # VMInsert để gửi dữ liệu
VM_SELECT_URL = "http://localhost:8481"  # VMSelect để query

# Auto-detect mode dựa trên URL nào available
VICTORIA_METRICS_URL = None  # Sẽ được set tự động

class SensorPublisher:
    def __init__(self):
        # Sử dụng Callback API version 2
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.running = False
        self.message_count = 0
        
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[PLAN1] Da ket noi MQTT broker tai {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
        else:
            print(f"[PLAN1] Loi ket noi MQTT broker: {reason_code}")
    
    def on_publish(self, client, userdata, mid, reason_code, properties):
        self.message_count += 1
        if self.message_count % 10 == 0:
            print(f"[PLAN1] Da gui {self.message_count} messages")
    
    def generate_sensor_data(self):
        return {
            "timestamp": datetime.now().isoformat(),
            "sensor_id": f"sensor_{random.randint(1, 10):03d}",
            "temperature": round(random.uniform(20.0, 35.0), 2),
            "humidity": round(random.uniform(40.0, 80.0), 2),
            "pressure": round(random.uniform(980.0, 1020.0), 2),
            "location": f"room_{random.randint(1, 5):02d}",
            "battery_level": round(random.uniform(80.0, 100.0), 2)
        }
    
    def publish_sensor_data(self):
        sensor_data = self.generate_sensor_data()
        message = json.dumps(sensor_data)
        
        try:
            result = self.client.publish(MQTT_TOPIC, message, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[PLAN1] Gui: {sensor_data['temperature']}C, "
                      f"Do am: {sensor_data['humidity']}%, "
                      f"Ap suat: {sensor_data['pressure']}hPa")
            else:
                print(f"[PLAN1] Loi gui message: {result.rc}")
        except Exception as e:
            print(f"[PLAN1] Loi publish: {e}")
    
    def start_publishing(self):
        self.running = True
        print("[PLAN1] Bat dau gui du lieu sensor...")
        
        while self.running:
            self.publish_sensor_data()
            time.sleep(1)  # Gửi mỗi 1 giây
    
    def stop_publishing(self):
        self.running = False
        print("[PLAN1] Da dung gui du lieu")
    
    def connect_and_start(self):
        try:
            print(f"[PLAN1] Dang ket noi MQTT broker...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            time.sleep(2)
            
            publish_thread = threading.Thread(target=self.start_publishing)
            publish_thread.daemon = True
            publish_thread.start()
            return publish_thread
            
        except Exception as e:
            print(f"[PLAN1] Loi ket noi: {e}")
            return None

class VictoriaMetricsClient:
    def __init__(self):
        # Detect mode và set URL
        self.mode = VM_MODE
        self._setup_urls()
        
        self.current_url_index = 0
        self.success_count = 0
        self.error_count = 0
        self.session = requests.Session()
    
    def _setup_urls(self):
        """Setup URLs dựa trên mode"""
        if self.mode == "cluster":
            # Cluster mode - dùng vminsert để gửi dữ liệu
            self.base_url = VM_INSERT_URL
            self.select_url = VM_SELECT_URL
            self.urls = [
                # Prometheus text exposition (đúng cho cluster)
                f"{self.base_url}/insert/0/prometheus/api/v1/import/prometheus",
                # Remote write (Prometheus remote_write)
                f"{self.base_url}/insert/0/api/v1/write",
            ]
            print(f"[PLAN1] Su dung VictoriaMetrics CLUSTER mode")
            print(f"[PLAN1] VMInsert (gui du lieu): {self.base_url}")
            print(f"[PLAN1] VMSelect (query): {self.select_url}")
        else:
            # Single node mode
            self.base_url = VM_SINGLE_URL
            self.select_url = VM_SINGLE_URL
            self.urls = [
                f"{self.base_url}/api/v1/import",  # Endpoint chuẩn
                f"{self.base_url}/write",  # InfluxDB line protocol
                f"{self.base_url}/api/v1/import/prometheus"  # Prometheus format
            ]
            print(f"[PLAN1] Su dung VictoriaMetrics SINGLE NODE mode")
            print(f"[PLAN1] URL: {self.base_url}")
        
    def test_connection(self):
        """Test kết nối VictoriaMetrics"""
        try:
            # Test bằng root endpoint - đơn giản và luôn hoạt động
            response = requests.get(self.base_url, timeout=2)
            if response.status_code == 200:
                print(f"[PLAN1] VictoriaMetrics da san sang tai {self.base_url}")
                return True
            else:
                # 200 hoặc các status code khác đều OK, chỉ cần không lỗi connection
                print(f"[PLAN1] VictoriaMetrics tra ve status: {response.status_code} (co the OK)")
                return True  # Vẫn return True vì VM đang chạy
        except requests.exceptions.ConnectionError:
            print(f"[PLAN1] VictoriaMetrics chua chay hoac khong ket noi duoc")
            return False
        except Exception as e:
            print(f"[PLAN1] Loi khi kiem tra VictoriaMetrics: {e}")
            return False
        
    def send_metrics(self, sensor_data):
        """Gửi metrics đến VictoriaMetrics với retry mechanism"""
        metrics = self._convert_to_prometheus_format(sensor_data)
        
        # Thử endpoint hiện tại trước
        for attempt in range(len(self.urls)):
            try:
                url = self.urls[(self.current_url_index + attempt) % len(self.urls)]
                response = self.session.post(
                    url,
                    data=metrics,
                    headers={'Content-Type': 'text/plain'},
                    timeout=3
                )
                
                # HTTP 200, 204 đều là thành công
                if response.status_code in [200, 204]:
                    self.success_count += 1
                    if attempt > 0:
                        # Cập nhật URL tốt nhất
                        self.current_url_index = (self.current_url_index + attempt) % len(self.urls)
                        print(f"[PLAN1] Da tim thay endpoint tot: {url}")
                    return True
                else:
                    # Thử endpoint tiếp theo
                    continue
                    
            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                continue
        
        # Tất cả endpoint đều lỗi
        self.error_count += 1
        print(f"[PLAN1] VictoriaMetrics error - da thu tat ca endpoints")
        return False
    
    def _convert_to_prometheus_format(self, sensor_data):
        """Chuyển đổi dữ liệu sensor sang Prometheus format"""
        # Prometheus text exposition expects timestamp in seconds
        timestamp = int(datetime.fromisoformat(sensor_data['timestamp']).timestamp())
        
        metrics = []
        # Temperature metric
        metrics.append(
            f"sensor_temperature{{sensor_id=\"{sensor_data['sensor_id']}\","
            f"location=\"{sensor_data['location']}\"}} "
            f"{sensor_data['temperature']} {timestamp}"
        )
        # Humidity metric
        metrics.append(
            f"sensor_humidity{{sensor_id=\"{sensor_data['sensor_id']}\","
            f"location=\"{sensor_data['location']}\"}} "
            f"{sensor_data['humidity']} {timestamp}"
        )
        # Pressure metric
        metrics.append(
            f"sensor_pressure{{sensor_id=\"{sensor_data['sensor_id']}\","
            f"location=\"{sensor_data['location']}\"}} "
            f"{sensor_data['pressure']} {timestamp}"
        )
        # Battery level metric
        metrics.append(
            f"sensor_battery_level{{sensor_id=\"{sensor_data['sensor_id']}\","
            f"location=\"{sensor_data['location']}\"}} "
            f"{sensor_data['battery_level']} {timestamp}"
        )
        
        return '\n'.join(metrics)
    
    def get_stats(self):
        """Lấy thống kê gửi metrics"""
        total = self.success_count + self.error_count
        success_rate = (self.success_count / total * 100) if total > 0 else 0
        return {
            'success': self.success_count,
            'errors': self.error_count,
            'total': total,
            'success_rate': success_rate
        }

class SensorSubscriber:
    def __init__(self):
        # Sử dụng Callback API version 2
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.vm_client = VictoriaMetricsClient()
        self.message_count = 0
        self.start_time = None
        # Tăng throughput: xử lý VM ghi ở worker thread thay vì chặn on_message
        self.queue = queue.Queue(maxsize=1000)
        self.worker_threads = []
        self.worker_count = 3  # tăng mặc định để đạt >=1 msg/s ổn định
        
    def on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            print(f"[PLAN1] Subscriber da ket noi MQTT broker")
            client.subscribe(MQTT_TOPIC, qos=1)
            print(f"[PLAN1] Da subscribe topic: {MQTT_TOPIC}")
            self.start_time = time.time()
            
            # Test VictoriaMetrics connection
            if self.vm_client.test_connection():
                print(f"[PLAN1] San sang nhan va luu du lieu vao VictoriaMetrics")
            else:
                print(f"[PLAN1] Canh bao: VictoriaMetrics co the chua san sang")
            # Khởi động worker tiêu thụ hàng đợi
            for _ in range(self.worker_count):
                t = threading.Thread(target=self._worker_consume)
                t.daemon = True
                t.start()
                self.worker_threads.append(t)
        else:
            print(f"[PLAN1] Loi ket noi subscriber: {reason_code}")
    
    def on_message(self, client, userdata, msg):
        try:
            sensor_data = json.loads(msg.payload.decode('utf-8'))
            self.message_count += 1
            # Đưa vào hàng đợi để worker xử lý ghi VM
            try:
                self.queue.put_nowait(sensor_data)
            except queue.Full:
                print(f"[PLAN1] Hang doi day - bo qua 1 ban ghi")
            
            if self.message_count % 10 == 0:
                self._print_stats()
                
        except Exception as e:
            print(f"[PLAN1] Loi xu ly message: {e}")

    def _worker_consume(self):
        while True:
            data = self.queue.get()
            try:
                success = self.vm_client.send_metrics(data)
                if success:
                    print(f"[PLAN1] [{self.message_count}] Temp: {data['temperature']}C, "
                          f"Humidity: {data['humidity']}%, "
                          f"Pressure: {data['pressure']}hPa -> VictoriaMetrics [OK]")
                else:
                    print(f"[PLAN1] [{self.message_count}] Loi luu vao VictoriaMetrics")
            finally:
                self.queue.task_done()
    
    def on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        print("[PLAN1] Subscriber da ngat ket noi")
        self._print_final_stats()
    
    def _print_stats(self):
        """In thống kê định kỳ"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.message_count / elapsed if elapsed > 0 else 0
            vm_stats = self.vm_client.get_stats()
            
            print(f"[PLAN1] Thong ke: {self.message_count} messages, "
                  f"{rate:.2f} msg/s, {elapsed:.1f}s")
            print(f"[PLAN1] VictoriaMetrics: {vm_stats['success']} thanh cong, "
                  f"{vm_stats['errors']} loi, "
                  f"Success rate: {vm_stats['success_rate']:.1f}%")
    
    def _print_final_stats(self):
        """In thống kê cuối cùng"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            rate = self.message_count / elapsed if elapsed > 0 else 0
            vm_stats = self.vm_client.get_stats()
            
            print("\n" + "="*60)
            print("[PLAN1] THONG KE CUOI CUNG")
            print("="*60)
            print(f"Messages nhan tu MQTT: {self.message_count}")
            print(f"Thoi gian chay: {elapsed:.1f}s")
            print(f"Toc do: {rate:.2f} msg/s")
            print(f"\nVictoriaMetrics:")
            print(f"  Thanh cong: {vm_stats['success']}")
            print(f"  Loi: {vm_stats['errors']}")
            print(f"  Success rate: {vm_stats['success_rate']:.1f}%")
            print("="*60)
    
    def connect_and_listen(self):
        try:
            print(f"[PLAN1] Dang ket noi subscriber...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.client.loop_forever()
        except Exception as e:
            print(f"[PLAN1] Loi subscriber: {e}")
    
    def connect_and_listen_with_duration(self, duration_seconds: int):
        try:
            print(f"[PLAN1] Dang ket noi subscriber...")
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, 60)
            self.client.loop_start()
            time.sleep(duration_seconds)
            self.client.disconnect()
            self._print_final_stats()
        except Exception as e:
            print(f"[PLAN1] Loi subscriber: {e}")

def main():
    print("=" * 60)
    print("PHUONG AN 1: MQTT + Python + VictoriaMetrics")
    print("=" * 60)
    
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("role", nargs="?", choices=["publisher", "subscriber"], default=None)
    parser.add_argument("--duration", dest="duration", type=int, default=None)
    # New CLI flags
    parser.add_argument("--broker-host", dest="broker_host", default=None)
    parser.add_argument("--broker-port", dest="broker_port", type=int, default=None)
    parser.add_argument("--topic", dest="mqtt_topic", default=None)
    parser.add_argument("--vm-mode", dest="vm_mode", choices=["single", "cluster"], default=None)
    parser.add_argument("--vm-insert", dest="vm_insert", default=None)
    parser.add_argument("--vm-select", dest="vm_select", default=None)
    parser.add_argument("--workers", dest="workers", type=int, default=None)
    parser.add_argument("-h", "--help", action="help", help="Show this help message and exit")
    args = parser.parse_args()

    # Apply runtime overrides if provided
    global MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_TOPIC
    global VM_MODE, VM_INSERT_URL, VM_SELECT_URL
    if args.broker_host:
        MQTT_BROKER_HOST = args.broker_host
    if args.broker_port:
        MQTT_BROKER_PORT = args.broker_port
    if args.mqtt_topic:
        MQTT_TOPIC = args.mqtt_topic
    if args.vm_mode:
        VM_MODE = args.vm_mode
    if args.vm_insert:
        VM_INSERT_URL = args.vm_insert
    if args.vm_select:
        VM_SELECT_URL = args.vm_select

    if args.role == "publisher":
        # Chạy publisher
        publisher = SensorPublisher()
        try:
            publish_thread = publisher.connect_and_start()
            if publish_thread:
                if args.duration and args.duration > 0:
                    print(f"[PLAN1] Tu dong dung sau {args.duration}s...")
                    time.sleep(args.duration)
                    publisher.stop_publishing()
                    publisher.client.disconnect()
                    print("[PLAN1] Da dung thanh cong")
                else:
                    print("[PLAN1] Nhan Ctrl+C de dung...")
                    publish_thread.join()
            else:
                print("[PLAN1] Khong the khoi dong publisher")
        except KeyboardInterrupt:
            print("\n[PLAN1] Dang dung publisher...")
            publisher.stop_publishing()
            publisher.client.disconnect()
            print("[PLAN1] Da dung thanh cong")
    
    elif args.role == "subscriber":
        # Chạy subscriber
        subscriber = SensorSubscriber()
        if args.workers and args.workers > 0:
            subscriber.worker_count = args.workers
        try:
            if args.duration and args.duration > 0:
                print(f"[PLAN1] Chay subscriber trong {args.duration}s...")
                subscriber.connect_and_listen_with_duration(args.duration)
            else:
                print("[PLAN1] Nhan Ctrl+C de dung...")
                subscriber.connect_and_listen()
        except KeyboardInterrupt:
            print("\n[PLAN1] Dang dung subscriber...")
            subscriber.client.disconnect()
            subscriber._print_final_stats()
            print("[PLAN1] Da dung thanh cong")
    
    else:
        print("Su dung:")
        print("  python plan1_publisher.py publisher [--duration SECONDS] [--broker-host HOST] [--broker-port PORT] [--topic TOPIC] [--vm-mode single|cluster] [--vm-insert URL] [--vm-select URL]")
        print("  python plan1_publisher.py subscriber [--duration SECONDS] [--workers N] [--broker-host HOST] [--broker-port PORT] [--topic TOPIC] [--vm-mode single|cluster] [--vm-insert URL] [--vm-select URL]")

if __name__ == "__main__":
    main()
