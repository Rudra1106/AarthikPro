# Testing Guide - Pro & Personal Finance Modes

## Quick Start

### 1. Start Backend Server

```bash
cd /Users/rudra/Documents/AarthikAi

# Option A: Using startup script (recommended)
./backend/start_backend.sh

# Option B: Manual start
python3 -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Server will start on**: http://localhost:8000

### 2. Start Redis Worker (Optional - for market data)

In a **separate terminal**:

```bash
cd /Users/rudra/Documents/AarthikAi

# Option A: Using startup script
./backend/start_worker.sh

# Option B: Manual start
python3 scripts/market_data_worker.py --loop
```

**Note**: Worker is optional for basic testing. It's needed for:
- Real-time market data caching
- Background data updates
- FII/DII data

---

## Testing with Postman

### Setup

1. **Import Collection**:
   - Open Postman
   - Click "Import"
   - Select `backend/postman/AarthikAI_Backend.postman_collection.json`

2. **Variables** (auto-configured):
   - `base_url`: `http://localhost:8000`
   - `session_id`: Auto-generated UUID

### Test Sequence

#### Step 1: Health Check
Run: **Health & Status → Health Check**

Expected:
```json
{
  "status": "healthy",
  "memory_mb": 456.78,
  "max_memory_mb": 800,
  "environment": "development"
}
```

#### Step 2: Test Pro Mode
Run any request from **Pro Mode - Stock Queries** or **Pro Mode - Market Queries**

Example: **Stock Price - Reliance**

Request:
```json
{
  "message": "What is the current price of Reliance?",
  "session_id": "{{session_id}}",
  "metadata": {"user_mode": "pro"}
}
```

Expected Response:
```json
{
  "response": "The current price of Reliance Industries is ₹2,450.30...",
  "session_id": "...",
  "intent": "stock_price",
  "symbols": ["RELIANCE"],
  "metadata": {
    "latency_ms": 1250,
    "model_used": "gpt-4o-mini",
    "cost_estimate": 0.0012
  }
}
```

#### Step 3: Test Personal Finance Mode
Run any request from **Personal Finance Mode**

Example: **Emergency Fund Basics**

Request:
```json
{
  "message": "What is an emergency fund and why do I need one?",
  "session_id": "{{session_id}}",
  "metadata": {"user_mode": "personal"}
}
```

Expected Response:
```json
{
  "response": "An emergency fund is a dedicated savings account...",
  "session_id": "...",
  "intent": "pf_concept_explanation",
  "symbols": [],
  "metadata": {
    "latency_ms": 1800,
    "model_used": "gpt-4o-mini"
  }
}
```

---

## Test Questions by Mode

### Pro Mode - Stock Queries (9 questions)

#### Basic Stock Information
1. **Stock Price**: "What is the current price of Reliance?"
2. **Stock Overview**: "Tell me about Infosys stock"
3. **Multiple Stocks**: "Show me prices for TCS, Infosys, and Wipro"

#### Stock Analysis
4. **Fundamentals**: "Analyze TCS fundamentals and give me key metrics"
5. **Technical Analysis**: "What are the technical indicators for HDFC Bank?"
6. **Valuation**: "Is Reliance overvalued or undervalued right now?"

#### Comparisons
7. **Peer Comparison**: "Compare Infosys and TCS on key financial metrics"
8. **Sector Comparison**: "Compare top 3 IT stocks"
9. **Historical Comparison**: "How has Reliance performed vs Nifty 50 this year?"

### Pro Mode - Market Queries (10 questions)

#### Market Overview
10. **General Overview**: "Give me today's market overview"
11. **Market Sentiment**: "What's the overall market sentiment today?"
12. **Market Movers**: "What's driving the market today?"

#### Indices
13. **Index Performance**: "How is Nifty Bank performing compared to Nifty 50?"
14. **Sectoral Indices**: "Show me performance of all sectoral indices"
15. **Index Analysis**: "Why is Sensex up/down today?"

#### Market Data
16. **FII/DII**: "What is the FII and DII activity today?"
17. **Top Movers**: "Show me top 5 gainers and losers in Nifty 50"
18. **Volume Analysis**: "Which stocks have highest trading volume today?"

#### Sector Performance
19. **Sector Trends**: "Which sectors are performing well this year?"
20. **Sector Rotation**: "Is there any sector rotation happening?"

### Pro Mode - News & Events (5 questions)

21. **Company News**: "What's the latest news about HDFC Bank?"
22. **Sector News**: "Any major news in the banking sector?"
23. **Market News**: "What are the top market news today?"
24. **Earnings**: "When is TCS announcing earnings?"
25. **Corporate Actions**: "Any upcoming dividends or splits in Nifty 50?"

### Personal Finance Mode - Basics (8 questions)

#### Financial Concepts
26. **Emergency Fund**: "What is an emergency fund and why do I need one?"
27. **SIP Basics**: "Explain SIP to me like I'm a beginner. How does it work?"
28. **Mutual Funds**: "What are mutual funds? Should I invest in them?"
29. **Compound Interest**: "Explain compound interest with an example"

#### Investment Types
30. **Debt vs Equity**: "Should I invest in debt or equity funds? What's the difference?"
31. **Index Funds**: "What are index funds? Are they good for beginners?"
32. **Fixed Deposits**: "Is FD a good investment option?"
33. **PPF vs EPF**: "What's the difference between PPF and EPF?"

