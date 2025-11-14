# 🚀 Deploy MustangsAI with Google Gemini (95% CHEAPER!)

## Why Use Gemini?

**Cost Comparison:**
- **Google Gemini:** ~$0.20 per 1000 queries (95% cheaper!)
- **OpenAI (gpt-4o-mini):** ~$1.50 per 1000 queries

**Your $248 budget:**
- **Gemini:** 1,240,000 queries 🎉
- **OpenAI:** 165,000 queries

**Free Tier Benefits:**
- Embeddings: FREE up to 1500 requests/day
- gemini-1.5-flash: FREE up to 15 requests/min

---

## 🔑 Get Your Gemini API Key (30 seconds)

1. Go to: **https://aistudio.google.com/app/apikey**
2. Sign in with Google account
3. Click **"Get API key"** → **"Create API key"**
4. Copy the key (starts with `AIza...`)

**That's it! No credit card required for free tier!**

---

## ⚙️ Setup Instructions

### Step 1: Configure Environment

Create a `.env` file (or copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` and set:

```bash
# Enable Gemini
USE_GEMINI=true

# Add your Gemini API key
GOOGLE_API_KEY=AIza...your-actual-key-here

# Models (already optimized for cost)
GEMINI_EMBED_MODEL=models/embedding-001
GEMINI_CHAT_MODEL=gemini-1.5-flash
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This includes `langchain-google-genai` and `google-generativeai`.

### Step 3: Scrape Data (if not already done)

```bash
python scraper.py
```

### Step 4: Build Vector Database with Gemini Embeddings

```bash
python ingest.py
```

**Output:**
```
[ingest] Using Google Gemini embeddings: models/embedding-001
[ingest] Loading 215 unique URLs...
[ingest] Successfully loaded 215 web docs.
[ingest] Chunked into 1847 passages.
[ingest] Saved FAISS index to vectorstore/faiss_index.
```

**Cost:** FREE (within free tier limits)!

### Step 5: Run the App

```bash
streamlit run app.py
```

Access at: **http://localhost:8501**

---

## ☁️ Deploy to Cloud with Gemini

### Railway Deployment

1. Go to: https://railway.app/new
2. Deploy from GitHub: `Saimudragada/MustangsAI`
3. Branch: `claude/build-mustangsai-rag-01XtZxWvoMGpGt7RzsH14TpZ`
4. **Environment Variables:**
   ```
   USE_GEMINI=true
   GOOGLE_API_KEY=AIza...your-key-here
   GEMINI_EMBED_MODEL=models/embedding-001
   GEMINI_CHAT_MODEL=gemini-1.5-flash
   ```
5. Deploy!

### Streamlit Cloud Deployment

1. Go to: https://share.streamlit.io
2. New app → Connect repo
3. **Secrets:**
   ```toml
   USE_GEMINI = "true"
   GOOGLE_API_KEY = "AIza...your-key-here"
   GEMINI_EMBED_MODEL = "models/embedding-001"
   GEMINI_CHAT_MODEL = "gemini-1.5-flash"
   ```
4. Deploy!

---

## 📊 Gemini Model Options

### Chat Models

| Model | Cost (per 1M tokens) | Speed | Quality | Free Tier |
|-------|---------------------|-------|---------|-----------|
| **gemini-1.5-flash** | $0.075/$0.30 | ⚡⚡⚡ | ⭐⭐⭐ | 15 req/min |
| gemini-1.5-pro | $1.25/$5.00 | ⚡⚡ | ⭐⭐⭐⭐⭐ | 2 req/min |
| gemini-2.0-flash-exp | FREE | ⚡⚡⚡ | ⭐⭐⭐⭐ | Experimental |

**Recommended:** `gemini-1.5-flash` (fast, cheap, good quality)

### Embedding Models

| Model | Cost | Free Tier |
|-------|------|-----------|
| **models/embedding-001** | FREE | 1500 req/day |

---

## 💰 Real Cost Examples

### Scenario 1: 10,000 Queries/Month
- **Gemini (flash):** ~$2/month
- **OpenAI (gpt-4o-mini):** ~$15/month
- **Savings:** $13/month (87% cheaper)

### Scenario 2: 100,000 Queries/Month
- **Gemini (flash):** ~$20/month
- **OpenAI (gpt-4o-mini):** ~$150/month
- **Savings:** $130/month (87% cheaper)

### Your $248 Budget
- **Gemini:** Lasts ~12+ months at 10k queries/month
- **OpenAI:** Lasts ~1.6 months at 10k queries/month

---

## 🧪 Test It Works

### Valid Questions (Should Answer)
```
"What are the admission requirements for MSU Texas?"
"Tell me about housing options"
"How do I apply for financial aid?"
```

### Invalid Questions (Should Reject)
```
"What's the weather today?"
```
Expected: "Sorry, I can only answer questions about MSU Texas..."

---

## 🔄 Switch Between OpenAI and Gemini

Just change `.env`:

**Use Gemini:**
```bash
USE_GEMINI=true
GOOGLE_API_KEY=AIza...
```

**Use OpenAI:**
```bash
USE_GEMINI=false
OPENAI_API_KEY=sk-...
```

No code changes needed! The app automatically uses the right API.

---

## 🆘 Troubleshooting

### "google.generativeai not found"
**Fix:** `pip install google-generativeai langchain-google-genai`

### "API key not valid"
**Fix:** Check your key at https://aistudio.google.com/app/apikey
- Should start with `AIza`
- Make sure it's enabled

### "Rate limit exceeded"
**Fix:** Free tier limits:
- 15 requests/min for gemini-1.5-flash
- Upgrade at: https://console.cloud.google.com/billing

### Embeddings already exist with OpenAI
**Fix:** Rebuild with Gemini embeddings:
```bash
rm -rf vectorstore/faiss_index/
python ingest.py
```

---

## ✅ Why Gemini is Perfect for MustangsAI

1. **FREE embeddings** (up to 1500/day)
2. **FREE chat** (up to 15 requests/min with flash)
3. **95% cheaper** than OpenAI after free tier
4. **Fast responses** (comparable to gpt-4o-mini)
5. **Good quality** (competitive with GPT-4o-mini)
6. **Easy to get** (no credit card for free tier)

**Your $248 budget goes from 165k queries → 1.2M+ queries!**

---

## 📞 Resources

- **Get API Key:** https://aistudio.google.com/app/apikey
- **Pricing:** https://ai.google.dev/pricing
- **Documentation:** https://ai.google.dev/docs
- **Models:** https://ai.google.dev/models

---

## 🎊 Summary

**To use Gemini:**
1. Get free API key (30 seconds)
2. Set `USE_GEMINI=true` in `.env`
3. Add `GOOGLE_API_KEY=AIza...`
4. Run `python ingest.py` (rebuild with Gemini embeddings)
5. Run `streamlit run app.py`

**Save 95% on costs while maintaining great quality! 🚀**

**Questions?** Email: saimudragada1@gmail.com

**Built by a Mustang - Sai Mudragada**
