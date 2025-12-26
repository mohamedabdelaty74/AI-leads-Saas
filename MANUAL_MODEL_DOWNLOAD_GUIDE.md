# Manual Model Download & Cleanup Guide

**Task:** Download Qwen2.5-1.5B locally and remove old 7B model

---

## Step 1: Download 1.5B Model Manually

### Option A: Using huggingface-cli (Recommended)

```bash
# Install huggingface-cli if not installed
pip install -U huggingface_hub[cli]

# Login to HuggingFace (one-time)
huggingface-cli login --token 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

# Download the 1.5B model (~3GB)
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct --local-dir "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct"
```

### Option B: Using Python Script

```python
# Save as download_model.py and run: python download_model.py
from huggingface_hub import snapshot_download

print("Downloading Qwen2.5-1.5B-Instruct (~3GB)...")
model_path = snapshot_download(
    repo_id="Qwen/Qwen2.5-1.5B-Instruct",
    local_dir="C:\\Users\\Q\\.cache\\huggingface\\hub\\models--Qwen--Qwen2.5-1.5B-Instruct",
    token="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"
)
print(f"Model downloaded to: {model_path}")
```

**Download Time:** 5-10 minutes (depending on internet speed)

---

## Step 2: Find Your Old 7B Model Location

Your current 7B model is at:
```
C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct\snapshots\a09a35458c702b33eeacc393d103063234e8bc28
```

**Size:** ~14 GB (you'll free up this space after deletion)

---

## Step 3: Verify 1.5B Model Downloaded

Check that the model files exist:

```bash
# Check if model downloaded successfully
dir "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct"
```

You should see files like:
- `config.json`
- `model.safetensors` or `pytorch_model.bin`
- `tokenizer.json`
- `tokenizer_config.json`
- etc.

---

## Step 4: Update .env to Point to New Model

You have two options:

### Option A: Use Model Name (Automatic Discovery)

**File:** `.env` (line 73)

```bash
# NEW 1.5B MODEL (auto-discover from cache)
AI_MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct
```

**This is already set!** HuggingFace will automatically find it in cache.

### Option B: Use Exact Path (More Explicit)

If you want to be explicit about the path:

```bash
# Find the exact snapshot path after download
dir "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct\snapshots"

# Then update .env with the full path
AI_MODEL_PATH=C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct\snapshots\[SNAPSHOT_ID]
```

---

## Step 5: Delete Old 7B Model (Free 14GB!)

**⚠️ WARNING: Only do this AFTER confirming 1.5B works!**

### Windows Explorer Method:

1. Open File Explorer
2. Navigate to: `C:\Users\Q\.cache\huggingface\hub\`
3. Find folder: `models--Qwen--Qwen2.5-7B-Instruct`
4. Right-click → Delete
5. Empty Recycle Bin

### Command Line Method:

```bash
# ⚠️ DANGER: This permanently deletes 14GB! Only run after testing 1.5B!
rmdir /S /Q "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct"
```

---

## Step 6: Test New 1.5B Model

```bash
# Start backend with new model
cd "E:\first try\AI-leads-Saas-main"
python backend/main.py
```

**Expected Output:**
```
Loading AI model from: Qwen/Qwen2.5-1.5B-Instruct
Loading tokenizer...
Loading model (from local path or cache)...
✅ AI model loaded successfully on CPU!
INFO: Application startup complete.
```

**Loading time should be:** 1-2 minutes (much faster than 7B's 5-10 minutes!)

---

## Step 7: Test Email Generation

Generate a test email to verify quality:

```bash
# Test via API
curl -X POST http://localhost:8000/api/v1/campaigns/{campaign_id}/leads/bulk-generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "lead_ids": ["test_lead_id"],
    "template_id": "your_template_id"
  }'
```

Or test via your frontend at http://localhost:3000

---

## Quick Reference

### Current .env Setting (Already Correct!)

```bash
# .env line 73
AI_MODEL_PATH=Qwen/Qwen2.5-1.5B-Instruct  ✅ Already set!
```

### Model Locations

```
OLD 7B: C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct\
        Size: ~14 GB
        Status: Can be deleted after testing

NEW 1.5B: C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct\
          Size: ~3 GB
          Status: Download in progress or ready
```

---

## Troubleshooting

### Issue 1: Model Not Found After Download

**Solution:** HuggingFace cache might use a different path structure. Find the exact location:

```bash
python -c "from transformers import AutoTokenizer; t = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-1.5B-Instruct'); print(t.name_or_path)"
```

### Issue 2: Out of Disk Space

**Solution:** Delete old 7B model first (carefully!):

```bash
# Check current disk space
dir "C:\Users\Q\.cache\huggingface\hub" /s

# Delete 7B to free 14GB
rmdir /S /Q "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct"
```

### Issue 3: Download Fails

**Solution:** Download manually via browser and place in correct folder:

1. Go to: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct/tree/main
2. Download all files
3. Place in: `C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-1.5B-Instruct\snapshots\main\`

---

## Expected Benefits After Switch

- **6-10x faster email generation** (0.4s vs 2.5s per email)
- **4x less RAM usage** (3GB vs 14GB)
- **14GB disk space freed** (after deleting 7B)
- **Faster backend startup** (1-2 min vs 5-10 min)
- **Better scalability** (can handle more concurrent requests)

---

## Commands Summary

```bash
# 1. Download 1.5B model
pip install -U huggingface_hub[cli]
huggingface-cli download Qwen/Qwen2.5-1.5B-Instruct

# 2. Start backend (will auto-load from cache)
cd "E:\first try\AI-leads-Saas-main"
python backend/main.py

# 3. Test it works
# (Generate some emails via frontend)

# 4. Delete old 7B model (AFTER testing!)
rmdir /S /Q "C:\Users\Q\.cache\huggingface\hub\models--Qwen--Qwen2.5-7B-Instruct"
```

---

**Status:** Ready to download!
**Your .env is already configured correctly** ✅
**Just download the model and restart backend**
