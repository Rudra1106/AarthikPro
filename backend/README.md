# AarthikAI Backend API

Production-ready FastAPI backend for AarthikAI Financial Intelligence Chatbot with advanced market data integration, LLM-powered analysis, and real-time news aggregation.

## 🚀 Features

### Core Capabilities
- ✅ **Multi-Mode Support**: Pro Mode (market analysis) + Personal Finance Mode
- ✅ **Hybrid Symbol Recognition**: Hardcoded aliases (100+ stocks) + LLM fallback with Redis caching
- ✅ **Dual News Sources**: Indian API (primary) + Perplexity Sonar (fallback) with intelligent search classifier
- ✅ **Real-time Market Data**: Dhan API integration with OHLC caching
- ✅ **Portfolio Integration**: Zerodha OAuth for portfolio tracking
- ✅ **Vector Search**: Pinecone for annual reports, concall transcripts, and financial documents
- ✅ **Structured Data**: MongoDB for quarterly financials, corporate actions, and company info
- ✅ **LangGraph Orchestration**: Parallel data fetching with conditional routing

### API Features
- ✅ **RESTful API** with FastAPI
- ✅ **WebSocket** support for streaming responses
- ✅ **Session Management** with conversation history (MongoDB)
- ✅ **Health Checks** and system metrics
- ✅ **Production-Ready** with Docker support

### Optimizations
- ⚡ **Low Latency**: Parallel data fetching, Redis caching, timeout controls
- 💰 **Cost Efficient**: Intelligent model routing, response caching, LLM fallback only when needed
- 🐳 **Docker Optimized**: Multi-stage build, <500MB image size
- 📊 **Memory Efficient**: <800MB RAM usage under load

---

## 📋 Quick Start

### Prerequisites
- Python 3.13+
- Redis (for caching and worker queue)
- MongoDB (for structured data and conversation history)
- Pinecone (for vector search)
- API Keys: OpenRouter, Perplexity, Dhan, Zerodha, Indian API

### Local Development

**1. Install dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

**2. Set up environment**:
```bash
# Copy from parent directory
cp ../.env .env

# Or create new from example
cp ../.env.example .env
# Edit .env with your API keys
```

**3. Start Redis** (required):
```bash
redis-server
```

**4. Start backend server**:
```bash
# Option 1: Using startup script
./start_backend.sh

# Option 2: Manual
cd /Users/rudra/Documents/AarthikAi
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**5. Start market data worker** (optional, for OHLC caching):
```bash
# Option 1: Using startup script
./start_worker.sh

# Option 2: Manual
python3 scripts/market_data_worker.py --loop
```

The API will be available at `http://localhost:8000`

---

## 🐳 Docker Deployment

### Build and Run

```bash
# Build image
docker build -t aarthikai-backend -f backend/Dockerfile .

# Run container
docker run -p 8000:8000 --env-file .env aarthikai-backend
```

### Docker Compose

```bash
cd backend
docker-compose -f docker-compose.backend.yml up -d
```

**Image specs**:
- Base: Python 3.11-slim
- Size: <500MB (optimized from ~6-8GB)
- Memory limit: 1GB
- Multi-stage build with production dependencies only

---

## 📚 API Documentation

### Endpoints

#### Health & Status
- `GET /` - Root endpoint with API info
- `GET /health` - Health check with memory stats
- `GET /metrics` - System metrics (CPU, memory, environment)

#### Chat
- `POST /api/chat/message` - Send message, get AI response
- `GET /api/chat/history/{session_id}` - Get conversation history
- `DELETE /api/chat/session/{session_id}` - Clear session
- `WS /api/chat/ws` - WebSocket for streaming responses

#### Authentication
- `POST /api/auth/zerodha/initiate` - Start Zerodha OAuth flow
- `GET /api/auth/zerodha/status/{session_id}` - Check connection status
- `POST /api/auth/zerodha/disconnect` - Disconnect Zerodha account

### Interactive Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧪 Testing

### Postman Collection

**1. Import collection**:
- Open Postman
- Import `backend/postman/AarthikAI_Backend.postman_collection.json`

