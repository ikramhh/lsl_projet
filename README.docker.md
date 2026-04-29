# Docker Setup - LSL Project

## 🚀 Quick Start

### 1. Build and Start All Services

```bash
docker-compose up --build
```

### 2. Start in Background (Detached Mode)

```bash
docker-compose up -d --build
```

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api_service
docker-compose logs -f ai_worker
docker-compose logs -f rabbitmq
```

### 4. Stop Services

```bash
docker-compose down
```

### 5. Stop and Remove Volumes

```bash
docker-compose down -v
```

## 📦 Services

| Service | Port | Description |
|---------|------|-------------|
| **RabbitMQ** | 5672, 15672 | Message broker + Management UI |
| **API Service** | 8001 | Main API & Frontend |
| **AI Service** | 8002 | ML Model REST API |
| **AI Worker** | - | Background worker (RabbitMQ consumer) |
| **Auth Service** | 8003 | Authentication & Users |

## 🌐 Access URLs

- **Frontend**: http://localhost:8001
- **RabbitMQ Management**: http://localhost:15672
  - Username: `guest`
  - Password: `guest`

## 🔧 Common Commands

### Rebuild Specific Service

```bash
docker-compose build api_service
```

### Run Migrations

```bash
docker-compose exec api_service python manage.py migrate
docker-compose exec auth_service python manage.py migrate
docker-compose exec ai_service python manage.py migrate
```

### Create Superuser

```bash
docker-compose exec api_service python manage.py createsuperuser
```

### Open Shell in Container

```bash
docker-compose exec api_service bash
docker-compose exec ai_service bash
```

### View Running Containers

```bash
docker-compose ps
```

## 📊 Architecture

```
Frontend (Browser)
    ↓
API Service (8001)
    ↓
RabbitMQ (5672)
    ↓
AI Worker → AI Model Prediction
```

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :8001

# Kill process
taskkill /PID <PID> /F
```

### Rebuild Without Cache

```bash
docker-compose build --no-cache
```

### View RabbitMQ Queue

1. Open http://localhost:15672
2. Login with guest/guest
3. Go to "Queues" tab
4. Check `asl_queue`

### Check Worker Logs

```bash
docker-compose logs -f ai_worker
```

## 📝 Environment Variables

Services use these environment variables:

```yaml
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest
```

## 🗄️ Volumes

Data is persisted in Docker volumes:

- `rabbitmq_data` - RabbitMQ messages
- `auth_db_data` - Auth service database
- `api_db_data` - API service database
- `ai_db_data` - AI service database

## 🔄 Development Workflow

1. **Code changes are hot-reloaded** (volumes mount source code)
2. **Rebuild only when dependencies change**:
   ```bash
   docker-compose build
   ```
3. **Restart services**:
   ```bash
   docker-compose restart
   ```

## 🛑 Clean Install

```bash
# Stop and remove everything
docker-compose down -v

# Remove old images
docker system prune -a

# Rebuild
docker-compose up --build
```
