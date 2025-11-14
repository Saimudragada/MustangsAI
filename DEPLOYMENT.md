# 🚀 MustangsAI Deployment Guide

Complete guide to deploying MustangsAI from scratch.

---

## 📋 Prerequisites

- Python 3.9+
- OpenAI API key (or Anthropic Claude API key)
- Git

---

## 🏗️ Setup Instructions

### 1. Clone & Install

```bash
# Clone the repository
git clone https://github.com/Saimudragada/MustangsAI.git
cd MustangsAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=sk-...
```

**Important:** Get your OpenAI API key from https://platform.openai.com/api-keys

### 3. Scrape Data (100+ MSU Texas Pages)

```bash
# Run the scraper
python scraper.py
```

**What this does:**
- Scrapes 215+ URLs from `data/seed_urls.txt` and `data/additional_sources.txt`
- Saves clean text to `data/raw/`
- Takes ~10-15 minutes with polite crawl delay
- Creates metadata file for tracking

**Output:**
```
data/raw/
├── 000_msutexas.edu_housing.txt
├── 001_msutexas.edu_admissions.txt
├── ...
└── scrape_metadata.json
```

### 4. Build Vector Database

```bash
# Ingest scraped data into FAISS
python ingest.py
```

**What this does:**
- Loads all documents from `data/raw/` and seed URLs
- Chunks text into 1200-character passages
- Generates embeddings using OpenAI text-embedding-3-small
- Saves FAISS index to `vectorstore/faiss_index/`

**Cost estimate:** ~$0.50 for 215 pages (at $0.02/1M tokens)

### 5. Run Locally

```bash
# Start Streamlit app
streamlit run app.py
```

**Access at:** http://localhost:8501

---

## ☁️ Cloud Deployment

### Option 1: Streamlit Cloud (FREE)

1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect your repo: `Saimudragada/MustangsAI`
4. Set secrets in Streamlit Cloud dashboard:
   ```
   OPENAI_API_KEY = "sk-..."
   OPENAI_EMBED_MODEL = "text-embedding-3-small"
   OPENAI_CHAT_MODEL = "gpt-4o-mini"
   ```
5. Deploy!

**Limitations:**
- 1GB RAM limit (may need to optimize embeddings)
- Public URL (no custom domain on free tier)

### Option 2: Railway (Recommended)

1. Create account at https://railway.app
2. New Project → Deploy from GitHub
3. Select `MustangsAI` repo
4. Add environment variables:
   ```
   OPENAI_API_KEY=sk-...
   OPENAI_EMBED_MODEL=text-embedding-3-small
   OPENAI_CHAT_MODEL=gpt-4o-mini
   ```
5. Railway auto-detects Dockerfile and deploys

**Cost:** ~$5/month for hobby plan

**Railway configuration (railway.toml already included):**
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "streamlit run app.py --server.port $PORT --server.address 0.0.0.0"
restartPolicyType = "ON_FAILURE"
```

### Option 3: Azure Web Apps

See `Dockerfile` and `startup.sh` - ready for Azure deployment.

```bash
# Azure CLI deployment
az webapp up --name mustangsai --sku B1
```

### Option 4: Render

1. Create account at https://render.com
2. New Web Service → Connect GitHub repo
3. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
4. Add environment variables
5. Deploy

---

## 💰 Cost Optimization

### Embedding Model
- **Current:** `text-embedding-3-small` ($0.02/1M tokens)
- **Alternative:** `text-embedding-ada-002` ($0.10/1M tokens) - 5x more expensive

### Chat Model
- **Current:** `gpt-4o-mini` ($0.15/1M input, $0.60/1M output)
- **Budget alternative:** `gpt-3.5-turbo` ($0.50/1M, $1.50/1M)
- **Higher quality:** `gpt-4o` ($2.50/1M, $10/1M)

### Expected Costs (per 1000 queries)
```
Query cost breakdown:
- Retrieval: 6 docs × 1200 chars × 1000 queries = 7.2M chars
- Embedding: ~1.5M tokens
- Generation: ~500k input + 200k output tokens

