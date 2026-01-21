# Quick Start Guide - Backend API

## Prerequisites

- Python 3.11+ installed
- MongoDB, Redis, Pinecone accessible (or use existing .env)
- API keys configured in `.env`

## Option 1: Run Locally (Fastest)

```bash
# From project root
cd /Users/rudra/Documents/AarthikAi

# Activate virtual environment (if you have one)
source venv/bin/activate  # or your venv path

# Install backend dependencies
pip install fastapi uvicorn websockets pydantic pydantic-settings psutil

# Run the backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Access**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Option 2: Docker (Production-like)

```bash
# Build the image
docker build -t aarthikai-backend -f backend/Dockerfile .

# Check image size
docker images aarthikai-backend

# Run the container
docker run -p 8000:8000 --env-file .env aarthikai-backend

# Check health
curl http://localhost:8000/health
```

## Option 3: Docker Compose

```bash
cd backend
docker-compose -f docker-compose.backend.yml up -d

# View logs
docker-compose logs -f backend

# Check stats
docker stats aarthikai-backend
```

## Testing with Postman

1. **Import Collection**:
   - Open Postman
   - Import `backend/postman/AarthikAI_Backend.postman_collection.json`

2. **Set Variables**:
   - `base_url`: `http://localhost:8000`
   - `session_id`: Auto-generated

3. **Run Tests**:
   - Health Check ✓
   - Send Message - Stock Price ✓
   - Send Message - Market Overview ✓
   - Get History ✓

## Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# Send a message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the price of Reliance?",
    "session_id": "test-123",
    "metadata": {}
  }'

# Get history
curl http://localhost:8000/api/chat/history/test-123
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running from the project root:
```bash
cd /Users/rudra/Documents/AarthikAi
python -m uvicorn backend.main:app --reload
```

### Port Already in Use

If port 8000 is busy:
```bash
# Use different port
python -m uvicorn backend.main:app --reload --port 8001
```

### Missing Dependencies

Install all backend dependencies:
```bash
pip install -r backend/requirements.txt
```

## Next Steps

1. ✅ Backend created
2. ⏳ **Test with Postman** ← You are here
3. ⏳ Build Docker image
4. ⏳ Verify optimizations
5. ⏳ Deploy to AWS
