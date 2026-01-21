#!/bin/bash
# Start Redis Worker Script (for market data background processing)

echo "🔄 Starting Redis Worker..."
echo ""

# Check if we're in the right directory
if [ ! -f "scripts/market_data_worker.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   cd /Users/rudra/Documents/AarthikAi"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "⚠️  No virtual environment found. Using system Python."
fi

# Check if Redis is accessible
echo "🔍 Checking Redis connection..."
python3 -c "import redis; r = redis.from_url('${REDIS_URL:-redis://localhost:6379}'); r.ping()" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Warning: Cannot connect to Redis. Worker may not function properly."
    echo "   Make sure Redis is running or REDIS_URL is set correctly."
fi

echo ""
echo "✅ Starting market data worker..."
echo ""
echo "Press Ctrl+C to stop the worker"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start the worker
python3 scripts/market_data_worker.py --loop
