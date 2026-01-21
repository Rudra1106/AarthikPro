# AarthikAI Chatbot Backend

> **Professional Financial Intelligence API** - REST API backend for stock analysis, market data, and financial insights powered by LangGraph and LLMs.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Integration Guide](#integration-guide)
- [File Structure](#file-structure)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Performance & Optimization](#performance--optimization)
- [Security](#security)
- [Contributing](#contributing)

---

## 🎯 Overview

AarthikAI is a sophisticated financial intelligence chatbot backend that provides real-time stock analysis, market data, news aggregation, and portfolio management capabilities. Built with FastAPI and LangGraph, it offers a production-ready REST API for seamless frontend integration.

### What Makes It Special?

- **🧠 Intelligent Intent Classification** - Understands natural language queries about stocks, markets, and finances
- **📊 Real-Time Market Data** - Live prices from Zerodha/Dhan APIs
- **📰 News Aggregation** - Latest financial news via Perplexity and Indian API
- **🔍 Vector Search** - Semantic search through financial reports using Pinecone
- **💼 Portfolio Integration** - Zerodha OAuth for portfolio analysis
- **⚡ High Performance** - Redis caching, semantic caching, and optimized data fetching
- **🔒 Production Ready** - Error handling, logging, rate limiting, and CORS support

---

## ✨ Features

### Core Capabilities

- **Stock Analysis**
  - Real-time stock prices (NSE/BSE)
  - Company fundamentals and financials
  - Technical indicators
  - Peer comparison
  
- **Market Intelligence**
  - Market overview (Nifty, Sensex, FII/DII data)
  - Sector performance analysis
  - Market sentiment and trends
  
- **News & Insights**
  - Latest stock-specific news
  - Market news and analysis
  - Sector-wise news aggregation
  
- **Portfolio Management** (via Zerodha OAuth)
  - Holdings analysis
  - Position tracking
  - Portfolio performance metrics
  
- **Conversation Management**
  - Session-based chat history
  - Context-aware responses
  - Multi-turn conversations

### Technical Features

- **LangGraph Integration** - Sophisticated multi-step reasoning workflows
- **Streaming Responses** - Server-Sent Events (SSE) for real-time updates
- **Semantic Caching** - Reduce API costs and improve response times
- **Vector Database** - Pinecone for document search and retrieval
- **MongoDB Storage** - Structured data and conversation history
- **Redis Caching** - Fast data retrieval and session management

---

## 🏗️ Architecture

```
┌─────────────┐
│   Frontend  │
│  (Your UI)  │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────────────────────────────┐
│       FastAPI Backend (main.py)     │
│  ┌───────────────────────────────┐  │
│  │  Routes: /api/chat, /session  │  │
│  │          /zerodha, /health    │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │    LangGraph Orchestration    │  │
│  │  (Intent → Fetch → Synthesize)│  │
│  └───────────────────────────────┘  │
└──────┬──────────────┬───────────────┘
       │              │
       ▼              ▼
┌─────────────┐  ┌──────────────┐
│   MongoDB   │  │  Pinecone    │
│ (Structured │  │  (Vectors)   │
│    Data)    │  │              │
└─────────────┘  └──────────────┘
       │              │
       ▼              ▼
┌─────────────┐  ┌──────────────┐
│    Redis    │  │  External    │
│  (Cache)    │  │   APIs       │
│             │  │ (Zerodha,    │
│             │  │  Perplexity) │
└─────────────┘  └──────────────┘
```

**Data Flow:**
1. Frontend sends user query to `/api/chat`
2. LangGraph classifies intent and extracts entities
3. Parallel data fetching (market data, news, vector search)
4. LLM synthesizes response from gathered data
5. Response streamed back to frontend

---

## 📦 Prerequisites

Before you begin, ensure you have:

- **Python 3.11 or higher** - [Download](https://www.python.org/downloads/)
- **MongoDB Atlas Account** - [Sign up](https://www.mongodb.com/cloud/atlas)
- **Redis Instance** - Local or cloud (e.g., [Redis Cloud](https://redis.com/try-free/))
- **API Keys:**
  - [OpenRouter](https://openrouter.ai/) - For LLM access (GPT-4, Claude)
  - [Perplexity](https://www.perplexity.ai/settings/api) - For news and web search
  - [Pinecone](https://www.pinecone.io/) - For vector database
  - [Zerodha Kite Connect](https://developers.kite.trade/) - For market data and portfolio
  - (Optional) [Dhan API](https://dhanhq.co/) - Alternative market data source

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Aarthik-ai/chatbot.git
cd chatbot/proChatbot
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials (see [Environment Variables](#environment-variables) section).

---

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

### LLM Configuration

```bash
# OpenRouter API key for LLM access (GPT-4, Claude, etc.)
# Get from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_key_here

# Perplexity API key for real-time news and web search
# Get from: https://www.perplexity.ai/settings/api
PERPLEXITY_API_KEY=your_perplexity_key_here
```

### Zerodha Configuration

```bash
# Zerodha API credentials for live market data
# Get from: https://developers.kite.trade/
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_secret

# Access token (expires daily - regenerate using scripts/zerodha_login.py)
ZERODHA_ACCESS_TOKEN=your_access_token

# Encryption key for storing access tokens (32+ characters)
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ZERODHA_ENCRYPTION_KEY=your-32-character-encryption-key-here

# OAuth redirect URL (must match Kite Connect app settings)
ZERODHA_REDIRECT_URL=http://localhost:8000/api/zerodha/callback
```

### MongoDB Configuration

```bash
# MongoDB Atlas connection string
# Format: mongodb+srv://username:password@cluster.mongodb.net/database
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/PORTFOLIO_MANAGER
MONGODB_DATABASE=PORTFOLIO_MANAGER

# Conversations database (for chat history)
MONGODB_CONVERSATIONS_DATABASE=aarthik_ai_conversations
```

### Pinecone Configuration

```bash
# Pinecone API key for vector search
# Get from: https://www.pinecone.io/
PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=aarthik-ai
PINECONE_ENVIRONMENT=us-east-1
```

### Redis Configuration

```bash
# Redis connection URL for caching
# Local: redis://localhost:6379/0
# Docker: redis://redis:6379/0
REDIS_URL=redis://localhost:6379/0
```

### API Configuration

```bash
# API server settings
API_HOST=0.0.0.0
API_PORT=8000

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001,https://yourdomain.com

# Rate limiting
RATE_LIMIT_PER_MINUTE=60
```

### Application Configuration

```bash
# Environment mode
ENVIRONMENT=development  # or 'production'

# Logging level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

---

## 🗄️ Database Setup

### MongoDB Setup

1. **Create MongoDB Atlas Cluster** (if you don't have one)
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
   - Create a free cluster
   - Get connection string

2. **Configure Database Access**
   - Add your IP to whitelist (or allow from anywhere for development)
   - Create database user with read/write permissions

3. **Update `.env`**
   ```bash
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
   MONGODB_DATABASE=PORTFOLIO_MANAGER
   ```

### Pinecone Setup

1. **Create Pinecone Account**
   - Sign up at [Pinecone](https://www.pinecone.io/)
   - Get API key from dashboard

2. **Create Index**
   ```bash
   # Run the setup script
   python scripts/setup_pinecone.py
   ```

   Or manually:
   ```python
   from pinecone import Pinecone
   
   pc = Pinecone(api_key="your-api-key")
   pc.create_index(
       name="aarthik-ai",
       dimension=1536,  # for text-embedding-3-small
       metric="cosine",
       spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
   )
   ```

3. **Verify Setup**
   ```bash
   python scripts/test_pinecone_connection.py
   ```

### Redis Setup

**Option 1: Local Redis**
```bash
# Install Redis (macOS)
brew install redis

# Start Redis
redis-server

# Verify
redis-cli ping  # Should return PONG
```

**Option 2: Redis Cloud**
- Sign up at [Redis Cloud](https://redis.com/try-free/)
- Get connection URL
- Update `REDIS_URL` in `.env`

---

## ▶️ Running the Application

### Development Mode

```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py directly
python main.py
```

### Production Mode

```bash
# Using Gunicorn with Uvicorn workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Verify It's Running

Open your browser and navigate to:
- **API Docs**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/health
- **Root**: http://localhost:8000/

---

## 🔌 API Endpoints

### Health Check

#### `GET /api/health`
Basic health check for the API and services.

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "mongodb": "connected",
    "redis": "connected",
    "pinecone": "available"
  },
  "version": "1.0.0"
}
```

#### `GET /api/health/detailed`
Detailed health check with service information.

---

### Chat

#### `POST /api/chat`
Main chat endpoint for processing user queries.

**Request:**
```json
{
  "message": "What is the current price of Reliance?",
  "session_id": "user-123-session-456",
  "mode": "pro"
}
```

**Response:**
```json
{
  "response": "Reliance Industries (RELIANCE) is currently trading at ₹2,450.50...",
  "intent": "stock_price",
  "symbols": ["RELIANCE"],
  "metadata": {
    "model_used": "gpt-4o-mini",
    "latency_ms": 1250,
    "cache_hit": false,
    "related_questions": [
      "What is Reliance's market cap?",
      "Show me Reliance's financials"
    ]
  }
}
```

#### `POST /api/chat/stream`
Streaming chat endpoint using Server-Sent Events (SSE).

**Request:** Same as `/api/chat`

**Response:** SSE stream
```
data: {"type": "status", "message": "Analyzing query..."}

data: {"type": "chunk", "content": "Reliance Industries..."}

data: {"type": "metadata", "intent": "stock_price", "symbols": ["RELIANCE"]}

data: {"type": "done"}
```

---

### Session Management

#### `POST /api/session/create`
Create a new chat session.

**Request:**
```json
{
  "user_id": "user-123"  // optional
}
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-17T10:00:00Z",
  "message": "Session created successfully"
}
```

#### `GET /api/session/{session_id}/history?limit=50`
Get conversation history for a session.

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "user",
      "content": "What is the price of Reliance?",
      "timestamp": "2026-01-17T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Reliance is trading at ₹2,450.50",
      "timestamp": "2026-01-17T10:00:02Z"
    }
  ],
  "total_count": 2
}
```

#### `DELETE /api/session/{session_id}`
Clear conversation history for a session.

---

### Zerodha Integration

#### `POST /api/zerodha/login`
Initiate Zerodha OAuth login flow.

**Request:**
```json
{
  "session_id": "user-123-session-456"
}
```

**Response:**
```json
{
  "login_url": "https://kite.zerodha.com/connect/login?api_key=xxx",
  "message": "Please visit the login URL to authorize"
}
```

#### `GET /api/zerodha/callback?request_token=xxx&status=success`
OAuth callback handler (called by Zerodha).

#### `GET /api/zerodha/status?session_id=xxx`
Check Zerodha connection status.

**Response:**
```json
{
  "connected": true,
  "user_id": "AB1234"
}
```

#### `POST /api/zerodha/disconnect?session_id=xxx`
Disconnect Zerodha account.

---

## 🔗 Integration Guide

### JavaScript/TypeScript Example

```typescript
// Create a session
const createSession = async () => {
  const response = await fetch('http://localhost:8000/api/session/create', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 'user-123' })
  });
  const data = await response.json();
  return data.session_id;
};

// Send a chat message
const sendMessage = async (sessionId: string, message: string) => {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message: message,
      session_id: sessionId,
      mode: 'pro'
    })
  });
  return await response.json();
};

// Usage
const sessionId = await createSession();
const result = await sendMessage(sessionId, 'What is the price of TCS?');
console.log(result.response);
```

### React Integration Example

```tsx
import { useState, useEffect } from 'react';

function ChatComponent() {
  const [sessionId, setSessionId] = useState<string>('');
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');

  useEffect(() => {
    // Create session on mount
    fetch('http://localhost:8000/api/session/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    })
      .then(res => res.json())
      .then(data => setSessionId(data.session_id));
  }, []);

  const handleSend = async () => {
    const res = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        session_id: sessionId,
        mode: 'pro'
      })
    });
    const data = await res.json();
    setResponse(data.response);
  };

  return (
    <div>
      <input value={message} onChange={(e) => setMessage(e.target.value)} />
      <button onClick={handleSend}>Send</button>
      <div>{response}</div>
    </div>
  );
}
```

### Streaming Example (SSE)

```javascript
const streamChat = (sessionId, message) => {
  const eventSource = new EventSource(
    `http://localhost:8000/api/chat/stream?` +
    new URLSearchParams({
      message: message,
      session_id: sessionId,
      mode: 'pro'
    })
  );

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'chunk') {
      // Append chunk to UI
      console.log(data.content);
    } else if (data.type === 'done') {
      eventSource.close();
    }
  };
};
```

---

## 📁 File Structure

```
proChatbot/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
│
├── api/                         # API layer
│   ├── __init__.py
│   ├── routes/                  # API route handlers
│   │   ├── __init__.py
│   │   ├── chat.py             # Chat endpoints
│   │   ├── session.py          # Session management
│   │   ├── zerodha.py          # Zerodha OAuth
│   │   └── health.py           # Health checks
│   └── models/                  # Pydantic models
│       ├── __init__.py
│       ├── request_models.py   # Request schemas
│       └── response_models.py  # Response schemas
│
├── src/                         # Core backend logic
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   │
│   ├── middleware/             # Custom middleware
│   │   ├── __init__.py
│   │   ├── error_handler.py   # Error handling
│   │   └── logger.py          # Request logging
│   │
│   ├── graph/                  # LangGraph orchestration
│   │   ├── graph.py           # Pro chatbot graph
│   │   ├── nodes.py           # Graph nodes
│   │   └── state.py           # State management
│   │
│   ├── data/                   # Data clients
│   │   ├── mongo_client.py    # MongoDB client
│   │   ├── redis_client.py    # Redis client
│   │   ├── vector_store.py    # Pinecone client
│   │   ├── zerodha_client.py  # Zerodha API
│   │   ├── dhan_client.py     # Dhan API
│   │   ├── perplexity_client.py # Perplexity API
│   │   └── conversation_history.py # Chat history
│   │
│   ├── intelligence/           # Intelligence modules
│   │   ├── symbol_mapper.py   # Stock symbol extraction
│   │   └── ...
│   │
│   ├── auth/                   # Authentication
│   │   ├── zerodha_oauth.py   # Zerodha OAuth flow
│   │   └── token_manager.py   # Token management
│   │
│   └── personal_finance/       # Personal finance mode
│       └── graph/
│           └── pf_graph.py    # Personal finance graph
│
├── scripts/                    # Utility scripts
│   ├── setup_pinecone.py      # Pinecone index setup
│   └── test_pinecone_connection.py # Connection test
│
├── vendor/                     # Vendored dependencies
│   └── nselib/                # NSE library (patched)
│
└── tests/                      # Test suite
    └── ...
```

### Key Files Explained

- **`main.py`** - FastAPI app initialization, middleware setup, route registration
- **`src/config.py`** - Centralized configuration using Pydantic Settings
- **`src/graph/graph.py`** - LangGraph workflow definition for pro chatbot
- **`src/graph/nodes.py`** - Individual graph nodes (intent classification, data fetching, synthesis)
- **`api/routes/chat.py`** - Main chat endpoint logic
- **`src/data/`** - All external service clients (MongoDB, Redis, Pinecone, APIs)
- **`src/middleware/`** - Custom middleware for error handling and logging

---

## 🧪 Testing

### Manual Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Create session
curl -X POST http://localhost:8000/api/session/create \
  -H "Content-Type: application/json"

# Send chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the price of Reliance?",
    "session_id": "test-session-123",
    "mode": "pro"
  }'

# Get session history
curl http://localhost:8000/api/session/test-session-123/history?limit=10
```

### Automated Testing

```bash
# Run tests (if you create them)
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 🚢 Deployment

### Docker Deployment (Optional)

Create `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

Build and run:
```bash
docker build -t aarthik-ai-backend .
docker run -p 8000:8000 --env-file .env aarthik-ai-backend
```

### Cloud Deployment

**AWS EC2 / Google Cloud / Azure VM:**

1. Set up VM with Python 3.11+
2. Clone repository
3. Install dependencies
4. Configure environment variables
5. Run with Gunicorn:
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```
6. Set up reverse proxy (Nginx) for HTTPS

**Heroku:**
```bash
# Create Procfile
echo "web: gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker" > Procfile

# Deploy
heroku create aarthik-ai-backend
git push heroku main
```

**Railway / Render:**
- Connect GitHub repository
- Set environment variables in dashboard
- Deploy automatically

---

## 🐛 Troubleshooting

### Common Issues

#### 1. MongoDB Connection Failed

**Error:** `MongoServerSelectionTimeoutError`

**Solution:**
- Check MongoDB URI in `.env`
- Verify IP whitelist in MongoDB Atlas
- Ensure database user has correct permissions

#### 2. Redis Connection Failed

**Error:** `ConnectionRefusedError`

**Solution:**
- Ensure Redis is running: `redis-cli ping`
- Check `REDIS_URL` in `.env`
- For cloud Redis, verify credentials

#### 3. Pinecone Index Not Found

**Error:** `Index 'aarthik-ai' not found`

**Solution:**
```bash
python scripts/setup_pinecone.py
```

#### 4. Zerodha Access Token Expired

**Error:** `TokenException: Invalid access token`

**Solution:**
- Zerodha tokens expire daily
- Re-login through OAuth flow
- Or regenerate token using Zerodha's token generation tool

#### 5. CORS Errors

**Error:** `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution:**
- Add your frontend URL to `CORS_ORIGINS` in `.env`
- Restart the server

### Debug Mode

Enable detailed logging:
```bash
# In .env
ENVIRONMENT=development
LOG_LEVEL=DEBUG
```

View logs:
```bash
# Logs will show in console
tail -f logs/app.log  # if you set up file logging
```

---

## ⚡ Performance & Optimization

### Caching Strategy

1. **Redis Caching** - Market data cached for 5 minutes
2. **Semantic Caching** - Similar queries return cached responses
3. **Vector Search** - Pre-computed embeddings in Pinecone

### Rate Limiting

Configure in `.env`:
```bash
RATE_LIMIT_PER_MINUTE=60
```

### Database Indexing

Ensure MongoDB indexes are created:
```javascript
// In MongoDB shell
db.financial_statements.createIndex({ symbol: 1, year: -1 })
db.conversations.createIndex({ session_id: 1, timestamp: -1 })
```

### Response Times

- **Stock Price Query:** ~1-2 seconds
- **Market Overview:** ~2-3 seconds
- **Complex Analysis:** ~3-5 seconds

---

## 🔒 Security

### Best Practices

1. **Environment Variables** - Never commit `.env` to Git
2. **API Keys** - Rotate keys regularly
3. **HTTPS** - Use HTTPS in production
4. **Rate Limiting** - Prevent abuse
5. **Input Validation** - Pydantic models validate all inputs
6. **Error Messages** - Don't expose sensitive info in errors

### Encryption

Zerodha tokens are encrypted using Fernet:
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()
```

---

## 📝 Updates & Changelog

### Version 1.0.0 (2026-01-17)

- Initial release
- FastAPI REST API
- LangGraph integration
- Zerodha OAuth
- Streaming responses (SSE)
- Comprehensive documentation

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 📞 Support

For issues or questions:
- **GitHub Issues:** [Create an issue](https://github.com/Aarthik-ai/chatbot/issues)
- **Email:** support@aarthik.ai
- **Documentation:** See `API_REFERENCE.md` and `INTEGRATION_GUIDE.md`

---

**Built with ❤️ by the AarthikAI Team**
