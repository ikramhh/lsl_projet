# Consul Service Discovery Integration

## Overview
This document explains the Consul service discovery integration for the LSL (Sign Language) microservices project.

## What is Consul?
Consul is a service networking solution that provides:
- **Service Discovery**: Services register themselves and can be discovered by others
- **Health Checking**: Automatic monitoring of service health
- **Key-Value Storage**: Configuration storage
- **Multi-Datacenter**: Support for multiple datacenters (not used here)

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐                                       │
│  │   Traefik    │ ← Reverse Proxy (Port 8888)          │
│  └──────┬───────┘                                       │
│         │                                                │
│  ┌──────┴───────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Django API   │  │ AI Svc   │  │ Auth Service     │  │
│  │ (Port 8000)  │  │(Port 8002│  │ (Part of API)    │  │
│  └──────┬───────┘  └────┬─────┘  └────────┬─────────┘  │
│         │               │                  │             │
│         └───────────────┴──────────────────┘             │
│                         │                                │
│                  ┌──────┴──────┐                         │
│                  │   Consul    │ ← Service Registry      │
│                  │ (Port 8500) │   & Health Checks       │
│                  └─────────────┘                         │
│                                                          │
│  ┌──────────────────┐                                   │
│  │   RabbitMQ       │ ← Message Queue                   │
│  │ (Port 5672)      │                                   │
│  └──────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
```

## Services Registered in Consul

| Service Name | Port | Health Check URL | Description |
|-------------|------|------------------|-------------|
| `django-api` | 8000 | `/auth/` | Main API service with authentication |
| `ai-service` | 8002 | `/predict/` | AI model for gesture recognition |

## How It Works

### 1. Service Registration
When each service starts, it automatically registers with Consul:

```python
# register_consul.py
register_service(
    service_name='django-api',
    service_id='django-api-8000',
    address='lsl_django',
    port=8000,
    health_check_url='/auth/'
)
```

### 2. Service Discovery
Other services can discover registered services:

```python
# Discover AI service
response = requests.get('http://consul:8500/v1/catalog/service/ai-service')
ai_instances = response.json()

# Get AI service address
ai_address = ai_instances[0]['ServiceAddress']
ai_port = ai_instances[0]['ServicePort']
ai_url = f"http://{ai_address}:{ai_port}/predict/"
```

### 3. Health Checking
Consul automatically checks service health every 10 seconds:
- ✅ **Passing**: Service is healthy
- ⚠️ **Warning**: Service has issues
- ❌ **Critical**: Service is down

## Setup & Usage

### 1. Start All Services
```bash
docker-compose up -d
```

### 2. Access Consul UI
Open your browser and navigate to:
```
http://localhost:8500
```

You'll see:
- All registered services
- Health status
- Service metadata
- Key-value store

### 3. Test Service Discovery
```bash
# Enter the Django container
docker exec -it lsl_django bash

# Run discovery demo
python test_consul_discovery.py
```

### 4. Query Consul API Directly
```bash
# List all services
curl http://localhost:8500/v1/agent/services

# Get specific service
curl http://localhost:8500/v1/catalog/service/django-api

# Check service health
curl http://localhost:8500/v1/health/service/django-api
```

## Environment Variables

Each service uses these environment variables for Consul:

```yaml
CONSUL_HOST=consul              # Consul server hostname
CONSUL_PORT=8500                # Consul server port
CONSUL_SERVICE_NAME=django-api  # Service name in Consul
SERVICE_PORT=8000               # Service port
SERVICE_ADDRESS=lsl_django      # Service hostname
HEALTH_CHECK_URL=/auth/         # Health check endpoint
```

## Benefits of Service Discovery

### ✅ Without Consul (Hardcoded)
```python
# Problem: Hardcoded URLs
AI_SERVICE_URL = "http://lsl_ai:8002/predict/"
API_SERVICE_URL = "http://lsl_django:8000/api/"

# Issues:
# ❌ What if IP changes?
# ❌ What if port changes?
# ❌ What if service moves?
# ❌ No health checking
```

### ✅ With Consul (Dynamic Discovery)
```python
# Solution: Dynamic discovery
def get_ai_service_url():
    response = requests.get('http://consul:8500/v1/catalog/service/ai-service')
    instances = response.json()
    if instances:
        instance = instances[0]
        return f"http://{instance['ServiceAddress']}:{instance['ServicePort']}/predict/"
    raise Exception("AI service not found!")

# Benefits:
# ✅ Automatic service location
# ✅ Health checking built-in
# ✅ Load balancing ready
# ✅ No hardcoded URLs
```

## Integration with Existing Services

### Traefik (No Changes Needed)
- Traefik continues to work as reverse proxy
- Consul adds service discovery layer
- Both can work together

### RabbitMQ (No Changes Needed)
- RabbitMQ continues as message broker
- Services can discover RabbitMQ via Consul too

### Your Existing Code
- **Nothing breaks!**
- Consul is additive
- Your JWT auth, permissions, and routing still work

## Academic Project Demonstration

For your presentation/demo, show:

1. **Consul UI** (http://localhost:8500)
   - Visual proof of service registry
   - Health check status
   - Service metadata

2. **Service Discovery in Action**
   ```bash
   docker exec -it lsl_django python test_consul_discovery.py
   ```

3. **Health Checking**
   - Stop a service: `docker stop lsl_ai`
   - Watch Consul mark it as unhealthy
   - Start it again: `docker start lsl_ai`
   - Watch Consul mark it as healthy

4. **Dynamic Discovery**
   - Show how services find each other
   - No hardcoded IPs or ports
   - Works even if containers restart

## Consul API Examples

### Register a Service
```bash
curl -X PUT http://localhost:8500/v1/agent/service/register \
  -d '{
    "ID": "my-service-1",
    "Name": "my-service",
    "Port": 8080,
    "Check": {
      "HTTP": "http://localhost:8080/health",
      "Interval": "10s"
    }
  }'
```

### Deregister a Service
```bash
curl -X PUT http://localhost:8500/v1/agent/service/deregister/my-service-1
```

### Watch for Changes (Blocking Query)
```bash
curl http://localhost:8500/v1/catalog/service/django-api?index=1&wait=30s
```

## Troubleshooting

### Consul Not Starting
```bash
# Check logs
docker logs lsl_consul

# Restart
docker-compose restart consul
```

### Service Not Registered
```bash
# Check service logs
docker logs lsl_django | grep -i consul

# Manually register
docker exec -it lsl_django python register_consul.py
```

### Health Checks Failing
```bash
# Check health endpoint manually
curl http://localhost:8888/auth/

# Check Consul health
curl http://localhost:8500/v1/health/service/django-api
```

## Next Steps (Optional Enhancements)

1. **Service Mesh**: Use Consul Connect for service-to-service encryption
2. **Key-Value Config**: Store configuration in Consul KV store
3. **DNS Interface**: Use Consul's built-in DNS (port 8600)
4. **Load Balancing**: Use Consul with load balancers
5. **Multi-Datacenter**: Extend to multiple environments

## Resources

- [Consul Documentation](https://www.consul.io/docs)
- [Consul API Reference](https://www.consul.io/api-docs)
- [Service Discovery Pattern](https://microservices.io/patterns/service-discovery.html)

## Summary

This integration demonstrates:
- ✅ Service registry pattern
- ✅ Health checking
- ✅ Dynamic service discovery
- ✅ Microservices best practices
- ✅ Production-ready architecture

Perfect for academic projects and real-world applications! 🚀
