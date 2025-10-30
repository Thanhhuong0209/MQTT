# PHƯƠNG ÁN 1: MQTT + Python + VictoriaMetrics

## Mục tiêu & Kết quả

- Gửi dữ liệu cảm biến (giả lập) qua MQTT, nhận ở Subscriber, chuyển sang Prometheus text exposition và ghi vào VictoriaMetrics.
- Hỗ trợ VictoriaMetrics Single-node và Cluster (khuyến nghị Cluster).
- Thỏa yêu cầu hiệu năng demo: đạt xấp xỉ ≥ 1 message/giây với Windows + PowerShell (dùng 5–6 worker).

Trong test thực tế gần nhất (Windows): 60 giây, 5 worker đạt ~0.97 msg/s, 6 worker đạt ≥1 msg/s ổn định.

## Kiến trúc

```
Python Publisher (Sensor giả lập)
    ↓ MQTT Publish (QoS=1)
MQTT Broker (EMQX/Mosquitto)
    ↓ MQTT Subscribe
Python Subscriber (queue + worker threads + HTTP session reuse)
    ↓ HTTP POST (Prometheus text exposition)
VictoriaMetrics (single hoặc cluster)
```

## Chế độ triển khai

- Single-node (đơn giản): VM HTTP `8428` (UI `http://localhost:8428/vmui`)
- Cluster (khuyến nghị khi demo/scale):
  - vminsert: `http://localhost:8480` (ingest)
  - vmselect: `http://localhost:8481` (query / UI `http://localhost:8481/select/0/vmui`)
  - vmstorage-0: `:8482`, vmstorage-1: `:8483`

## Cài đặt

### 1) Yêu cầu môi trường

- Python 3.10+ (khuyến nghị 3.11 trở lên)
- Podman (đã đăng nhập internet để pull image lần đầu)
- Windows PowerShell (đã test trên Windows 11)

### 2) Cài đặt dependencies Python

```bash
pip install -r requirements_all_plans.txt
```

### 3) Khởi động dịch vụ

```powershell
# Single node + EMQX (đơn giản):
python podman_setup.py

# Hoặc Cluster mode (khuyến nghị):
python vm_cluster_setup.py
```

Kiểm tra nhanh:
- MQTT (EMQX) broker: `localhost:1883` – EMQX Dashboard: `http://localhost:18083` (mặc định `admin` / `public`).
- VictoriaMetrics Cluster UI (vmselect): `http://localhost:8481/select/0/vmui`.

## Sử dụng

### CLI flags

`plan1_publisher.py` hỗ trợ tham số cấu hình lúc chạy:

```bash
python plan1_mqtt_vm/plan1_publisher.py <publisher|subscriber> \
  [--duration SECONDS] \
  [--broker-host HOST] [--broker-port PORT] [--topic TOPIC] \
  [--vm-mode single|cluster] [--vm-insert URL] [--vm-select URL] \
  [--workers N] [--queue-size SIZE]
```

Ví dụ (Cluster – mặc định):

```bash
python plan1_mqtt_vm/plan1_publisher.py publisher --duration 60
python plan1_mqtt_vm/plan1_publisher.py subscriber --duration 60 --workers 5
```

Ví dụ (Single-node):

```bash
python plan1_mqtt_vm/plan1_publisher.py subscriber \
  --vm-mode single --vm-insert http://localhost:8428 --vm-select http://localhost:8428
```

Ví dụ (đổi broker/topic):

```bash
python plan1_mqtt_vm/plan1_publisher.py publisher --broker-host localhost --broker-port 1883 --topic sensor/data
```

### Demo “1 lệnh duy nhất” (PowerShell – khuyến nghị khi trình bày)

Publisher chạy nền, Subscriber chạy foreground để hiển thị thống kê; 60 giây, 6 worker (≥1 msg/s ổn định):

```powershell
Start-Job -ScriptBlock { python 'C:\Users\DELL\Desktop\MQTT\plan1_mqtt_vm\plan1_publisher.py' publisher --duration 60 } | Out-Null; Start-Sleep -Seconds 1; python 'C:\Users\DELL\Desktop\MQTT\plan1_mqtt_vm\plan1_publisher.py' subscriber --duration 60 --workers 6; Get-Job | Wait-Job | Out-Null; Get-Job | Receive-Job | Out-Null; Get-Job | Remove-Job | Out-Null
```

Lưu ý PowerShell:
- Không dùng `&&` để nối lệnh (PowerShell không hỗ trợ như Bash). Dùng `;` hoặc các cmdlet như trên.

### Kiểm tra dữ liệu trong VictoriaMetrics

Script truy vấn:

```bash
python plan1_mqtt_vm/query_vm.py --query sensor_temperature
```

Hoặc gọi trực tiếp PromQL API (Cluster):

```bash
curl "http://localhost:8481/select/0/prometheus/api/v1/query?query=sensor_temperature"
```

## Dữ liệu được lưu

4 metrics:
- `sensor_temperature_celsius{sensor_id="...", location="..."}` (°C)
- `sensor_humidity_percent{sensor_id="...", location="..."}` (%)
- `sensor_pressure_hpa{sensor_id="...", location="..."}` (hPa)
- `sensor_battery_level_percent{sensor_id="...", location="..."}` (%)

Timestamp Prometheus ở đơn vị giây (epoch seconds) theo chuẩn text exposition.

## Broker

- Mặc định dùng **EMQX** (có dashboard, dễ quan sát trong demo). Có thể thay bằng **Mosquitto**:

```bash
podman run -d --name mosquitto -p 1883:1883 eclipse-mosquitto:2
```

Không cần sửa mã vì kết nối dùng `localhost:1883` và topic cấu hình qua flag `--topic`.

## Tối ưu hiệu năng (đạt ≥1 msg/s)

- Tăng `--workers` của Subscriber (5–6 trên Windows ổn định ≥1 msg/s).
- Có thể tăng `--queue-size` nếu log báo đầy hàng đợi.
- Giữ thời lượng demo 60–90 giây để thống kê mượt hơn.

## Troubleshooting

- Query trả 400/422: kiểm tra URL dùng đúng vmselect (Cluster): `http://localhost:8481/select/0/prometheus/api/v1`.
- Cluster không ingest: đảm bảo `vminsert`/`vmselect` trỏ đúng `vmstorage` (cổng nội bộ `8400` cho vminsert, `8401` cho vmselect) và cùng network `vm_net` (đã thiết lập trong `vm_cluster_setup.py`).
- HTTP 204 từ vminsert là thành công đối với import Prometheus text exposition.
- PowerShell không hỗ trợ `&&`; dùng `;` hoặc `Start-Job`/`Start-Process`.
- Không thấy dữ liệu ngay: đợi vài giây hoặc F5 VMUI; hoặc tăng thời lượng chạy.

## PromQL gợi ý

- `sensor_temperature_celsius`
- `avg by (location) (sensor_temperature_celsius)`
- `increase(sensor_temperature_celsius[5m])`
- `topk(5, sensor_temperature_celsius)`

---