### Personal Finance Mode - Goal Planning (7 questions)

#### Specific Goals
34. **House Purchase**: "I want to buy a house worth 50 lakhs in 5 years. How much should I invest monthly?"
35. **Retirement**: "I'm 30 years old. How much should I save for retirement?"
36. **Child Education**: "I need 20 lakhs for my child's education in 10 years. What should I do?"
37. **Car Purchase**: "I want to buy a car worth 10 lakhs in 2 years. Help me plan"

#### General Planning
38. **Investment Strategy**: "I'm 28 years old with 50k monthly savings. What's a good investment strategy for me?"
39. **Risk Assessment**: "How do I know my risk appetite for investments?"
40. **Portfolio Allocation**: "How should I allocate my portfolio between debt and equity?"

### Personal Finance Mode - Tax & Savings (5 questions)

41. **Tax Saving**: "What are the best tax-saving investment options under 80C?"
42. **Tax Optimization**: "How can I reduce my tax liability legally?"
43. **NPS Benefits**: "Should I invest in NPS? What are the tax benefits?"
44. **ELSS vs PPF**: "Which is better for tax saving - ELSS or PPF?"
45. **Capital Gains**: "How is capital gains tax calculated on stocks?"

### Personal Finance Mode - Advanced (5 questions)

46. **Rebalancing**: "When and how should I rebalance my portfolio?"
47. **Diversification**: "How much diversification is enough?"
48. **Market Timing**: "Should I wait for market correction to invest?"
49. **Lump Sum vs SIP**: "I have 5 lakhs. Should I invest lump sum or via SIP?"
50. **Emergency Situations**: "I lost my job. Should I stop my SIPs?"

---

## Mode Differences

### Pro Mode
- **Purpose**: Professional stock analysis and market intelligence
- **Audience**: Traders, investors, analysts
- **Features**:
  - Real-time stock prices
  - Technical and fundamental analysis
  - Market overview and trends
  - News and events
  - Sector performance
- **Data Sources**: Zerodha, Dhan, NSE, Perplexity, MongoDB

### Personal Finance Mode
- **Purpose**: Financial education and goal planning
- **Audience**: Beginners, retail investors
- **Features**:
  - Concept explanations
  - Goal-based planning
  - Investment strategy
  - Tax optimization
  - Risk assessment
- **Approach**: Educational, beginner-friendly, no jargon

---

## Testing Tips

### 1. Test Both Modes Separately
Use different `session_id` for Pro and Personal Finance to avoid context mixing:

```json
// Pro Mode
{
  "session_id": "pro-session-123",
  "metadata": {"user_mode": "pro"}
}

// Personal Finance Mode
{
  "session_id": "pf-session-456",
  "metadata": {"user_mode": "personal"}
}
```

### 2. Test Conversation Context
Send multiple related questions in same session:

**Pro Mode Example**:
1. "What is the price of Reliance?"
2. "Compare it with RIL's 52-week high"
3. "Show me its P/E ratio"

**Personal Finance Example**:
1. "What is SIP?"
2. "How much should I invest in SIP monthly?"
3. "Which mutual funds are good for SIP?"

### 3. Check Response Quality
Verify:
- ✅ Correct mode detection
- ✅ Appropriate response style (technical vs educational)
- ✅ Data accuracy
- ✅ Response time (<3s for simple queries)
- ✅ Proper error handling

### 4. Monitor Performance
Check `/metrics` endpoint after each test:
```bash
curl http://localhost:8000/metrics
```

Watch for:
- Memory usage staying under 800MB
- CPU usage reasonable
- No memory leaks over time

---

## Troubleshooting

### Backend Won't Start

**Error**: Import errors
```bash
# Install dependencies
pip install fastapi uvicorn websockets pydantic pydantic-settings psutil python-dotenv
```

**Error**: Port 8000 in use
```bash
# Use different port
python3 -m uvicorn backend.main:app --reload --port 8001
```

### Slow Responses

**Issue**: Queries taking >5s

**Solutions**:
1. Check if Redis worker is running (for cached data)
2. Verify MongoDB connection
3. Check API keys are valid
4. Monitor `/metrics` for memory issues

### Mode Not Working

**Issue**: Personal Finance mode giving Pro-style responses

**Check**:
1. Verify `metadata.user_mode` is set correctly
2. Check backend logs for mode detection
3. Ensure session_id is different for different modes

### No Real Data

**Issue**: Getting placeholder/mock data

**Solutions**:
1. Start Redis worker for market data
2. Check Dhan/Zerodha API keys
3. Verify MongoDB has data
4. Check network connectivity

---

## Next Steps

After testing:

1. ✅ **Verify both modes work**
2. ✅ **Test 10-15 questions from each mode**
3. ✅ **Check response quality and accuracy**
4. ⏳ **Build Docker image** and test
5. ⏳ **Load testing** with multiple concurrent requests
6. ⏳ **Deploy to AWS**

---

## Quick Reference

### Start Backend
```bash
./backend/start_backend.sh
```

### Start Worker
```bash
./backend/start_worker.sh
```

### Test with cURL
```bash
# Pro Mode
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Price of Reliance?", "session_id": "test", "metadata": {"user_mode": "pro"}}'

# Personal Finance Mode
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is SIP?", "session_id": "test", "metadata": {"user_mode": "personal"}}'
```

### Check Health
```bash
curl http://localhost:8000/health
```

### View Logs
Backend logs will show in terminal where you started the server.
