# Backend Troubleshooting Guide

## Common Issues & Solutions

### Issue 1: Pydantic Validation Errors

**Error**:
```
pydantic_core._pydantic_core.ValidationError: 28 validation errors for BackendSettings
Extra inputs are not permitted [type=extra_forbidden]
```

**Cause**: Backend config was rejecting environment variables from `.env`

**Solution**: ✅ **FIXED** - Updated `backend/config.py`:
- Added `extra = "ignore"` to allow extra fields
- Added `protected_namespaces = ('settings_',)` to avoid conflicts
- Renamed `model_timeout` → `llm_timeout` to avoid `model_` namespace warning

**Restart backend** after this fix.

---

### Issue 2: Import Errors

**Error**:
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution**:
```bash
pip install fastapi uvicorn websockets pydantic pydantic-settings psutil python-dotenv
```

---

### Issue 3: Port Already in Use

**Error**:
```
OSError: [Errno 48] Address already in use
```

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python3 -m uvicorn backend.main:app --reload --port 8001
```

---

### Issue 4: Redis Worker Errors

**Warning**:
```
Exception in dhanhq>>intraday_minute_data: interval value must be ['1','5','15','25','60']
```

**Cause**: Dhan API expects specific interval values

**Impact**: Index data won't be cached, but stock data will work

**Solution**: Worker will continue running, stock OHLC data is cached successfully

---

### Issue 5: Missing Stock Data

**Warning**:
```
No security IDs found for 6 symbols: KOTAKBANK, BAJFINANCE, etc.
```

**Cause**: Some symbols have different ISINs or are not in Dhan's database

**Impact**: These specific stocks won't have real-time data

**Solution**: Data will fall back to MongoDB or other sources

---

## Verification Steps

### 1. Check Backend is Running

```bash
curl http://localhost:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "memory_mb": 456.78,
  "max_memory_mb": 800,
  "environment": "development"
}
```

### 2. Test Simple Query

```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello",
    "session_id": "test-123",
    "metadata": {"user_mode": "pro"}
  }'
```

### 3. Check Worker Status

Worker logs should show:
```
✅ OHLC update complete: 113 success, 22 failed
```

This is normal - some stocks/indices may not have data.

---

## Quick Restart

If backend crashes, restart with:

```bash
# Stop all
pkill -f "uvicorn backend.main"
pkill -f "market_data_worker"

# Start backend
cd /Users/rudra/Documents/AarthikAi
./backend/start_backend.sh

# Start worker (optional, in new terminal)
./backend/start_worker.sh
```

---

## Next Steps After Fix

1. ✅ Backend config fixed
2. ⏳ Restart backend server
3. ⏳ Test with Postman
4. ⏳ Verify both Pro and Personal Finance modes work
