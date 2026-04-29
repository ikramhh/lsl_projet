# Traefik Integration Guide

## 🚀 Quick Start

### Start all services:
```bash
docker-compose up --build
```

## 🌐 Access URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Traefik Dashboard** | http://localhost:8080 | Monitor all routes |
| **API Service** | http://localhost/api | Django API |
| **Auth Service** | http://localhost/auth | Authentication |
| **AI Service** | http://localhost/ai | AI Prediction |
| **RabbitMQ** | http://localhost:15672 | Management UI (guest/guest) |

## 📊 Architecture

```
Client (Port 80)
    ↓
Traefik (Reverse Proxy)
    ├── /api → api_service:8001
    ├── /auth → auth_service:8003
    └── /ai → ai_service:8002
```

## ✅ Testing

### 1. Traefik Dashboard
Open: http://localhost:8080
- You should see 3 routers (api, auth, ai)
- Check HTTP services are healthy

### 2. Test API Service
```bash
# Via Traefik
curl http://localhost/api

# Direct (for comparison - only in dev)
curl http://localhost:8001
```

### 3. Test Auth Service
```bash
# Via Traefik
curl http://localhost/auth

# Direct
curl http://localhost:8003
```

### 4. Test AI Service
```bash
# Via Traefik
curl http://localhost/ai

# Direct
curl http://localhost:8002
```

### 5. Test Prediction Endpoint
```bash
curl -X POST http://localhost/api/predict/ \
  -H "Content-Type: application/json" \
  -d '{"image": "data:image/jpeg;base64,..."}'
```

## 🔧 Configuration

### Routing Rules (defined in docker-compose.yml labels):

- `/api` → api_service (port 8001)
- `/auth` → auth_service (port 8003)
- `/ai` → ai_service (port 8002)

### Environment Variables:
- `ALLOWED_HOSTS=*` - Allows Traefik to forward requests
- All services run on `0.0.0.0` internally

## 🐛 Troubleshooting

### Service not accessible via Traefik?
```bash
# Check Traefik logs
docker-compose logs traefik

# Check service logs
docker-compose logs api_service

# Verify labels are applied
docker inspect lsl_api | grep traefik
```

### 404 Error?
- Check if path prefix matches in Traefik dashboard
- Verify service is running: `docker-compose ps`

### CSRF Issues?
- In development, CSRF is disabled for API endpoints
- In production, configure CSRF_TRUSTED_ORIGINS

## 🛑 Stop Services

```bash
docker-compose down
```

## 📝 Notes

- Only Traefik exposes ports 80 and 8080
- RabbitMQ exposes 5672 (AMQP) and 15672 (UI)
- All Django services are internal (no direct port exposure)
- Traefik automatically discovers services via Docker labels
