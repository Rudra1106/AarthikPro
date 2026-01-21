# 📚 AarthikAI - Complete System Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Phase 1: PDF Download](#phase-1-pdf-download)
3. [Phase 2: PDF Extraction](#phase-2-pdf-extraction)
4. [Phase 3: Query System](#phase-3-query-system)
5. [Phase 4: Monitoring](#phase-4-monitoring)
6. [Troubleshooting](#troubleshooting)

---

## System Overview

**Architecture**:
```
MongoDB (Source) → Download PDFs → Extract Data → Store (MongoDB + Pinecone) → Query System
```

**Data Flow**:
- **MongoDB**: All data (hot + warm + cold)
- **Pinecone**: Hot data only (FY2025, FY2024, FY2023)
- **Temperature**: Hot (3 years), Warm (3-5 years), Cold (5+ years)

---

## Phase 1: PDF Download

### 📥 **Download Annual Reports**

#### **1.1 Download First Chunk (100 stocks)**
```bash
cd /Users/rudra/Documents/AarthikAi
python scripts/download_pdfs.py --annual-only
```

**What it does**:
- Downloads annual reports for 100 stocks
- Saves to `data/annual_reports/[ISIN]/[year].pdf`
- Creates progress tracking in `data/download_state.json`
- Logs errors to `data/download_errors.log`

**Expected output**:
```
Chunk 0: 100%|████████████████████| 100/100 [1:46:08<00:00]
📊 Total PDFs Processed: 628
✅ Successfully Downloaded: 590
Success Rate: 93.9%
```

#### **1.2 Download Next Chunk**
```bash
python scripts/download_pdfs.py --annual-only
```
Automatically processes next chunk (chunk 1, stocks 101-200)

#### **1.3 Download Specific Chunk**
```bash
python scripts/download_pdfs.py --annual-only --chunk-number 5
```

#### **1.4 Reset Download Progress**
```bash
python scripts/download_pdfs.py --reset
```

---

## Phase 2: PDF Extraction

### 🔍 **Extract Data from PDFs**

#### **2.1 Test Extraction (1 PDF)**
```bash
python scripts/extract_pdfs.py --test
```

**What it does**:
- Tests extraction on 1 stock
- Validates all components working
- Shows cost estimates

#### **2.2 Extract Small Batch (10 stocks)**
```bash
python scripts/extract_pdfs.py --chunk-number 0 --chunk-size 10
```

**What it does**:
- Extracts 10 stocks from chunk 0
- Good for testing before full run

#### **2.3 Extract Full Chunk (100 stocks)**
```bash
python scripts/extract_pdfs.py --chunk-number 0
```

**What it does**:
- Processes all PDFs in chunk 0
- For each PDF:
  - ✅ Extract narrative text
  - ✅ Classify temperature (hot/warm/cold)
  - ✅ **If HOT**: Detect verticals + Extract tables
  - ✅ **If WARM/COLD**: Skip verticals/tables
  - ✅ Store in MongoDB
  - ✅ **If HOT**: Generate embeddings + Upload to Pinecone

**Expected output**:
```
📄 Processing: INE467B01029 FY2024
  Extracting narrative...
  🔥 Hot data - Detecting verticals...
  🔥 Hot data - Extracting tables...
  Storing in MongoDB...
  🔥 Generating embeddings...
  📌 Uploading to Pinecone...

📄 Processing: INE467B01029 FY2020
  Extracting narrative...
  ❄️  Cold data - Skipping vertical/table extraction
  Storing in MongoDB...
```

#### **2.4 Extract Next Chunk**
```bash
python scripts/extract_pdfs.py --chunk-number 1
```

---

### 🔄 **Complete Workflow (Download → Extract → Repeat)**

```bash
# Chunk 0
python scripts/download_pdfs.py --annual-only
python scripts/extract_pdfs.py --chunk-number 0

# Chunk 1
python scripts/download_pdfs.py --annual-only
python scripts/extract_pdfs.py --chunk-number 1

# Chunk 2
python scripts/download_pdfs.py --annual-only
python scripts/extract_pdfs.py --chunk-number 2

# ... repeat for all 57 chunks
```

---

## Phase 3: Query System

### 🔍 **Query Extracted Data**

#### **3.1 Query MongoDB (All Data)**

**Connect to MongoDB**:
```bash
mongosh "mongodb+srv://aarthikaibot:xjJ0Dh1wMmCNr5p6@aarthik.m9cjl1m.mongodb.net/PORTFOLIO_MANAGER"
```

**Query Examples**:
```javascript
// Count extracted documents
db.extraction_documents.countDocuments()

// Find hot data
db.extraction_documents.find({ temperature: "hot" })

// Find specific company
db.text_chunks.find({ isin: "INE467B01029" })

// Find vertical chunks
db.text_chunks.find({ chunk_type: "vertical" })

// Find tables
db.table_chunks.find({ fiscal_year: 2024 })

// Count by temperature
db.extraction_documents.aggregate([
  { $group: { _id: "$temperature", count: { $sum: 1 } } }
])
```

#### **3.2 Query Pinecone (Hot Data)**

**Python Example**:
```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-key")
index = pc.Index("finance-general-v1")

# Get stats
stats = index.describe_index_stats()
print(f"Total vectors: {stats.total_vector_count}")

# Query
results = index.query(
    vector=[...],  # Your query embedding
    top_k=5,
    include_metadata=True,
    filter={"isin": "INE467B01029", "fiscal_year": 2024}
)
```

#### **3.3 Intent Classification (Future)**

**Using BAAI/bge-large-en-v1.5**:
```python
# To be implemented
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('BAAI/bge-large-en-v1.5')
query = "What is TCS revenue growth?"
intent = classify_intent(query, model)
# Route to appropriate index based on intent
```

---

## Phase 4: Monitoring

### 📊 **Check System Status**

#### **4.1 Test Components**
```bash
python scripts/test_basic.py
```

**Checks**:
- ✅ LLM client
- ✅ MongoDB connection
- ✅ Pinecone connection
- ✅ Extractors
- ✅ Temperature classification
- ✅ PDF count

#### **4.2 Check Download Progress**
```bash
cat data/download_state.json
```

#### **4.3 Check Extraction Logs**
```bash
# MongoDB
db.extraction_logs.find().sort({ timestamp: -1 }).limit(10)
```

#### **4.4 Check Pinecone Stats**
```python
from pinecone import Pinecone

pc = Pinecone(api_key="your-key")

for index_name in ["finance-general-v1", "finance-vertical-v1", "finance-table-v1"]:
    index = pc.Index(index_name)
    stats = index.describe_index_stats()
    print(f"{index_name}: {stats.total_vector_count} vectors")
```

#### **4.5 Check Costs**
After extraction, check the summary:
```
OpenAI Embedding Cost:
  Total Tokens: 424,045
  Total Cost: $0.0085

LLM Cost Summary:
  Total Calls: 12
  Total Cost: $0.0024
```

---

## Troubleshooting

### 🔧 **Common Issues**

#### **Issue 1: Pinecone Dimension Mismatch**
```bash
# Reset Pinecone indexes
python scripts/reset_pinecone.py

# Restart extraction
python scripts/extract_pdfs.py --chunk-number 0
```

#### **Issue 2: MongoDB Connection Error**
```bash
# Check .env file
cat .env | grep MONGODB_URI

# Test connection
python scripts/test_basic.py
```

#### **Issue 3: LLM API Error**
```bash
# Check OpenRouter API key
cat .env | grep OPENROUTER_API_KEY

# Model should be: openai/gpt-4o-mini
```

#### **Issue 4: Download 403 Errors**
- Already fixed with browser headers
- Check `data/download_errors.log` for details

#### **Issue 5: Extraction Too Slow**
- Already optimized (skips warm/cold vertical/table extraction)
- Expected: ~20-40 minutes per 100 stocks

---

## Quick Reference

### **File Locations**

```
data/
├── annual_reports/          # Downloaded PDFs
│   └── [ISIN]/
│       └── [year].pdf
├── llm_cache/               # LLM response cache
├── download_state.json      # Download progress
└── download_errors.log      # Download errors

MongoDB Collections:
├── extraction_documents     # PDF metadata
├── text_chunks              # Narrative + vertical text
├── table_chunks             # Extracted tables
└── extraction_logs          # Processing logs

Pinecone Indexes:
├── finance-general-v1       # Narrative embeddings (1536-dim)
├── finance-vertical-v1      # Vertical embeddings (1536-dim)
└── finance-table-v1         # Table embeddings (1536-dim)
```

### **Key Scripts**

```bash
# Download
python scripts/download_pdfs.py --annual-only

# Extract
python scripts/extract_pdfs.py --chunk-number 0

# Test
python scripts/test_basic.py

# Reset Pinecone
python scripts/reset_pinecone.py
```

### **Environment Variables**

```bash
OPENAI_API_KEY=...           # For embeddings
OPENROUTER_API_KEY=...       # For LLM enhancement
PINECONE_API_KEY=...         # For vector storage
MONGODB_URI=...              # For data storage
```

---

## Progress Tracking

### **Current Status** (Update as you go)

- [x] Phase 1: Download infrastructure ✅
- [x] Phase 2: Extraction pipeline ✅
- [ ] Chunk 0: Download + Extract
- [ ] Chunk 1: Download + Extract
- [ ] ... (57 chunks total)
- [ ] Phase 3: Intent classifier
- [ ] Phase 4: Query system

### **Estimated Timeline**

- **Per Chunk**: ~2 hours (download + extract)
- **Total**: ~114 hours (~5 days continuous)
- **Recommended**: Process 5-10 chunks per day

---

## Cost Summary

### **Per 100 Stocks (1 Chunk)**
- OpenAI Embeddings: ~$0.20
- LLM Enhancement: ~$1.68
- **Total**: ~$1.88

### **Full 5,700 Stocks (57 Chunks)**
- OpenAI Embeddings: ~$11.40
- LLM Enhancement: ~$96
- **Total One-Time**: ~$107.40
- **Monthly (Pinecone + MongoDB)**: ~$95

---

## Support

**Documentation**:
- `EXTRACTION_COMPLETE.md` - Full extraction guide
- `EXTRACTION_QUICKSTART.md` - Quick start guide
- `UPDATED_COST_STRATEGY.md` - Cost analysis
- `EXTRACTION_OPTIMIZATION.md` - Performance tips
- `TEMPERATURE_UPDATE.md` - Hot/warm/cold classification

**Need Help?**
- Check MongoDB: `db.extraction_logs.find({ status: "failed" })`
- Check errors: `cat data/download_errors.log`
- Test components: `python scripts/test_basic.py`

- for dhan csv : curl -s "https://images.dhan.co/api-data/api-scrip-master-detailed.csv" | head -2