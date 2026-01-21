# Quick Reference - Backend Testing

## 🚀 Start Backend & Worker

### Terminal 1: Backend Server
```bash
cd /Users/rudra/Documents/AarthikAi
./backend/start_backend.sh
```
**URL**: http://localhost:8000

### Terminal 2: Redis Worker (Optional)
```bash
cd /Users/rudra/Documents/AarthikAi
./backend/start_worker.sh
```

---

## 📮 Postman Testing

### 1. Import Collection
- File: `backend/postman/AarthikAI_Backend.postman_collection.json`
- Variables auto-configured

### 2. Test Pro Mode
```json
{
  "message": "What is the price of Reliance?",
  "session_id": "{{session_id}}",
  "metadata": {"user_mode": "pro"}
}
```

### 3. Test Personal Finance Mode
```json
{
  "message": "What is an emergency fund?",
  "session_id": "{{session_id}}",
  "metadata": {"user_mode": "personal"}
}
```

---

## 🧪 Sample Test Questions

### Pro Mode (Stock & Market)
1. "What is the current price of Reliance?"
2. "Give me today's market overview"
3. "Analyze TCS fundamentals"
4. "Compare Infosys and TCS"
5. "Which sectors are performing well?"
6. "What's the latest news about HDFC Bank?"
7. "Show me top 5 gainers in Nifty 50"
8. "What is the FII and DII activity?"
9. "How is Nifty Bank performing?"

### Personal Finance Mode
1. "What is an emergency fund and why do I need one?"
2. "Explain SIP to me like I'm a beginner"
3. "I want to buy a house worth 50 lakhs in 5 years. How much should I invest?"
4. "Should I invest in debt or equity funds?"
5. "What are the best tax-saving options under 80C?"
6. "I'm 28 with 50k savings. What's a good strategy?"
7. "What are mutual funds?"
8. "How should I allocate my portfolio?"

**Full list**: See `backend/TESTING.md` for 50 questions

---

## ✅ Quick Health Check

```bash
# Health
curl http://localhost:8000/health

# Metrics
curl http://localhost:8000/metrics

# Test message
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test", "metadata": {"user_mode": "pro"}}'
```

---

## 📁 Key Files

- **Startup**: `backend/start_backend.sh`, `backend/start_worker.sh`
- **Postman**: `backend/postman/AarthikAI_Backend.postman_collection.json`
- **Testing Guide**: `backend/TESTING.md` (50 questions + troubleshooting)
- **API Docs**: http://localhost:8000/docs (when running)

---

## 🔧 Troubleshooting

**Import errors**: `pip install fastapi uvicorn websockets pydantic psutil`

**Port busy**: Use `--port 8001` instead

**Slow responses**: Start Redis worker for cached data

**See full guide**: `backend/TESTING.md`
