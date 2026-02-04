# 🔧 URGENT FIX: Database Schema Error

## Error You're Seeing
```
Error: Error processing file: (sqlite3.OperationalError) 
table invoice has no column named file_path
```

## Quick Fix (30 seconds)

### Option 1: Use the Fix Script (Easiest)
```bash
cd /opt/pvapp
./fix_database.sh
sudo systemctl restart pvapp
```

### Option 2: Run Migration Manually
```bash
cd /opt/pvapp
source .venv/bin/activate
python scripts/migrate_db.py
sudo systemctl restart pvapp
```

### Option 3: Update Everything
```bash
sudo /opt/pvapp/update.sh
# This updates code AND runs migration
```

## What This Does
- Adds 3 missing columns to your database:
  - `file_path` - stores uploaded file location
  - `file_type` - stores file format (PDF, DOC, etc.)
  - `raw_text` - stores extracted text content
- Safe to run multiple times
- Doesn't delete any existing data

## Verification
After running the fix, try uploading an invoice again. It should work!

## Why This Happened
You have an existing database from before the invoice upload feature was added. The new feature requires additional database columns that need to be added through migration.

## Future Prevention
Use the `update.sh` script for future updates - it automatically runs migrations:
```bash
sudo /opt/pvapp/update.sh
```

## Need More Help?
See [TROUBLESHOOTING_UPLOAD.md](TROUBLESHOOTING_UPLOAD.md) for detailed troubleshooting.