Total: ~$1.50 per 1000 queries with gpt-4o-mini
```

**$248 budget = ~165,000 queries** (way more than needed!)

---

## 🧪 Testing

### Test Non-MSU Question Rejection

```python
# Should reject
"What's the weather today?"
"Who won the Super Bowl?"
"How do I bake a cake?"

# Should answer
"What are MSU Texas admission requirements?"
"Tell me about housing at MSU"
"What financial aid is available?"
```

### Test Source Citations

Every response should include:
- Expandable "📚 View Sources" section
- Links to original msutexas.edu pages
- Preview of relevant text

### Test UI Elements

✅ Maroon (#660000) buttons with gold (#FFD700) accents
✅ Welcome screen with mascot (120px, gold border)
✅ Quick topic buttons
✅ Sidebar with emoji icons (📚📖📅📝💰🏛️)
✅ Footer: "Built by a Mustang - Sai Mudragada"
✅ Disclaimer above chat input

---

## 📊 Monitoring

### Usage Tracking

The app includes rate limiting in `rate_limiter.py`:
- Tracks daily query count
- Prevents abuse
- Shows usage stats in UI

### Feedback System

Users can rate responses with 👍/👎:
- Stored in `feedback.py`
- Track satisfaction metrics
- Identify areas for improvement

---

## 🐛 Troubleshooting

### "Vector store not found" error
```bash
# Make sure you ran the scraper and ingestion
python scraper.py
python ingest.py
```

### "OpenAI API key not found"
```bash
# Check .env file exists and has correct key
cat .env
# Make sure it's loaded
source .env  # or restart app
```

### Slow responses (>5 seconds)
- Check embedding model (use text-embedding-3-small)
- Reduce retrieval documents (k=6 → k=4)
- Use gpt-4o-mini instead of gpt-4o
- Check network latency

### Memory errors on Streamlit Cloud
- Reduce chunk size in ingest.py (1200 → 800)
- Use smaller embedding model
- Consider switching to Pinecone (cloud vector DB)

---

## 📦 Project Structure

```
mustangsai/
├── app.py                 # Main Streamlit app
├── scraper.py            # Web scraper for msutexas.edu
├── ingest.py             # Vector DB ingestion pipeline
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── Dockerfile            # Container config
├── railway.toml          # Railway deployment config
├── startup.sh            # Azure startup script
│
├── assets/
│   └── Mustangs_mascot.png
│
├── data/
│   ├── seed_urls.txt         # Primary URL list (215+ URLs)
│   ├── additional_sources.txt
│   └── raw/                  # Scraped content
│
├── vectorstore/
│   └── faiss_index/          # FAISS vector database
│
└── core/                 # Utility modules
    ├── ingest.py
    ├── chunk.py
    └── indexer.py
```

---

## 🎯 Success Criteria Checklist

✅ UI matches specifications exactly
- Maroon #660000 / Gold #FFD700
- Welcome screen with mascot
- Topic buttons with hover effects
- Footer: "Built by Sai Mudragada"

✅ 100+ MSU pages scraped (215 URLs)

✅ Sub-5 second responses
- Optimized with gpt-4o-mini
- FAISS for fast vector search

✅ Accurate answers with citations
- Source URLs displayed
- Top 6 relevant documents

✅ Polite rejection of non-MSU questions
- Keyword-based filtering
- Custom rejection message

✅ Under $248 budget
- ~$1.50 per 1000 queries
- Budget supports 165k+ queries

✅ Deployable
- Railway, Streamlit Cloud, Azure, Render
- Dockerfile and configs included

---

## 🤝 Support

**Questions?** Contact saimudragada1@gmail.com

**Report bugs:** GitHub Issues

**Live demo:** https://mustangsai-production.up.railway.app/
