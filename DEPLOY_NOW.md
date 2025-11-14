# 🚀 DEPLOYMENT INSTRUCTIONS

## Current Status
✅ Code committed and pushed to: `claude/build-mustangsai-rag-01XtZxWvoMGpGt7RzsH14TpZ`
✅ Railway configuration ready (railway.toml)
✅ Dockerfile configured
✅ All dependencies listed in requirements.txt

---

## 🎯 Railway Deployment (RECOMMENDED)

### Step 1: Prepare Data (LOCAL - REQUIRED BEFORE DEPLOY)

**IMPORTANT:** You MUST run these commands locally first to create the vector database:

```bash
# 1. Install dependencies locally
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY=your_key_here  # Linux/Mac
# OR
set OPENAI_API_KEY=your_key_here     # Windows

# 3. Scrape MSU data (10-15 minutes)
python scraper.py

# 4. Build vector database (~2 min, $0.50)
python ingest.py
```

This creates `vectorstore/faiss_index/` which needs to be committed.

### Step 2: Commit Vector Database

```bash
# Add the vector store to git
git add vectorstore/
git add data/raw/
git commit -m "Add vector database and scraped data"
git push -u origin claude/build-mustangsai-rag-01XtZxWvoMGpGt7RzsH14TpZ
```

### Step 3: Deploy to Railway

1. **Go to Railway Dashboard**: https://railway.app/dashboard
2. **Create New Project** (if not already created)
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose: `Saimudragada/MustangsAI`
   - Select branch: `claude/build-mustangsai-rag-01XtZxWvoMGpGt7RzsH14TpZ`

3. **Set Environment Variables** in Railway:
   - Go to project → Variables tab
   - Add these:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   OPENAI_EMBED_MODEL=text-embedding-3-small
   OPENAI_CHAT_MODEL=gpt-4o-mini
   ```

4. **Deploy**
   - Railway will auto-detect `railway.toml` and `Dockerfile`
   - Build takes ~3-5 minutes
   - You'll get a public URL like: `mustangsai.up.railway.app`

---

## 🌐 Alternative: Streamlit Cloud (FREE)

### Prerequisites
- Vector database must be committed to repo (see Step 1-2 above)

### Deployment Steps

1. **Go to**: https://share.streamlit.io
2. **Sign in with GitHub**
3. **New app**:
   - Repository: `Saimudragada/MustangsAI`
   - Branch: `claude/build-mustangsai-rag-01XtZxWvoMGpGt7RzsH14TpZ`
   - Main file path: `app.py`

4. **Advanced Settings → Secrets**:
   ```toml
   OPENAI_API_KEY = "sk-your-actual-key-here"
   OPENAI_EMBED_MODEL = "text-embedding-3-small"
   OPENAI_CHAT_MODEL = "gpt-4o-mini"
   ```

5. **Deploy** - Takes ~2-3 minutes

---

## ⚠️ CRITICAL: Data Requirements

**Your app WILL FAIL if you don't include the vector database!**

The vector database (`vectorstore/faiss_index/`) contains the embeddings for all 215+ MSU Texas pages. Without it, the app cannot retrieve relevant documents.

### Option A: Include in Git (Recommended for small DBs)
```bash
# Remove vectorstore from .gitignore if present
# Then commit it
git add vectorstore/
git commit -m "Add FAISS vector database"
git push
```

### Option B: Build on Deploy (Slower, costs per deployment)
Add to your deployment startup:
```bash
python ingest.py && streamlit run app.py
```

**This runs ingestion on EVERY deploy (~$0.50 each time)**

---

## 🧪 Test Deployment

Once deployed, test with:

✅ **Valid questions:**
- "What are the admission requirements for MSU Texas?"
- "Tell me about housing options"

❌ **Invalid questions:**
- "What's the weather today?"
- Expected response: "Sorry, I can only answer questions about MSU Texas..."

---

## 📊 Deployment Checklist

Before deploying, ensure:

- [ ] OpenAI API key obtained (https://platform.openai.com/api-keys)
- [ ] Scraped data exists in `data/raw/` (run `python scraper.py`)
- [ ] Vector database exists in `vectorstore/faiss_index/` (run `python ingest.py`)
- [ ] Vector database committed to git
- [ ] Environment variables set in deployment platform
- [ ] `requirements.txt` includes all dependencies

---

## 💰 Deployment Costs

| Platform | Cost | Notes |
|----------|------|-------|
| **Streamlit Cloud** | FREE | 1GB RAM limit, may struggle with large vector DB |
| **Railway** | $5/month | Recommended, 512MB-1GB RAM, auto-scaling |
| **Render** | $7/month | 512MB RAM, good performance |
| **Azure** | $13+/month | B1 tier, enterprise features |

**API Costs (same for all platforms):**
- Setup: $0.50 (one-time)
- Per query: ~$0.0015
- $248 budget = 165,000 queries

---

## 🔧 Troubleshooting

### "Vector store not found" error
**Solution:** Run `python ingest.py` locally and commit the vectorstore directory

### "No module named 'langchain'"
**Solution:** Check `requirements.txt` includes all dependencies (already done)

### App crashes with "Out of memory"
**Solutions:**
1. Use smaller embedding model
2. Reduce chunk size in `ingest.py`
3. Upgrade to larger deployment tier
4. Use cloud vector DB (Pinecone, Qdrant)

### Slow responses (>10 seconds)
**Solutions:**
1. Verify using `gpt-4o-mini` (not `gpt-4o`)
2. Check FAISS index is loaded (should be cached)
3. Reduce retrieval docs from 6 to 4

---

## 📞 Need Help?

- **Email:** saimudragada1@gmail.com
- **Docs:** See `DEPLOYMENT.md` for detailed guides
- **Quick Start:** See `QUICKSTART.md`

---

**Ready to deploy! 🚀**
