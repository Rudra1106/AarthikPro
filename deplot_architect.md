Railway Deployment Architecture - AarthikAI Chatbot
Overview
Deploy both Backend Chatbot and Market Data Worker on Railway platform.

Architecture Diagram
┌─────────────────────────────────────────────────┐
│           Railway Platform ($8-12/mo)           │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │   Service 1: Backend Chatbot (Web)      │  │
│  │   - FastAPI + Gunicorn                  │  │
│  │   - Port: 8000 (auto-assigned)          │  │
│  │   - Workers: 2                          │  │
│  │   - Health: /health                     │  │
│  │   - Auto-deploy from GitHub             │  │
│  │   - No sleep (always-on)                │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │   Service 2: Market Data Worker (BG)    │  │
│  │   - Python background job               │  │
│  │   - Caches OHLC data to Redis           │  │
│  │   - Runs every 2 minutes                │  │
│  │   - Auto-restart on failure             │  │
│  │   - No sleep (always-on)                │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  Shared Environment Variables                  │
│  - All API keys configured once               │
│  - Auto-synced between services               │
│                                                 │
└─────────────────┬───────────────────────────────┘
                  │
                  ↓
┌─────────────────────────────────────────────────┐
│         Shared External Services (Free)         │
│  ┌──────────────────────────────────────────┐  │
│  │ MongoDB Atlas (M0 - 512MB)              │  │
│  │ Redis Cloud (30MB)                      │  │
│  │ Pinecone (1 index, 100K vectors)        │  │
│  └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
Why Railway?
✅ Advantages
No Sleep Behavior

Services run continuously
No cold starts
Better for background workers
Better Multi-Service Support

Auto-detects Dockerfiles
Shared environment variables
Easy service-to-service communication
Cost-Effective

$5 trial credits
$5/month hobby plan + usage
Total: $8-12/month (vs $14 on Render)
Superior Developer Experience

Modern dashboard
Real-time logs
One-click rollbacks
Better monitoring
Usage-Based Pricing

Pay only for what you use
Transparent billing
No surprise costs
Deployment Steps
Step 1: Sign Up for Railway
Go to https://railway.app/
Click "Start a New Project"
Sign up with GitHub
Authorize Railway to access your repositories
Trial Credits: $5 free credits to start

Step 2: Create New Project
Click "New Project"
Select "Deploy from GitHub repo"
Choose repository: Rudra1106/AarthikPro
Railway will scan your repository
Step 3: Railway Auto-Detects Services
Railway automatically detects:

Service 1 (Backend):

Dockerfile: 
./Dockerfile
Type: Web service
Port: Auto-detected from Dockerfile
Service 2 (Worker):

Dockerfile: 
./Dockerfile.worker
Type: Background worker
No port needed
Step 4: Configure Environment Variables
Add environment variables once (applies to both services):

Required Variables
# Environment
ENVIRONMENT=production
# OpenAI (for embeddings + LLM)
OPENAI_API_KEY=sk-...
# OpenRouter (for LLM)
OPENROUTER_API_KEY=sk-...
# Perplexity (for news/search)
PERPLEXITY_API_KEY=pplx-...
# Pinecone (for vector search)
PINECONE_API_KEY=...
PINECONE_INDEX_NAME=aarthikai-embeddings-v2
# MongoDB (from Atlas)
MONGODB_URI=mongodb+srv://...
# Redis (from Redis Cloud)
REDIS_URL=redis://...
# Dhan API (for market data)
DHAN_CLIENT_ID=...
DHAN_ACCESS_TOKEN=...
# Zerodha API (for portfolio)
ZERODHA_API_KEY=...
ZERODHA_API_SECRET=...
# Indian API (for news)
INDIAN_API_KEY=...
INDIAN_API_BASE_URL=https://stock.indianapi.in
# Workers (optional)
WORKERS=2
How to Add:

Go to project settings
Click "Variables"
Add each variable
Click "Add" for each
Step 5: Deploy Services
Click "Deploy" for each service
Railway builds Docker images
Services start automatically
Monitor deployment logs
Build Time: ~5-10 minutes per service

Step 6: Get Service URLs
Backend Chatbot:

Railway auto-generates URL
Example: https://aarthikai-chatbot-production.up.railway.app
Custom domain available (optional)
Worker:

No public URL (background service)
Accessible via Railway dashboard logs
Step 7: Verify Deployment
Test Backend Health
curl https://your-backend-url.up.railway.app/health
Expected response:

{
  "status": "healthy",
  "timestamp": "2026-01-22T...",
  "version": "1.0.0"
}
Test Chat API
curl -X POST https://your-backend-url.up.railway.app/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is TCS stock price?",
    "metadata": {"user_mode": "pro"}
  }'
