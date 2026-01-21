# 🚀 BGE Embedding Model - AWS Deployment Guide

## Your Current Setup

**Model**: `all-MiniLM-L6-v2` (from `settings.embedding_model`)
- **Size**: ~90MB
- **RAM**: ~120MB when loaded
- **Dimensions**: 384
- **Speed**: ~100-200ms per query (CPU)
- **Quality**: Good for general semantic search

**Location**: Used in `src/data/vector_store.py` for Pinecone queries

---

## AWS Deployment Impact

### ✅ Good News

Your current model (`all-MiniLM-L6-v2`) is **lightweight** and **AWS-friendly**:

1. **Memory**: Only ~120MB RAM
   - Your target: <800MB total
   - **Remaining**: ~680MB for FastAPI + other services ✅

2. **Docker Image**: Adds ~200MB
   - Base image: ~450MB
   - With model: ~650MB
   - **Still under 1GB** ✅

3. **Startup Time**: ~20-30 seconds
   - Model downloads on first run
   - Cached for subsequent starts ✅

4. **Performance**: Fast enough for production
   - First query: ~500ms (model loading)
   - Subsequent: ~100-200ms ✅

---

## Recommended AWS Configuration

### Option 1: Keep Current Model (Recommended)

**AWS Instance**: `t3.medium`
- **vCPU**: 2
- **RAM**: 4GB
- **Cost**: ~$30/month
- **Why**: Comfortable headroom for model + services

**Docker Configuration**:
```yaml
# docker-compose.yml
services:
  backend:
    image: aarthikai-backend:latest
    deploy:
      resources:
        limits:
          memory: 2G  # Plenty of room
          cpus: '1.0'
        reservations:
          memory: 1G
```

### Option 2: Upgrade to BGE-Small (Better Quality)

If you want better embedding quality:

```python
# In .env or config
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

**Impact**:
- **Size**: ~130MB (vs 90MB)
- **RAM**: ~150MB (vs 120MB)
- **Quality**: 10-15% better retrieval
- **Still fits in t3.medium** ✅

### Option 3: Use OpenAI Embeddings (No Model Loading)

For minimal memory footprint:

```python
# In src/data/vector_store.py
from openai import OpenAI

class VectorStore:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def _generate_embedding(self, text: str):
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
```

**Benefits**:
- **No model loading**: Instant startup
- **No RAM overhead**: Just API calls
- **Smaller Docker image**: ~450MB
- **Cost**: ~$0.02 per 1M tokens (~$0.0001/query)

**Drawbacks**:
- **API dependency**: Requires internet
- **Latency**: +50-100ms per query
- **Cost**: Small but ongoing

---

## Deployment Steps for AWS

### 1. Update Environment Variables

```bash
# On AWS EC2
cd /home/ubuntu/aarthikai

# Create .env
nano .env
```

Add:
```bash
# Embedding Model (choose one)
EMBEDDING_MODEL=all-MiniLM-L6-v2  # Current (lightweight)
# EMBEDDING_MODEL=BAAI/bge-small-en-v1.5  # Better quality
# EMBEDDING_MODEL=BAAI/bge-base-en-v1.5  # Best quality (more RAM)

# Pinecone
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=aarthikai-embeddings

# Other services...
```

### 2. Pull Latest Code

```bash
# On AWS EC2
cd /home/ubuntu/aarthikai
git pull origin main

# Verify vector_store.py exists
ls -la src/data/vector_store.py
```

### 3. Build and Deploy

```bash
# Build Docker image
docker-compose build

# Start services
docker-compose up -d

# Monitor logs
docker logs -f pro-chat-service
```

### 4. Verify Model Loading

```bash
# Check logs for model download
docker logs pro-chat-service 2>&1 | grep -i "sentence"

# Expected output:
# "Downloading sentence-transformers model..."
# "Model loaded successfully"
```

---

## Performance Optimization

### 1. Pre-download Model in Docker

Update `Dockerfile`:

```dockerfile
# Add after dependencies installation
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

