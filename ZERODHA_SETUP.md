# Zerodha OAuth Integration - Setup Guide

## 📋 Prerequisites

1. **Zerodha Trading Account** - Active Zerodha account
2. **Kite Connect App** - Created at [developers.kite.trade](https://developers.kite.trade/)

---

## 🔧 Step 1: Create Zerodha Kite Connect App

1. Go to [https://developers.kite.trade/](https://developers.kite.trade/)
2. Sign in with your Zerodha credentials
3. Click **"Create New App"**
4. Fill in the details:
   - **App Name**: AarthikAI (or your preferred name)
   - **Client ID**: Your Zerodha Client ID (e.g., AB1234)
   - **Redirect URL**: `http://localhost:8001/api/zerodha/callback`
   - **Postback URL**: (leave empty for now)

5. Click **"Create"**
6. You'll receive:
   - **API Key** (e.g., `abc123xyz456`)
   - **API Secret** (e.g., `def789ghi012`) - **Keep this secret!**

---

## 🔑 Step 2: Generate Encryption Key

Run this command to generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Copy the output (e.g., `gAAAAABh...`) - you'll need this for `.env`

---

## ⚙️ Step 3: Update Environment Variables

Add these to your `.env` file:

```bash
# Zerodha OAuth Configuration
ZERODHA_ENCRYPTION_KEY=<paste-your-generated-key-here>
ZERODHA_REDIRECT_URL=http://localhost:8001/api/zerodha/callback

# Make sure these are also set (from Step 1)
ZERODHA_API_KEY=<your-api-key>
ZERODHA_API_SECRET=<your-api-secret>
```

**Important**: The redirect URL must be `http://localhost:8001` (port 8001) because:
- Chainlit runs on port 8000
- OAuth server runs on port 8001

---

## 📦 Step 4: Install Dependencies

```bash
pip install cryptography
```

Or reinstall all requirements:

```bash
pip install -r requirements.txt
```

---

## 🚀 Step 5: Run the Application

You need to run **TWO servers** simultaneously:

### Terminal 1: OAuth Server (Port 8001)
```bash
python oauth_server.py
```

You should see:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### Terminal 2: Chainlit App (Port 8000)
```bash
chainlit run app.py
```

You should see:
```
Your app is available at http://localhost:8000
```

---

## ✅ Step 6: Test the Integration

1. Open [http://localhost:8000](http://localhost:8000) in your browser
2. You should see the chatbot interface
3. Type: **"Connect my Zerodha account"** (once we add the UI integration)
4. You'll be redirected to Zerodha login
5. After login, you'll be redirected back with a success message
6. Now you can ask portfolio questions!

---

## 🔍 Troubleshooting

### Error: "Invalid or expired OAuth state"
- **Cause**: State parameter mismatch or expired (> 5 minutes)
- **Fix**: Try connecting again

### Error: "Failed to decrypt token"
- **Cause**: `ZERODHA_ENCRYPTION_KEY` changed or not set
- **Fix**: Ensure encryption key is set correctly in `.env`

### Error: "Connection refused" on callback
- **Cause**: OAuth server not running
- **Fix**: Make sure `python oauth_server.py` is running on port 8001

### Redirect URL Mismatch
- **Cause**: Redirect URL in Kite Connect app doesn't match
- **Fix**: Ensure it's exactly `http://localhost:8001/api/zerodha/callback`

---

## 📊 What Data Can You Access?

Once connected, users can ask:

- **"What stocks do I own?"** - Shows holdings
- **"How is my portfolio performing?"** - Shows P&L
- **"What are my top gainers?"** - Analyzes performance
- **"Do I have any F&O positions?"** - Shows positions
- **"How much buying power do I have?"** - Shows margins

---

## 🔐 Security Notes

✅ **What we do:**
- Encrypt all access tokens with AES-256
- Use CSRF protection (state parameter)
- Store tokens in separate MongoDB database
- Never log sensitive data
- Tokens auto-expire after 24 hours

❌ **What we DON'T do:**
- Store passwords (Zerodha handles all authentication)
- Share tokens between users
- Place orders (read-only access)

---

## 🎯 Next Steps

After testing locally, for production deployment:

1. Update redirect URL in Kite Connect app to your production domain
2. Update `ZERODHA_REDIRECT_URL` in `.env`
3. Enable HTTPS (required by Zerodha)
4. Set up proper domain for OAuth server

---

## 📝 For Your Reference

**Redirect URL for local testing:**
```
http://localhost:8001/api/zerodha/callback
```

**Redirect URL for production (example):**
```
https://yourdomain.com/api/zerodha/callback
```

Make sure to update both:
1. Kite Connect app settings
2. `ZERODHA_REDIRECT_URL` in `.env`
