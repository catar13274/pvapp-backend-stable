# Troubleshooting Invoice Upload Feature

## 🔧 QUICK FIX: Database Schema Error (Most Common)

### Symptom
When uploading an invoice, you see:
```
Error: Error processing file: (sqlite3.OperationalError) table invoice has no column named file_path
```

### Quick Fix
```bash
cd /opt/pvapp
./fix_database.sh
sudo systemctl restart pvapp
```

**What it does:** Adds missing columns to your database for the invoice upload feature.

### Alternative Methods

**Method 1: Use the fix script (Recommended)**
```bash
cd /opt/pvapp
./fix_database.sh
```

**Method 2: Run migration manually**
```bash
cd /opt/pvapp
source .venv/bin/activate
python scripts/migrate_db.py
```

**Method 3: Reinitialize database**
```bash
cd /opt/pvapp
source .venv/bin/activate
python scripts/init_db.py
```

**Method 4: Use the update script**
```bash
cd /opt/pvapp
./update.sh
# Now includes automatic migration
```

### Why This Happens
- You have an existing database from before the invoice upload feature
- The new feature requires additional database columns
- These columns need to be added via migration

### After Fix
After running the fix, restart your application:
- **Systemd**: `sudo systemctl restart pvapp`
- **Manual**: Stop (Ctrl+C) and restart uvicorn

---

## 405 Method Not Allowed Error

### Symptom
When trying to upload an invoice file, you see:
```
Failed to load resource: the server responded with a status of 405 (Method Not Allowed)
```

### Cause
The invoice upload endpoint was added after the server was started. The server needs to be restarted to register the new endpoints.

### Solution

#### For Development (uvicorn)
```bash
# Stop the current server (Ctrl+C)
# Then restart:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### For Production (systemd service)
```bash
sudo systemctl restart pvapp
```

#### For Manual Production
```bash
# Find the process
ps aux | grep uvicorn

# Kill it
sudo kill <process_id>

# Or use pkill
sudo pkill -f "uvicorn app.main"

# Restart
cd /opt/pvapp
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Verification

After restarting, check if the endpoint is available:
```bash
curl -X POST http://localhost:8000/api/invoices/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.txt"
```

You should see either:
- Success response (if authenticated and file is valid)
- 401 Unauthorized (if token is missing/invalid) - this means endpoint exists
- 400 Bad Request (if file type is invalid) - this means endpoint exists

You should NOT see:
- 405 Method Not Allowed - this means endpoint is not registered

## Missing Dependencies Error

### Symptom
Server won't start or crashes when uploading files.

### Cause
Required parsing libraries are not installed.

### Solution
```bash
cd /opt/pvapp
source .venv/bin/activate
pip install -r requirements.txt
```

Required dependencies:
- PyPDF2 (PDF parsing)
- python-docx (DOC/DOCX parsing)
- lxml (XML parsing)
- aiofiles (async file operations)

## Upload Directory Permission Error

### Symptom
```
Error saving file: Permission denied
```

### Cause
The upload directory `/opt/pvapp/data/invoices` doesn't exist or has wrong permissions.

### Solution
```bash
sudo mkdir -p /opt/pvapp/data/invoices
sudo chown -R $USER:$USER /opt/pvapp/data
# Or if running as specific user:
sudo chown -R pvapp:pvapp /opt/pvapp/data
```

## File Upload Size Limit

### Symptom
Large files fail to upload or connection times out.

### Cause
Nginx or server has a file size limit.

### Solution

For Nginx:
```nginx
# In /etc/nginx/sites-available/pvapp
client_max_body_size 20M;
```

For FastAPI (in main.py):
```python
from fastapi import FastAPI
app = FastAPI()
# No explicit limit in FastAPI, but consider implementing one
```

Then restart Nginx:
```bash
sudo systemctl restart nginx
```

## Parsing Errors

### Symptom
File uploads but shows parsing error.

### Common Causes and Solutions

**Scanned PDF (image-based)**
- Cause: PDF contains only images, no text
- Solution: Use OCR software first or wait for OCR feature
- Workaround: Convert to text format manually

**Corrupted File**
- Cause: File is damaged
- Solution: Try re-saving or converting the file

**Unsupported Format**
- Cause: File extension doesn't match content
- Solution: Verify file is actually PDF/DOC/TXT/XML

**Special Characters**
- Cause: File contains unusual encoding
- Solution: Re-save with UTF-8 encoding

## Cannot See Upload Button

### Symptom
No "Upload Invoice" button in the Invoices section.

### Cause
Frontend files weren't updated or browser cache.

### Solution
1. Hard refresh browser: `Ctrl+F5` (Windows/Linux) or `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Verify frontend files are up to date:
```bash
ls -la /opt/pvapp/frontend/
# Should see recent dates on app.js, index.html
```

## Validation Screen Issues

### Symptom
After upload, validation screen doesn't show or is empty.

### Cause
JavaScript error or API response issue.

### Solution
1. Open browser console (F12)
2. Look for JavaScript errors
3. Check network tab for failed requests
4. Verify invoice was created:
```bash
# Check database
sqlite3 /opt/pvapp/data/pvapp.db "SELECT * FROM invoice ORDER BY id DESC LIMIT 1;"
```

## Quick Diagnostic Commands

```bash
# Check if service is running
systemctl status pvapp

# Check recent logs
journalctl -u pvapp -n 50

# Check if port is open
netstat -tlnp | grep 8000

# Test endpoint directly
curl -X POST http://localhost:8000/api/invoices/upload \
  -H "Authorization: Bearer $(cat /tmp/test_token)" \
  -F "file=@/opt/pvapp/examples/sample_invoice_ro.txt"

# Check uploaded files
ls -lh /opt/pvapp/data/invoices/
```

## Common Solutions Summary

| Problem | Quick Fix |
|---------|-----------|
| 405 Error | Restart server |
| Permission Denied | Fix directory permissions |
| Dependencies Missing | `pip install -r requirements.txt` |
| Large File Fails | Increase nginx `client_max_body_size` |
| No Upload Button | Clear browser cache |
| Parsing Fails | Check file format and encoding |

## Still Having Issues?

1. Check server logs:
   ```bash
   journalctl -u pvapp -f
   ```

2. Test with example files:
   ```bash
   cd /opt/pvapp/examples
   # Try uploading sample_invoice_ro.txt through the UI
   ```

3. Verify all services are running:
   ```bash
   systemctl status pvapp
   systemctl status nginx  # if using nginx
   ```

4. Check file permissions:
   ```bash
   ls -la /opt/pvapp/data/
   ls -la /opt/pvapp/frontend/
   ```

If issues persist, check the main troubleshooting guide: `TROUBLESHOOTING_RPI.md`
