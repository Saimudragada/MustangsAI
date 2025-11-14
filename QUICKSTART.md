# ⚡ MustangsAI Quick Start Guide

Get MustangsAI running in **5 minutes**.

---

## 🎯 Prerequisites

- Python 3.9+
- OpenAI API key → Get it at https://platform.openai.com/api-keys

---

## 🚀 Setup (5 Minutes)

### Step 1: Install Dependencies (1 min)

```bash
# Clone repo
git clone https://github.com/Saimudragada/MustangsAI.git
cd MustangsAI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure API Key (30 sec)

```bash
# Copy template
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### Step 3: Scrape MSU Data (10-15 min)

```bash
python scraper.py
```

This will scrape 215+ pages from msutexas.edu.

**⏱️ Time:** ~10-15 minutes (polite crawl delay)
**💾 Output:** `data/raw/*.txt`

### Step 4: Build Vector Database (2 min)

```bash
python ingest.py
```

**💰 Cost:** ~$0.50 (embeddings for 215 pages)
**💾 Output:** `vectorstore/faiss_index/`

### Step 5: Run App (10 sec)

```bash
streamlit run app.py
```

**🌐 Access:** http://localhost:8501

---

## ✅ Verify It Works

### Test Valid Questions

```
✅ "What are the admission requirements for MSU Texas?"
✅ "Tell me about housing options"
✅ "How do I apply for financial aid?"
```

**Expected:** Detailed answer with source citations

### Test Invalid Questions

```
❌ "What's the weather today?"
❌ "Who won the Super Bowl?"
```

**Expected:** "Sorry, I can only answer questions about MSU Texas..."

---

## 🎨 UI Checklist

Verify these elements:

- ✅ Maroon (#660000) and Gold (#FFD700) colors
- ✅ Mascot image (120px, gold border)
- ✅ Topic buttons (Admissions, Financial Aid, etc.)
- ✅ Sources expandable with 📚 icon
- ✅ Footer: "Built by a Mustang - Sai Mudragada"
- ✅ Disclaimer above chat input

---

## 💰 Cost Breakdown

### Initial Setup
- Embeddings (one-time): ~$0.50
- Total setup cost: **$0.50**

### Per Query (gpt-4o-mini)
- ~$0.0015 per query
- **$248 budget = 165,000 queries**

---

## 🐛 Common Issues

### "Vector store not found"
**Fix:** Run `python ingest.py`

### "OpenAI API key not found"
**Fix:** Check `.env` file has `OPENAI_API_KEY=sk-...`

### Slow responses
**Fix:** Already optimized! Using gpt-4o-mini + FAISS

---

## 📚 Next Steps

- **Deploy to cloud:** See `DEPLOYMENT.md`
- **Customize UI:** Edit `app.py` CSS section
- **Add more sources:** Edit `data/seed_urls.txt`
- **Track usage:** Check `rate_limiter.py` and `feedback.py`

---

## 🆘 Need Help?

- **Email:** saimudragada1@gmail.com
- **GitHub:** https://github.com/Saimudragada/MustangsAI
- **Live Demo:** https://mustangsai-production.up.railway.app/

---

**Built by a Mustang - Sai Mudragada**
