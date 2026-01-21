# Production Deployment Guide - AarthikAI Chatbot

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose installed
- `.env` file configured (copy from `.env.production`)
- API keys for OpenRouter, Perplexity, Zerodha, etc.

### One-Command Deployment

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f chainlit
```

Your chatbot will be available at: **http://localhost:8000**

---

## 📦 Services

The deployment includes 4 services:

1. **Redis** (Port 6379) - Caching layer
2. **OAuth Server** (Port 8080) - Zerodha authentication
3. **Market Worker** - Background data fetching
4. **Chainlit App** (Port 8000) - Main chatbot interface

---

## 🔧 Configuration

### 1. Environment Setup

```bash
# Copy production template
cp .env.production .env

# Edit with your API keys
nano .env
```

**Required Keys:**
- `OPENROUTER_API_KEY`
- `PERPLEXITY_API_KEY`
- `ZERODHA_API_KEY` & `ZERODHA_API_SECRET`
- `MONGODB_URI`
- `PINECONE_API_KEY`

### 2. Resource Limits

Default limits (adjust in `docker-compose.yml`):
- **Chainlit**: 1GB RAM, 1 CPU
- **Worker**: 512MB RAM, 0.5 CPU
- **Redis**: 256MB max memory

---

## 🏗️ Build & Deploy

### Development

```bash
# Start with logs
docker-compose up

# Rebuild after code changes
docker-compose up --build
```

### Production

```bash
# Build images
docker-compose build

# Start in detached mode
docker-compose up -d

# Scale Chainlit instances
docker-compose up -d --scale chainlit=3
```

---

## 📊 Monitoring

### Health Checks

```bash
# Check all services
docker-compose ps

# Chainlit health
curl http://localhost:8000

# Redis health
docker-compose exec redis redis-cli ping
```

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chainlit
docker-compose logs -f market-worker

# Last 100 lines
docker-compose logs --tail=100 chainlit
```

### Resource Usage

```bash
# Container stats
docker stats

# Redis memory
docker-compose exec redis redis-cli INFO memory
```

---

## 🔄 Updates & Maintenance

### Update Code

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Backup Redis Data

```bash
# Create backup
docker-compose exec redis redis-cli SAVE
docker cp aarthikai-redis:/data/dump.rdb ./backup/

# Restore
docker cp ./backup/dump.rdb aarthikai-redis:/data/
docker-compose restart redis
```

### Clear Cache

```bash
# Flush all Redis data
docker-compose exec redis redis-cli FLUSHALL

# Restart services
docker-compose restart
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs chainlit

# Restart specific service
docker-compose restart chainlit

# Full restart
docker-compose down
docker-compose up -d
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase limits in docker-compose.yml
# Then restart
docker-compose up -d
```

### Redis Connection Issues

```bash
# Test Redis
docker-compose exec redis redis-cli ping

# Check network
docker network inspect aarthikai-network

# Restart Redis
docker-compose restart redis
```

---

## 🔒 Security Best Practices

1. **Never commit `.env`** - Use `.env.production` as template only
2. **Use Docker secrets** for production API keys
3. **Enable firewall** - Only expose necessary ports
4. **Regular updates** - Keep Docker images updated
5. **Monitor logs** - Watch for suspicious activity

---

## 📈 Scaling

### Horizontal Scaling

```bash
# Run 3 Chainlit instances behind load balancer
docker-compose up -d --scale chainlit=3
```

### Vertical Scaling

Edit `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      memory: 2G  # Increase from 1G
      cpus: '2.0'  # Increase from 1.0
```

---

## 🌐 Production Deployment (Cloud)

### AWS ECS / Azure Container Instances

1. Push images to registry (ECR/ACR)
2. Create task definitions from `docker-compose.yml`
3. Configure load balancer
4. Set environment variables
5. Deploy

### Kubernetes

```bash
# Convert docker-compose to k8s
kompose convert -f docker-compose.yml

# Apply manifests
kubectl apply -f .
```

---

## 📞 Support

For issues:
1. Check logs: `docker-compose logs -f`
2. Verify `.env` configuration
3. Test individual services
4. Check resource usage

---

## ✅ Production Checklist

Before deploying to production:

- [ ] All API keys configured in `.env`
- [ ] Redis persistence enabled (RDB/AOF)
- [ ] Resource limits set appropriately
- [ ] Health checks passing
- [ ] Logs configured and monitored
- [ ] Backup strategy in place
- [ ] SSL/TLS configured (if public-facing)
- [ ] Firewall rules configured
- [ ] Monitoring/alerting setup (optional: Prometheus/Grafana)

---

## 🎯 Performance Tuning

### Redis Optimization

```bash
# Monitor Redis performance
docker-compose exec redis redis-cli --latency

# Check hit rate
docker-compose exec redis redis-cli INFO stats | grep keyspace
```

### Application Optimization

- Monitor response times in logs
- Adjust worker intervals in `.env`
- Scale Chainlit instances based on load
- Use CDN for static assets

---

**Your AarthikAI chatbot is now production-ready!** 🚀
