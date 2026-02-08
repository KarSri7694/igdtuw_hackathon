# TRACE Quick Start Guide

## 🚀 Quick Setup (5 minutes)

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up llama.cpp Server

1. **Download llama.cpp**:
   - Windows: https://github.com/ggerganov/llama.cpp/releases
   - Linux/Mac: Build from source or use package manager

2. **Download Qwen 3 4B Model** (GGUF format):
   ```bash
   # Example: Download from Hugging Face
   # Model: Qwen/Qwen3-4B-Instruct-GGUF (Q4_K_M variant recommended)
   ```

3. **Start the llama.cpp server**:
   ```bash
   # Windows (PowerShell)
   .\llama-server.exe -m path\to\Qwen3-4B-Instruct-2507-Q4_K_M.gguf --port 8080

   # Linux/Mac
   ./llama-server -m path/to/Qwen3-4B-Instruct-2507-Q4_K_M.gguf --port 8080
   ```

   **Important**: Keep this terminal open while using TRACE!

### Step 3: Launch TRACE

```bash
python ui.py
```

---

## 📝 First Scan Tutorial

1. **Click "Browse"** → Select a folder with images/documents (e.g., Downloads, Pictures)

2. **Configure scan options**:
   - ✅ **Recursive Scan**: Check if you want to scan subfolders
   - ✅ **Enable OCR**: Must be enabled for image analysis
   - ✅ **Enable Encoding**: Recommended for semantic search later

3. **Click "Start Privacy Scan"**

4. **Wait for results**:
   - First scan will download GLM-OCR model (~2GB)
   - Progress bar shows current status
   - Typical speed: 5-10 images/minute (depends on GPU)

5. **Review sensitive files**:
   - Popup automatically shows Critical/High/Medium risk files
   - Read recommendations carefully
   - Use action buttons:
     - 🗑️ **Delete**: Remove file permanently (with confirmation)
     - 📂 **Open Location**: Navigate to file folder
     - 🔐 **Vault**: (Coming soon) Encrypt and secure

---

## 🔧 Troubleshooting

### Issue: "LLM server is not responding"

**Solution**: 
- Ensure llama.cpp server is running on `http://localhost:8080`
- Test with: `curl http://localhost:8080/health`
- Check firewall settings

### Issue: GLM-OCR download fails

**Solution**:
- Check internet connection
- Manually download from: https://huggingface.co/zai-org/GLM-OCR
- Place in: `model_folder/models--zai-org--GLM-OCR/`

### Issue: Out of memory during scan

**Solution**:
- Reduce batch size by scanning smaller folders
- Close other applications
- Disable encoding temporarily (`Enable Encoding = OFF`)
- Use GPU if available

### Issue: Popup window doesn't show

**Solution**:
- Check console for errors
- Ensure sensitive files were detected (Critical/High/Medium risk)
- Try "Find Sensitive Docs" button for manual analysis

---

## 💡 Usage Tips

### Best Practices

1. **Start Small**: Test on a small folder first (10-20 files)
2. **Use Encoding**: Enable for better semantic search capabilities
3. **Review Regularly**: Scan Downloads/Pictures folders weekly
4. **Take Action**: Don't just scan - delete or secure sensitive files
5. **Backup First**: Before bulk deletions, ensure you have backups

### Performance Optimization

- **GPU Usage**: Significantly faster for OCR and LLM
- **Batch Scanning**: Process multiple folders in sequence
- **Disable OCR**: For text-only scans (`.txt`, `.md` files)
- **Recursive Scan**: Be careful with large directory trees

### Privacy Controls

- **Local Only**: All data stays on your machine
- **No Internet**: Works offline (after model downloads)
- **Sensitive Data**: Never uploaded or shared
- **LLM Privacy**: llama.cpp runs 100% locally

---

## 📊 Understanding Results

### Risk Levels Explained

| Level | Color | Meaning | Examples |
|-------|-------|---------|----------|
| **CRITICAL** | 🔴 Red | Immediate threat | Passwords, SSNs, credit cards |
| **HIGH** | 🟠 Orange | Serious concern | Passports, medical records, bank statements |
| **MEDIUM** | 🟡 Yellow | Moderate risk | Name+address, employee ID, phone+email |
| **LOW** | 🟢 Green | Minor concern | Just first name, generic email |

### Common PII Categories

- **Personal Identifiers**: Names, addresses, contacts
- **Government IDs**: SSN, passport, driver's license
- **Financial**: Credit cards, bank accounts, transactions
- **Credentials**: Passwords, API keys, tokens
- **Medical**: Health records, prescriptions
- **Biometric**: Fingerprints, facial data
- **Confidential**: Business secrets, internal docs

---

## 🔍 Advanced Features

### Semantic Search

After encoding documents, use "Find Sensitive Docs" to:
- Search by meaning (not just keywords)
- Find related concepts across all documents
- Analyze entire document database with LLM

### Manual Encoding

Encode specific directories:
1. Click "Encode Documents"
2. Select folder with `.txt` or `.md` files
3. Wait for semantic chunking and embedding
4. Documents added to vector database

### Batch Analysis

For large datasets:
1. Split into smaller folders
2. Scan each folder separately
3. Review results incrementally
4. Use encoding to build searchable database

---

## 🆘 Support

### Getting Help

1. **Check Logs**: Look for error messages in console
2. **Review Documentation**: Read README.md thoroughly
3. **Test Components**: Verify llama.cpp and GLM-OCR separately
4. **Report Issues**: Include error messages and system info

### System Requirements

- **OS**: Windows 10/11, Linux, macOS
- **Python**: 3.9+ (tested on 3.11.9)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 5GB for models + results
- **GPU**: Optional but recommended (NVIDIA with CUDA)

---

<div align="center">

**Ready to discover your digital footprint?**

Start with: `python ui.py`

</div>
