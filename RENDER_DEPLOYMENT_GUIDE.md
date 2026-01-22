# 🚀 Render Deployment Guide - AarthikAI Chatbot

## Overview

Complete step-by-step guide to deploy your AarthikAI chatbot on Render's free tier.

---

## Prerequisites

✅ GitHub repository: `https://github.com/Rudra1106/AarthikPro.git`
✅ Render account (free): `https://render.com`
✅ External services ready:
- MongoDB Atlas (free M0 cluster)
- Redis Cloud (free 30MB)
- Pinecone (free tier)

---

## Step 1: Set Up External Services

### MongoDB Atlas (Free)

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create free account
3. Create new cluster:
   - **Tier**: M0 (Free)
   - **Region**: Choose closest to you
   - **Name**: aarthikai-cluster
4. Create database user:
   - Username: `aarthikai`
   - Password: (generate strong password)
5. Whitelist IP: `0.0.0.0/0` (allow from anywhere)
6. Get connection string:
   ```
   mongodb+srv://aarthikai:<password>@cluster0.xxxxx.mongodb.net/aarthik_ai?retryWrites=true&w=majority
   ```

### Redis Cloud (Free)

1. Go to https://redis.com/try-free/
2. Create free account
3. Create new database:
   - **Plan**: Free (30MB)
   - **Region**: Choose closest
4. Get connection string:
   ```
   redis://default:<password>@redis-xxxxx.cloud.redislabs.com:12345
   ```

### Pinecone (Free)

1. Go to https://www.pinecone.io/
2. Create free account
3. Create new index:
   - **Name**: `aarthikai-embeddings-v2`
   - **Dimensions**: 1536
   - **Metric**: cosine
   - **Region**: us-east-1
4. Get API key from dashboard

---

## Step 2: Deploy to Render

### 2.1 Sign Up for Render

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended)
4. Authorize Render to access your repositories

### 2.2 Create New Web Service

1. Click "New +" → "Web Service"
2. Connect your repository:
   - Select: `Rudra1106/AarthikPro`
   - Click "Connect"

### 2.3 Configure Service

**Basic Settings**:
- **Name**: `aarthikai-chatbot`
- **Region**: Oregon (or closest to you)
- **Branch**: `main`
- **Root Directory**: (leave empty)

**Build Settings**:
- **Environment**: Docker
- **Dockerfile Path**: `./Dockerfile`

**Plan**:
- Select: **Free** (750 hours/month)

### 2.4 Add Environment Variables

Click "Advanced" → "Add Environment Variable"

Add these variables:

```bash
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
MONGODB_URI=mongodb+srv://aarthikai:...

# Redis (from Redis Cloud)
REDIS_URL=redis://default:...

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
```

### 2.5 Deploy

1. Click "Create Web Service"
2. Wait for build (~5-10 minutes)
3. Monitor logs for any errors

---

## Step 3: Verify Deployment

### 3.1 Check Health Endpoint

Once deployed, Render will give you a URL like:
```
https://aarthikai-chatbot.onrender.com
```

Test health:
```bash
curl https://aarthikai-chatbot.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2026-01-22T...",
  "version": "1.0.0"
}
```

### 3.2 Test Chat API

```bash
curl -X POST https://aarthikai-chatbot.onrender.com/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the current price of TCS?",
    "metadata": {"user_mode": "pro"}
  }'
```

### 3.3 Monitor Logs

In Render dashboard:
1. Go to your service
2. Click "Logs" tab
3. Watch for any errors

---

## Step 4: Handle Free Tier Limitations

### Sleep After 15 Minutes

Render free tier services sleep after 15 minutes of inactivity.

**Solution 1: Accept Cold Starts**
- First request after sleep: ~2-3 minutes
- Subsequent requests: Fast

**Solution 2: Keep Alive with CRON**
1. Go to https://cron-job.org (free)
2. Create account
3. Add new cron job:
   - **URL**: `https://aarthikai-chatbot.onrender.com/health`
   - **Interval**: Every 10 minutes
   - **Title**: Keep AarthikAI Alive

This will ping your service every 10 minutes to prevent sleep.

---

## Step 5: Custom Domain (Optional)

### Add Custom Domain

1. In Render dashboard, go to your service
2. Click "Settings" → "Custom Domain"
3. Add your domain: `chat.yourdomain.com`
4. Update DNS records as instructed
5. Render will auto-provision SSL certificate

---

## Troubleshooting

### Build Fails

**Issue**: Dependencies fail to install

**Solution**:
```bash
# Check requirements.txt syntax
# Ensure all dependencies are compatible
# Check Render build logs for specific error
```

### Container Won't Start

**Issue**: Application crashes on startup

**Solution**:
1. Check Render logs
2. Verify all environment variables are set
3. Test MongoDB/Redis connections
4. Ensure Pinecone index exists

### Health Check Fails

**Issue**: `/health` endpoint returns 500

**Solution**:
```bash
# Check logs for error
# Verify database connections
# Ensure all required env vars are set
```

### High Memory Usage

**Issue**: Container uses >512MB RAM

**Solution**:
1. Reduce `WORKERS` to 1
2. Optimize code for memory
3. Consider upgrading to paid plan

---

## Monitoring

### Render Dashboard

Monitor:
- **Metrics**: CPU, Memory, Response time
- **Logs**: Real-time application logs
- **Events**: Deployments, restarts

### Set Up Alerts

1. Go to Settings → Notifications
2. Add email for:
   - Deploy failures
   - Service crashes
   - High resource usage

---

## Updating Your App

### Auto-Deploy

Every push to `main` branch automatically deploys!

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Render automatically:
# 1. Detects push
# 2. Builds new Docker image
# 3. Deploys with zero downtime
```

### Manual Deploy

In Render dashboard:
1. Go to your service
2. Click "Manual Deploy"
3. Select branch: `main`
4. Click "Deploy"

---

## Cost Breakdown

### Free Tier (Current)

| Service | Cost | Limits |
|---------|------|--------|
| Render | $0 | 750 hrs/month, sleeps after 15min |
| MongoDB Atlas | $0 | 512MB storage |
| Redis Cloud | $0 | 30MB storage |
| Pinecone | $0 | 1 index, 100K vectors |
| **Total** | **$0/month** | Perfect for demo/testing |

### Upgrade Path

When you need always-on service:

| Service | Cost | Benefits |
|---------|------|----------|
| Render Starter | $7/month | No sleep, 512MB RAM |
| MongoDB M2 | $9/month | 2GB storage |
| Redis 100MB | $5/month | More cache |
| **Total** | **$21/month** | Production-ready |

---

## Next Steps

1. ✅ Deploy to Render
2. ⏳ Test all API endpoints
3. ⏳ Set up CRON keep-alive (if needed)
4. ⏳ Monitor for 24 hours
5. ⏳ Add custom domain (optional)
6. ⏳ Set up monitoring alerts

---

## Quick Reference

### Your URLs

- **Render Dashboard**: https://dashboard.render.com
- **Your Service**: https://aarthikai-chatbot.onrender.com
- **Health Check**: https://aarthikai-chatbot.onrender.com/health
- **API Docs**: https://aarthikai-chatbot.onrender.com/docs

### Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com

---

## Summary

✅ **Free deployment** with Render
✅ **Auto-deploy** on Git push
✅ **HTTPS** included
✅ **Monitoring** built-in
✅ **Scalable** upgrade path

**Total setup time**: ~30 minutes
**Monthly cost**: $0

Ready to deploy! 🚀
