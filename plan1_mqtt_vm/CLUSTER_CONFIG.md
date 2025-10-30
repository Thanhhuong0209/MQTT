# CẤU HÌNH CHO VICTORIAMETRICS CLUSTER ĐÃ BUILD SẴN

## Cách cấu hình

Code đã được cập nhật để hỗ trợ cả **single node** và **cluster mode**.

### 1. Cập nhật Configuration

Mở file `plan1_mqtt_vm/plan1_publisher.py` và kiểm tra/cập nhật:

```python
# Mode: "single" hoặc "cluster"
VM_MODE = "cluster"  # Đổi thành "cluster"

# Cluster Configuration - Cập nhật theo cluster của bạn
VM_INSERT_URL = "http://localhost:8480"  # VMInsert endpoint
VM_SELECT_URL = "http://localhost:8481"  # VMSelect endpoint
```

**Nếu cluster của bạn dùng port khác, sửa lại:**

```python
VM_INSERT_URL = "http://YOUR_VMINSERT_HOST:PORT"
VM_SELECT_URL = "http://YOUR_VMSELECT_HOST:PORT"
```

### 2. Cập nhật Query Script

Mở file `query_vm.py` và cập nhật:

```python
VM_MODE = "cluster"
VM_SELECT_URL = "http://localhost:8481"  # Theo cluster của bạn
```

### 3. Kiểm tra Cluster

Đảm bảo cluster đang chạy:

```bash
# Kiểm tra các services
curl http://localhost:8480/health  # VMInsert
curl http://localhost:8481/health  # VMSelect

# Hoặc
podman ps | findstr vm
```

### 4. Chạy Demo

```bash
python demo_auto.py
# hoặc
python plan1_mqtt_vm/demo_plan1.py
```

### 5. Query Dữ liệu

```bash
python query_vm.py
```

## Endpoints cho Cluster

- **VMInsert** (gửi dữ liệu): `http://localhost:8480/insert/0/prometheus`
- **VMSelect** (query): `http://localhost:8481/api/v1/query`

## Chuyển về Single Node

Nếu muốn dùng single node:

```python
VM_MODE = "single"
VM_SINGLE_URL = "http://localhost:8428"
```

---

**Lưu ý**: 
- Cluster mode sẽ tự động sử dụng VMInsert để gửi dữ liệu
- Query sẽ dùng VMSelect
- Code tự động detect và sử dụng đúng endpoint