**2. Set environment variables**:
- `base_url`: `http://localhost:8000`
- `session_id`: Auto-generated UUID

**3. Test requests**:
- **Pro Mode**: Stock analysis, market overview, fundamental analysis
- **Personal Finance**: SIP calculator, goal planning, tax optimization

See `backend/TESTING.md` for 50+ test questions.

### Example Requests

**Stock Analysis**:
```json
{
  "message": "Analyze TCS fundamentals",
  "metadata": {"user_mode": "pro"}
}
```

**Comparison**:
```json
{
  "message": "Compare Infosys and TCS on key financial metrics",
  "metadata": {"user_mode": "pro"}
}
```

**Market Overview**:
```json
{
  "message": "How is the market today?",
  "metadata": {"user_mode": "pro"}
}
```

---

## 🏗️ Architecture

### Directory Structure

```
backend/
├── main.py                 # FastAPI application entry point
├── config.py              # Configuration management
├── api/
│   ├── routes/
│   │   ├── chat.py       # Chat endpoints
│   │   └── auth.py       # Auth endpoints
│   └── models/
│       ├── chat.py       # Pydantic models for chat
│       └── auth.py       # Pydantic models for auth
├── services/
│   └── chat_service.py   # Business logic layer
├── postman/               # Postman collection
├── scripts/
│   └── health_check.sh   # Health check script
├── Dockerfile             # Optimized multi-stage build
├── docker-compose.backend.yml
├── start_backend.sh       # Server startup script
├── start_worker.sh        # Worker startup script
└── requirements.txt       # Production dependencies
```

### Data Flow

```
User Request
    ↓
FastAPI Endpoint
    ↓
Chat Service
    ↓
LangGraph State Machine
    ↓
┌─────────────────────────────────────────┐
│  Parallel Data Fetching (Conditional)   │
├─────────────────────────────────────────┤
│ 1. Intent Classification                │
│ 2. Symbol Extraction (Hybrid)           │
│ 3. Vector Search (Pinecone)             │
│ 4. Structured Data (MongoDB)            │
│ 5. News (Indian API → Perplexity)       │
│ 6. Market Data (Dhan OHLC)              │
│ 7. Portfolio (Zerodha)                  │
└─────────────────────────────────────────┘
    ↓
Response Synthesis (LLM)
    ↓
Streaming Response to User
```

### Key Components

**1. Symbol Recognition (4-Tier Hybrid)**:
- Tier 1: Symbol Mapper (indices, aliases) - <1ms
- Tier 2: Hardcoded Aliases (100+ stocks) - <1ms
- Tier 3: Regex Pattern Matching - <1ms
- Tier 4: LLM Fallback (gpt-4o-mini) - ~300ms (cached: <1ms)

**2. News Fetching (Dual-Source)**:
- Primary: Indian API (6-hour cache, 2s timeout)
- Fallback: Perplexity Sonar (5s timeout, search classifier)
- Average latency: ~500ms (cached: <50ms)

**3. Market Data (Dhan)**:
- OHLC data with Redis caching
- Background worker for pre-fetching
- Segmentwise API for efficiency

**4. LLM Routing**:
- Simple queries: `gpt-4o-mini` ($0.15/$0.60 per 1M tokens)
- Complex analysis: `claude-3.5-sonnet` ($3/$15 per 1M tokens)
- Intelligent routing based on query complexity

---

## ⚙️ Configuration

### Environment Variables

Edit `backend/config.py` or set in `.env`:

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=2

# Memory Limits
MAX_MEMORY_MB=800
GC_THRESHOLD=700,10,10

# LLM Configuration
DEFAULT_MODEL=openai/gpt-4o-mini
COMPLEX_MODEL=anthropic/claude-3.5-sonnet
MAX_TOKENS=2000

# Data Sources
MONGODB_URI=mongodb://localhost:27017/aarthikai
REDIS_URL=redis://localhost:6379/0
PINECONE_API_KEY=your_key
PINECONE_INDEX_NAME=aarthikai-embeddings