**Benefit**: Model included in image, no download on startup

### 2. Use Model Caching

The model is already cached as a singleton in `vector_store.py`:

```python
_vector_store_instance: Optional[VectorStore] = None

def get_vector_store() -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStore()  # Loads model once
    return _vector_store_instance
```

**Benefit**: Model loaded once, reused for all queries ✅

### 3. Lazy Loading (Optional)

If you want faster startup:

```python
class VectorStore:
    def __init__(self):
        self.pc = Pinecone(api_key=settings.pinecone_api_key)
        self.embedding_model = None  # Don't load yet
    
    def _ensure_model_loaded(self):
        if self.embedding_model is None:
            self.embedding_model = SentenceTransformer(settings.embedding_model)
    
    def _generate_embedding(self, text: str):
        self._ensure_model_loaded()  # Load on first use
        return self.embedding_model.encode(text).tolist()
```

**Benefit**: Faster startup, model loads on first query

---

## Memory Monitoring

### Check Memory Usage

```bash
# On AWS EC2
docker stats pro-chat-service

# Expected output:
# CONTAINER    CPU %    MEM USAGE / LIMIT    MEM %
# pro-chat     5.2%     450MiB / 2GiB       22.5%
```

### If Memory is High

1. **Reduce workers**:
   ```bash
   # In Dockerfile or docker-compose
   CMD ["uvicorn", "backend.main:app", "--workers", "1"]  # Instead of 2
   ```

2. **Use smaller model**:
   ```bash
   EMBEDDING_MODEL=all-MiniLM-L6-v2  # Smallest
   ```

3. **Upgrade instance**:
   ```bash
   # From t3.medium (4GB) to t3.large (8GB)
   ```

---

## Cost Comparison

### Option 1: Local Model (Current)

**AWS Instance**: t3.medium
- **Cost**: $30/month
- **RAM**: 4GB
- **Embedding cost**: $0 (runs locally)
- **Total**: **$30/month**

### Option 2: OpenAI Embeddings

**AWS Instance**: t3.small (can use smaller)
- **Cost**: $15/month
- **RAM**: 2GB
- **Embedding cost**: ~$5/month (assuming 50K queries)
- **Total**: **$20/month**

**Winner**: OpenAI is cheaper if you have <100K queries/month

---

## Recommended Configuration

### For Your Use Case (Production Chatbot)

**Use current model** (`all-MiniLM-L6-v2`):
- ✅ Lightweight (~120MB RAM)
- ✅ Fast enough (~100-200ms)
- ✅ No API dependency
- ✅ No per-query cost
- ✅ Works offline

**AWS Setup**:
- **Instance**: t3.medium (4GB RAM)
- **Docker**: 2GB memory limit
- **Workers**: 2 uvicorn workers
- **Expected RAM**: ~400-600MB total

---

## Deployment Checklist

- [ ] Code pushed to GitHub ✅ (Done!)
- [ ] `vector_store.py` in repository ✅ (Verified!)
- [ ] Environment variables set on AWS
- [ ] Docker image built
- [ ] Model downloads successfully
- [ ] Memory usage <800MB
- [ ] First query completes (<2s)
- [ ] Subsequent queries fast (<500ms)

---

## Quick Deploy Commands

```bash
# On AWS EC2
cd /home/ubuntu
git clone https://github.com/Rudra1106/AarthikPro.git aarthikai
cd aarthikai

# Create .env
cp .env.example .env
nano .env  # Add your API keys

# Deploy
docker-compose up -d --build

# Monitor
docker logs -f pro-chat-service

# Test
curl http://localhost:5007/health
```

---

## Summary

**Your current setup is AWS-ready!** ✅

- **Model**: all-MiniLM-L6-v2 (lightweight)
- **RAM**: ~120MB (well within limits)
- **Performance**: Fast enough for production
- **Cost**: $30/month (t3.medium)

**No changes needed** - just deploy as-is! 🚀

The BGE model will **NOT** cause issues on AWS. Your current configuration is optimal for cost and performance.
