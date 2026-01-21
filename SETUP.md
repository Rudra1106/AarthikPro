# AarthikAI - Setup Guide

Complete setup instructions for running AarthikAI locally, either manually or with Docker.

---

## Prerequisites

### Required
- **Python 3.11+** (for manual setup)
- **Docker & Docker Compose** (for Docker setup)
- **Redis** (included in Docker setup, or install locally)

### API Keys Required
- **OpenRouter API Key** - For LLM access
- **Perplexity API Key** - For real-time news
- **Zerodha Kite Connect** - For live market data
- **MongoDB Atlas** - For structured financial data
- **Pinecone** - For vector search

---

## Quick Start (Docker - Recommended)

**One-command setup:**

```bash
# 1. Clone repository
git clone <your-repo-url>
cd AarthikAi

# 2. Create .env file (copy from .env.example)
cp .env.example .env

# 3. Edit .env with your API keys
nano .env  # or use your preferred editor

# 4. Start everything
docker-compose up --build
```

**Access the app:**
- Open browser: http://localhost:8000
- Redis: localhost:6379

**Stop the app:**
```bash
docker-compose down
```

---

## Manual Setup

### 1. Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\\Scripts\\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Install & Start Redis

**macOS (Homebrew):**
```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis
```

**Windows:**
- Download from: https://redis.io/download
- Or use Docker: `docker run -d -p 6379:6379 redis:alpine`

### 3. Configure Environment Variables

Create `.env` file in project root:

```bash
cp .env.example .env
```

Edit `.env` with your API keys:

```env
# LLM Configuration
OPENROUTER_API_KEY=your_openrouter_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Zerodha Configuration
ZERODHA_API_KEY=your_zerodha_api_key
ZERODHA_API_SECRET=your_zerodha_secret
ZERODHA_ACCESS_TOKEN=your_access_token

# MongoDB Configuration
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/PORTFOLIO_MANAGER
MONGODB_DATABASE=PORTFOLIO_MANAGER

# Pinecone Configuration
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=your_environment
PINECONE_INDEX_NAME=your_index_name

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Application Configuration
IS_DEVELOPMENT=true
LOG_LEVEL=INFO
```

### 4. Run the Application

```bash
# Activate virtual environment (if not already active)
source venv/bin/activate

# Start Chainlit app
chainlit run app.py -w
```

**Access the app:**
- Open browser: http://localhost:8000

---

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | `sk-or-v1-xxx` |
| `PERPLEXITY_API_KEY` | Perplexity API key for news | `pplx-xxx` |
| `ZERODHA_API_KEY` | Zerodha Kite Connect API key | `xxx` |
| `ZERODHA_API_SECRET` | Zerodha API secret | `xxx` |
| `ZERODHA_ACCESS_TOKEN` | Zerodha access token | `xxx` |
| `MONGODB_URI` | MongoDB connection string | `mongodb+srv://...` |
| `PINECONE_API_KEY` | Pinecone API key | `xxx` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379/0` |
| `IS_DEVELOPMENT` | Development mode flag | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

---

## Zerodha Setup

### 1. Create Kite Connect App
1. Go to https://developers.kite.trade/
2. Create new app
3. Note down API Key and Secret

### 2. Generate Access Token

```bash
# Run the Zerodha login script
python scripts/zerodha_login.py
```

Follow the instructions to:
1. Login to Zerodha
2. Authorize the app
3. Copy the access token to `.env`

**Note:** Access tokens expire daily. You'll need to regenerate them.

For detailed instructions, see [ZERODHA_SETUP.md](ZERODHA_SETUP.md)

---

## Troubleshooting

### Redis Connection Failed

**Error:** `Redis connection failed: max number of clients reached`

**Solution:**
- Check if Redis is running: `redis-cli ping` (should return `PONG`)
- Restart Redis: `brew services restart redis` (macOS) or `sudo systemctl restart redis` (Linux)
- Check Redis config: `redis-cli CONFIG GET maxclients`

### Instruments Loading Failed

**Error:** `Failed to load instruments`

**Solution:**
- Ensure Zerodha credentials are correct in `.env`
- Check if access token is valid (regenerate if expired)
- Verify internet connection

### MongoDB Connection Failed

**Error:** `MongoDB connection failed`

**Solution:**
- Verify `MONGODB_URI` in `.env`
- Check if IP is whitelisted in MongoDB Atlas
- Test connection: `mongosh "your_mongodb_uri"`

### Port Already in Use

**Error:** `Address already in use: 8000`

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
chainlit run app.py -w --port 8001
```

---

## Development Tips

### Hot Reload

Chainlit automatically reloads on file changes when using `-w` flag:
```bash
chainlit run app.py -w
```

### View Logs

```bash
# Tail application logs
tail -f logs/app.log

# View Redis logs (macOS)
tail -f /usr/local/var/log/redis.log
```

### Clear Redis Cache

```bash
# Clear all cache
redis-cli FLUSHDB

# Clear specific pattern
redis-cli KEYS "ohlc:*" | xargs redis-cli DEL
```

### Run Tests

```bash
# Run classification tests
python tests/test_question_classifier.py
python tests/test_combined_classification.py
```

---

## Production Checklist

Before deploying to production:

- [ ] Set `IS_DEVELOPMENT=false` in `.env`
- [ ] Use production MongoDB cluster
- [ ] Set up Redis with persistence
- [ ] Configure proper logging
- [ ] Set up monitoring (see [DEPLOYMENT.md](DEPLOYMENT.md))
- [ ] Enable HTTPS
- [ ] Set up backup strategy
- [ ] Configure rate limiting
- [ ] Review security settings

---

## Next Steps

- **Deploy to Production:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Configure Zerodha:** See [ZERODHA_SETUP.md](ZERODHA_SETUP.md)
- **Understand Architecture:** See [README.md](README.md)

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review logs for error details
3. Verify all environment variables are set correctly
