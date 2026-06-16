# RUN_LOCAL.md – Hướng dẫn chạy Lab 04

Tài liệu này giúp người khác clone repo sạch và chạy lại 2 services (IoT & Analytics) trong Docker.

---

## 1. Clone repo

```bash
git clone <repo-url>
cd FIT4110_lab04_docker_packaging
```

---

## 2. Cài dependencies cho Newman/Prism/Spectral

```bash
npm install
```

---

## 3. Build Docker Images

### Build IoT Service
```bash
docker build -f Dockerfile -t fit4110/iot-ingestion:lab04 .
```

### Build Analytics Service
```bash
docker build -f Dockerfile.analytics -t fit4110/analytics:lab04 .
```

Hoặc dùng Makefile:
```bash
make build:iot
make build:analytics
```

---

## 4. Run Services

### Cách 1: Chạy từng service riêng

**Terminal 1 - IoT Service:**
```bash
docker run --rm \
  --name fit4110-iot-lab04 \
  -p 8000:8000 \
  --env-file .env.example \
  fit4110/iot-ingestion:lab04
```

Kiểm tra health:
```bash
curl http://localhost:8000/health
```

Kết quả mong đợi:
```json
{
  "status": "ok",
  "service": "iot-ingestion",
  "version": "0.4.0"
}
```

**Terminal 2 - Analytics Service:**
```bash
docker run --rm \
  --name fit4110-analytics-lab04 \
  -p 8001:8001 \
  --env-file .env.analytics.example \
  fit4110/analytics:lab04
```

Kiểm tra health:
```bash
curl http://localhost:8001/api/v1/health
```

Kết quả mong đợi:
```json
{
  "status": "OK",
  "service": "analytics",
  "version": "0.4.0"
}
```

### Cách 2: Dùng Makefile

**Chạy cả 2 service:**
```bash
make run-all
```

**Chạy từng service:**
```bash
make run:iot      # Terminal 1
make run:analytics # Terminal 2
```

---

## 5. Chạy Postman Tests

### Test IoT Service
```bash
npm run test:local:iot
```

Report sinh tại:
```text
reports/newman-lab04-iot-local.xml
reports/newman-lab04-iot-local.html
```

### Test Analytics Service
```bash
npm run test:local:analytics
```

Report sinh tại:
```text
reports/newman-lab04-analytics-local.xml
reports/newman-lab04-analytics-local.html
```

### Test cả 2 services
```bash
make test-all
```

---

## 6. Dừng Services

```bash
docker stop fit4110-iot-lab04
docker stop fit4110-analytics-lab04
```

Hoặc dùng Makefile:
```bash
make stop-all
```

---

## 7. Lệnh nhanh (Makefile)

```bash
# Install dependencies
make install

# Build images
make build-all

# Run services (detached)
make run-all

# Health checks
make health:iot
make health:analytics

# Run tests
make test-all

# Stop services
make stop-all

# Clean reports
make clean-reports
```

---

## 8. Validate Contracts

```bash
make lint
npm run lint:openapi
```

---

## 9. Quick Troubleshooting

### Port already in use?
```bash
# Kill all containers
docker kill $(docker ps -q)

# Or use different ports
docker run --rm -p 9000:8000 ...
```

### View container logs
```bash
docker logs -f fit4110-iot-lab04
docker logs -f fit4110-analytics-lab04
```

### Remove all images
```bash
docker rmi fit4110/iot-ingestion:lab04 fit4110/analytics:lab04
```

---

## 10. Expected File Structure

```text
FIT4110_lab04_docker_packaging/
├── Dockerfile                    # IoT Service
├── Dockerfile.analytics          # Analytics Service
├── .env.example                  # IoT config
├── .env.analytics.example        # Analytics config
├── RUN_LOCAL.md                  # This file
├── src/
│   ├── iot_app/
│   │   ├── __init__.py
│   │   └── main.py
│   └── analytics_app/
│       ├── __init__.py
│       └── main.py
├── contracts/
│   ├── iot-ingestion.openapi.yaml
│   └── analytics-openapi.yaml
├── postman/
│   ├── collections/
│   │   ├── FIT4110_lab04_iot_docker.postman_collection.json
│   │   └── FIT4110_lab04_analytics_docker.postman_collection.json
│   ├── environments/
│   │   └── FIT4110_lab04_local.postman_environment.json
│   └── analytics-environments/
│       └── FIT4110_lab04_analytics_local.postman_environment.json
└── reports/
    ├── newman-lab04-iot-local.xml
    ├── newman-lab04-iot-local.html
    ├── newman-lab04-analytics-local.xml
    └── newman-lab04-analytics-local.html
```

```

---

## 7. Lệnh nhanh

```bash
make build
make run
make test-docker
make stop
```
