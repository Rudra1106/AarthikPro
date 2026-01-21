# 📦 Push Backend to Separate Git Repository

## Overview

This guide shows how to push **only the backend code** to a new Git repository, excluding all the frontend, data, and development files.

---

## Option 1: Create New Repo with Backend Only (Recommended)

### Step 1: Create New Git Repository

**On GitHub/GitLab**:
1. Go to GitHub.com (or your Git provider)
2. Click "New Repository"
3. Name: `aarthikai-backend`
4. Description: "AarthikAI Financial Intelligence Chatbot - Backend API"
5. Visibility: Private (recommended)
6. **Don't initialize** with README (we'll push existing code)
7. Click "Create repository"

### Step 2: Prepare Backend Directory

```bash
# Navigate to project root
cd /Users/rudra/Documents/AarthikAi

# Create a new directory for backend-only repo
mkdir -p ../aarthikai-backend-repo
cd ../aarthikai-backend-repo

# Initialize git
git init
```

### Step 3: Copy Backend Files

```bash
# Copy backend directory
cp -r ../AarthikAi/backend/* .

# Copy src directory (required for backend)
cp -r ../AarthikAi/src ./

# Copy essential root files
cp ../AarthikAi/.env.example .
cp ../AarthikAi/.gitignore .
cp ../AarthikAi/requirements.txt .
cp ../AarthikAi/README.md ./ROOT_README.md
cp ../AarthikAi/SETUP.md .
cp ../AarthikAi/DEPLOYMENT.md .

# Copy scripts (only production scripts)
mkdir -p scripts
cp ../AarthikAi/scripts/market_data_worker.py scripts/
cp ../AarthikAi/scripts/pdf_*.py scripts/ 2>/dev/null || true

# Copy vendor directory (if needed for nselib fix)
cp -r ../AarthikAi/vendor ./vendor 2>/dev/null || true
```

### Step 4: Create Backend-Specific README

```bash
# Rename backend README to root
mv README.md ROOT_README_BACKEND.md
cp ROOT_README_BACKEND.md README.md
```

### Step 5: Create .gitignore for Backend

```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg
*.egg-info/
dist/
build/
.pytest_cache/
.mypy_cache/
.ruff_cache/

# Virtual Environment
venv/
env/
ENV/

# Environment Variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Data (should be in external storage)
data/
*.csv
*.json
*.parquet
*.pkl

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Temporary
tmp/
temp/
*.tmp

# Large files
*.zip
*.tar.gz
*.pdf

# Redis dumps
dump.rdb

# Coverage
.coverage
htmlcov/
EOF
```

### Step 6: Create Project Structure README

```bash
cat > PROJECT_STRUCTURE.md << 'EOF'
# AarthikAI Backend - Project Structure

## Directory Layout

```
aarthikai-backend/
├── backend/                 # FastAPI application
│   ├── api/                # API routes and models
│   ├── services/           # Business logic
│   ├── main.py            # Application entry point
│   ├── config.py          # Configuration
│   ├── Dockerfile         # Production Docker image
│   └── requirements.txt   # Backend dependencies
├── src/                    # Core application logic
│   ├── graph/             # LangGraph state machine
│   ├── data/              # Data clients (Dhan, Zerodha, etc.)
│   ├── intelligence/      # Symbol mapper, query normalizer
│   ├── blueprints/        # Response templates
│   ├── services/          # External services
│   └── personal_finance/  # Personal finance mode
├── scripts/               # Production scripts
│   ├── market_data_worker.py  # OHLC caching worker
│   └── pdf_*.py          # PDF processing
├── vendor/                # Vendor fixes (nselib)
├── .env.example          # Environment variables template
├── requirements.txt      # Root dependencies
└── README.md            # Main documentation
```

## Quick Start

See `README.md` for complete setup and deployment instructions.

## Dependencies

- Python 3.13+
- Redis (caching and worker queue)
- MongoDB (structured data and history)
- Pinecone (vector search)
- API Keys: OpenRouter, Perplexity, Dhan, Zerodha, Indian API

## Deployment

See `DEPLOYMENT.md` for AWS ECS/Fargate deployment guide.
EOF
```

### Step 7: Initialize Git and Push

```bash
# Add all files
git add .

# Initial commit
git commit -m "Initial commit: AarthikAI Backend API

- FastAPI backend with multi-mode support (Pro + Personal Finance)
- Hybrid symbol recognition (100+ stocks + LLM fallback)
- Dual news sources (Indian API + Perplexity)
- Real-time market data (Dhan OHLC)
- Portfolio integration (Zerodha OAuth)
- Vector search (Pinecone) + Structured data (MongoDB)
- Docker optimized (<500MB image, <800MB RAM)
- Production-ready with health checks and monitoring"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/your-username/aarthikai-backend.git

# Push to main branch
git branch -M main
git push -u origin main
```