Check Worker Logs
Go to Railway dashboard
Select worker service
View logs
Should see: "✅ OHLC update complete"
Cost Breakdown
Railway Pricing
Trial: $5 free credits Hobby Plan: $5/month + usage

Estimated Monthly Cost
Service	vCPU	RAM	Cost/Month
Backend	0.5	512MB	$4-6
Worker	0.25	256MB	$2-4
Total			$8-12
Cost Comparison
Platform	Monthly Cost	Sleep?	Notes
Railway	$8-12	❌ No	Always-on, best value
Render Free	$0	✅ Yes	750hrs/month, sleeps after 15min
Render Paid	$14	❌ No	$7 per service
AWS t3.small	$30	❌ No	Full control, more expensive
Winner: Railway ($8-12/month)

Railway Configuration Files (Optional)
Backend Service Config
Create railway.json:

{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
Worker Service Config
Create railway.worker.json:

{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile.worker"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ALWAYS"
  }
}
Monitoring & Logs
Railway Dashboard
Metrics Available:

CPU usage
Memory usage
Network traffic
Request count
Response time
Logs:

Real-time log streaming
Filter by service
Search logs
Download logs
Health Monitoring
Backend:

Health endpoint: /health
Auto-restart on failure
Email alerts available
Worker:

Process monitoring
Auto-restart on crash
Redis connection health
Auto-Deploy Setup
GitHub Integration
Railway automatically deploys on:

Push to main branch
Pull request merge
Manual trigger
Workflow:

# Make changes locally
git add .
git commit -m "Update feature"
git push origin main
# Railway automatically:
# 1. Detects push
# 2. Builds Docker images
# 3. Deploys both services
# 4. Zero downtime deployment
Scaling
Horizontal Scaling
Backend:

Increase replicas in Railway dashboard
Load balancing automatic
Cost increases proportionally
Worker:

Can run multiple instances
Ensure idempotency in worker logic
Vertical Scaling
Upgrade resources:

More vCPU
More RAM
Better performance
Troubleshooting
Build Fails
Issue: Docker build fails

Solution:

Check Railway build logs
Verify Dockerfile syntax
Ensure all dependencies in requirements.txt
Test build locally: docker build -t test .
Service Won't Start
Issue: Service crashes on startup

Solution:

Check Railway logs
Verify environment variables set
Test MongoDB/Redis connections
Ensure Pinecone index exists
High Costs
Issue: Monthly bill higher than expected

Solution:

Check resource usage in dashboard
Reduce vCPU/RAM if over-provisioned
Optimize worker interval (increase from 2min to 5min)
Review logs for errors causing restarts
External Services Setup
MongoDB Atlas (Free M0)
Go to https://www.mongodb.com/cloud/atlas/register
Create free M0 cluster (512MB)
Whitelist IP: 0.0.0.0/0
Get connection string
Add to Railway env vars
Redis Cloud (Free 30MB)
Go to https://redis.com/try-free/
Create free database (30MB)
Get connection string
Add to Railway env vars
Pinecone (Free Tier)
Go to https://www.pinecone.io/
Create free account
Create index:
Name: aarthikai-embeddings-v2
Dimensions: 1536
Metric: cosine
Get API key
Add to Railway env vars
Custom Domain (Optional)
Add Custom Domain
Go to Railway project settings
Click "Domains"
Add custom domain: chat.yourdomain.com
Update DNS records as instructed
Railway auto-provisions SSL
Cost: Free (SSL included)

Backup & Recovery
Database Backups
MongoDB Atlas:

Automatic backups (free tier)
Point-in-time recovery
Download backups
Redis Cloud:

Automatic backups
Daily snapshots
Code Backups
GitHub:

All code in Git
Easy rollback via Railway
Tag releases for stability
Security Best Practices
Environment Variables
✅ Do:

Store all secrets in Railway env vars
Never commit 
.env
 to Git
Rotate API keys regularly
❌ Don't:

Hardcode secrets in code
Share env vars publicly
Use same keys for dev/prod
Network Security
Railway provides HTTPS by default
Auto-renewing SSL certificates
DDoS protection included
Migration from Render
If you already have 
render.yaml
:

Railway ignores 
render.yaml
Uses Dockerfiles instead
No migration needed
Just deploy to Railway
Summary
✅ Railway Deployment Ready
Services:

Backend Chatbot (FastAPI)
Market Data Worker (Background)
Cost: $8-12/month

Features:

✅ No sleep behavior
✅ Auto-deploy from GitHub
✅ Shared environment variables
✅ Real-time monitoring
✅ Auto-restart on failure
✅ HTTPS included
Next Steps:

Sign up at railway.app
Connect GitHub repository
Add environment variables
Deploy both services
Verify health endpoints
Deployment Time: ~20 minutes

🚀 Ready to deploy on Railway!