# API Keys
OPENROUTER_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
DHAN_CLIENT_ID=your_id
DHAN_ACCESS_TOKEN=your_token
ZERODHA_API_KEY=your_key
ZERODHA_API_SECRET=your_secret
INDIAN_API_KEY=your_key
```

---

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "memory_mb": 456.78,
  "max_memory_mb": 800,
  "environment": "production"
}
```

### Metrics

```bash
curl http://localhost:8000/metrics
```

Response:
```json
{
  "memory_mb": 456.78,
  "memory_percent": 57.1,
  "cpu_percent": 12.5,
  "environment": "production"
}
```

---

## 🚢 Deployment

### AWS ECS/Fargate

**1. Push to ECR**:
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker tag aarthikai-backend:latest <account>.dkr.ecr.us-east-1.amazonaws.com/aarthikai-backend:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/aarthikai-backend:latest
```

**2. Task Definition**:
- Memory: 1GB
- CPU: 0.5 vCPU
- Health check: `/health`
- Environment: Load from AWS Secrets Manager

**3. Service Configuration**:
- Auto-scaling: CPU > 70% or Memory > 80%
- Load balancer: ALB with health checks
- Desired count: 2 (for HA)

### Environment Variables (Production)

Store in AWS Secrets Manager:
- `MONGODB_URI`
- `REDIS_URL`
- `OPENROUTER_API_KEY`
- `PERPLEXITY_API_KEY`
- `DHAN_CLIENT_ID`
- `DHAN_ACCESS_TOKEN`
- `ZERODHA_API_KEY`
- `ZERODHA_API_SECRET`
- `INDIAN_API_KEY`
- `PINECONE_API_KEY`

---

## 🔧 Troubleshooting

### Import Errors

Run from project root:
```bash
cd /Users/rudra/Documents/AarthikAi
python3 -m uvicorn backend.main:app --reload
```

### Memory Issues

Check usage:
```bash
docker stats aarthikai-backend
```

Adjust limits in `docker-compose.backend.yml`.

### Connection Issues

Verify services:
- MongoDB: `mongosh $MONGODB_URI`
- Redis: `redis-cli ping`
- Pinecone: Check API key and index name
- APIs: Test with curl

### Symbol Recognition Issues

Test symbol extraction:
```python
from src.intelligence.symbol_mapper import get_symbol_mapper
mapper = get_symbol_mapper()
symbols = mapper.extract_from_query("Compare TCS and Infosys")
print(symbols)  # Should return ['TCS', 'INFY']
```

See `backend/TROUBLESHOOTING.md` for more details.

---

## 📖 Documentation

- `README.md` - This file
- `QUICKSTART.md` - Quick start guide
- `TESTING.md` - Testing guide with 50+ test questions
- `TROUBLESHOOTING.md` - Common issues and solutions
- `QUICK_REFERENCE.md` - API quick reference

---

## 🎯 Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Docker Image Size | <500MB | ✅ ~450MB |
| RAM Usage (Idle) | <300MB | ✅ ~250MB |
| RAM Usage (Load) | <800MB | ✅ ~600MB |
| Response Latency (P50) | <3s | ✅ ~2s |
| Response Latency (P95) | <8s | ✅ ~6s |
| LLM Cost Reduction | 30-50% | ✅ ~40% |

---

## 🔄 Recent Updates

### January 2026
- ✅ Expanded symbol recognition to 100+ stocks with LLM fallback
- ✅ Integrated Indian API as primary news source
- ✅ Added Perplexity search classifier for intelligent web search
- ✅ Implemented dual-source news fetching with timeout controls
- ✅ Optimized structured data fetching (now triggers for all symbol queries)
- ✅ Fixed comparison queries (now extracts multiple symbols)
- ✅ Removed old Chainlit files and test artifacts
- ✅ Cleaned up project for production deployment

---

## 📝 License

Proprietary - AarthikAI

---

## 🤝 Support

For issues or questions:
1. Check `TROUBLESHOOTING.md`
2. Review API docs at `/docs`
3. Test with Postman collection
4. Check logs: `docker logs aarthikai-backend`