---

## Option 2: Use Git Subtree (Alternative)

### Create Subtree from Existing Repo

```bash
cd /Users/rudra/Documents/AarthikAi

# Create new branch for backend only
git subtree split --prefix=backend -b backend-only

# Create new repo directory
cd ..
mkdir aarthikai-backend-repo
cd aarthikai-backend-repo

# Initialize and pull backend branch
git init
git pull ../AarthikAi backend-only

# Add remote and push
git remote add origin https://github.com/your-username/aarthikai-backend.git
git push -u origin main
```

**Note**: This only includes `backend/` directory. You'll need to manually copy `src/` and other dependencies.

---

## Option 3: Use Git Filter-Branch (Advanced)

### Extract Backend History

```bash
# Clone original repo
git clone /Users/rudra/Documents/AarthikAi ../aarthikai-backend-repo
cd ../aarthikai-backend-repo

# Filter to keep only backend-related files
git filter-branch --subdirectory-filter backend -- --all

# This keeps only backend/ directory in history
# You'll need to manually add src/ and other files
```

---

## Recommended: Option 1 (Clean Start)

**Why**:
- ✅ Clean history (no development commits)
- ✅ Only production code
- ✅ Proper structure for backend-only repo
- ✅ Easy to maintain
- ✅ No large files or data in history

---

## Files to Include in Backend Repo

### Essential Files ✅
```
backend/                    # All backend code
src/                       # Core application logic
scripts/market_data_worker.py  # Production worker
scripts/pdf_*.py          # PDF processing
vendor/                   # Vendor fixes
.env.example             # Environment template
.gitignore              # Git ignore rules
requirements.txt        # Root dependencies
README.md              # Main documentation
SETUP.md               # Setup guide
DEPLOYMENT.md          # Deployment guide
PROJECT_STRUCTURE.md   # Structure overview
```

### Files to Exclude ❌
```
data/                  # Large data files
tests/                # Test files (already removed)
.chainlit/           # Old Chainlit files (already removed)
app.py              # Old Chainlit app (already removed)
venv/               # Virtual environment
*.csv               # Data files
*.log               # Log files
__pycache__/        # Python cache
```

---

## Post-Push Checklist

### 1. Verify Repository

```bash
# Clone your new repo
git clone https://github.com/your-username/aarthikai-backend.git
cd aarthikai-backend

# Check structure
ls -la

# Verify size (should be small)
du -sh .
```

### 2. Test Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy .env
cp .env.example .env
# Edit .env with your API keys

# Test backend
python -m uvicorn backend.main:app --reload
```

### 3. Update README

Update `README.md` with:
- Correct repository URL
- Installation instructions
- API documentation link
- Deployment guide

### 4. Add GitHub Actions (Optional)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to AWS ECS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1
      
      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: aarthikai-backend
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG -f backend/Dockerfile .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
      
      - name: Deploy to ECS
        run: |
          # Add ECS deployment commands
```

---

## Repository Settings

### Recommended Settings

**Branch Protection**:
- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date

**Secrets** (GitHub Settings → Secrets):
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
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

**Topics** (for discoverability):
- `fastapi`
- `langchain`
- `financial-analysis`
- `stock-market`
- `chatbot`
- `ai`
- `python`

---

## Summary

**Recommended approach**: Option 1 (Clean Start)

**Steps**:
1. ✅ Create new repo on GitHub
2. ✅ Copy backend files to new directory
3. ✅ Initialize git and commit
4. ✅ Push to remote
5. ✅ Verify and test

**Result**: Clean, production-ready backend repository! 🎉

---

## Quick Commands

```bash
# Complete setup in one go
cd /Users/rudra/Documents/AarthikAi
mkdir -p ../aarthikai-backend-repo
cd ../aarthikai-backend-repo
git init

# Copy files
cp -r ../AarthikAi/backend/* .
cp -r ../AarthikAi/src ./
cp ../AarthikAi/.env.example .
cp ../AarthikAi/requirements.txt .
mkdir -p scripts
cp ../AarthikAi/scripts/market_data_worker.py scripts/

# Git setup
git add .
git commit -m "Initial commit: AarthikAI Backend API"
git remote add origin https://github.com/your-username/aarthikai-backend.git
git branch -M main
git push -u origin main
```

Done! 🚀
