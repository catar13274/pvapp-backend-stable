# Database Migration Guide

## Overview

This guide explains the database migration system for the PV Management App, specifically for adding invoice file upload columns.

## Background

When new features are added that require database schema changes, existing databases need to be migrated. The invoice file upload feature added three new columns to the `invoice` table and three to the `invoice_item` table.

## Migration System

### Files

**`scripts/migrate_db.py`** - Main migration script
- Can be run standalone or via init_db.py
- Checks for existing columns before adding
- Idempotent (safe to run multiple times)
- Detailed logging

**`scripts/init_db.py`** - Enhanced to call migrations
- Runs after table creation
- Ensures schema is up-to-date

### Schema Changes

#### Invoice Table
```sql
ALTER TABLE invoice ADD COLUMN file_path VARCHAR(500);
ALTER TABLE invoice ADD COLUMN file_type VARCHAR(10);
ALTER TABLE invoice ADD COLUMN raw_text TEXT;
```

**Columns:**
- `file_path` - Full path to uploaded invoice file (nullable)
- `file_type` - File format: PDF, DOC, TXT, XML (nullable)
- `raw_text` - Extracted text content from file (nullable)

#### Invoice Item Table
```sql
ALTER TABLE invoice_item ADD COLUMN unit VARCHAR(20);
ALTER TABLE invoice_item ADD COLUMN suggested_material_id INTEGER;
ALTER TABLE invoice_item ADD COLUMN match_confidence FLOAT;
```

**Columns:**
- `unit` - Unit of measure (pcs, m, kg, etc.) (nullable)
- `suggested_material_id` - Foreign key to suggested material match (nullable)
- `match_confidence` - Confidence score 0-100 for material match (nullable)

## Running Migrations

### Automatic (Recommended)

**During Installation:**
```bash
python scripts/init_db.py
```
Migrations run automatically after table creation.

**During Updates:**
```bash
/opt/pvapp/update.sh
```
The update script runs init_db.py which includes migrations.

### Manual Execution

```bash
cd /opt/pvapp
source .venv/bin/activate
python scripts/migrate_db.py
```

### Output Example

```
============================================================
Starting Database Migrations
============================================================
Checking invoice table for missing columns...
Adding column 'file_path' to invoice table...
✓ Successfully added column 'file_path' - Path to uploaded invoice file
Adding column 'file_type' to invoice table...
✓ Successfully added column 'file_type' - File format (PDF, DOC, TXT, XML)
Adding column 'raw_text' to invoice table...
✓ Successfully added column 'raw_text' - Extracted text content from file
Checking invoice_item table for missing columns...
✓ Column 'unit' already exists, skipping
✓ Column 'suggested_material_id' already exists, skipping
✓ Column 'match_confidence' already exists, skipping
============================================================
Database Migrations Completed Successfully!
============================================================
```

## Verification

### Check Schema

```bash
# SQLite
sqlite3 /opt/pvapp/data/pvapp.db "PRAGMA table_info(invoice);"

# Expected output includes:
# | file_path | VARCHAR(500) | 0 | NULL | 0 |
# | file_type | VARCHAR(10)  | 0 | NULL | 0 |
# | raw_text  | TEXT         | 0 | NULL | 0 |
```

### Check Migration Log

```bash
# If using systemd
journalctl -u pvapp -n 100 | grep -i migration

# Development
# Check console output when running init_db.py
```

## Troubleshooting

### Error: "table invoice has no column named file_path"

**Cause:** Database hasn't been migrated yet.

**Solution:**
```bash
# Run migration
python scripts/migrate_db.py

# Restart service
sudo systemctl restart pvapp
```

### Error: Migration script not found

**Cause:** Old version of code, missing migration script.

**Solution:**
```bash
# Update code
git pull origin copilot/add-user-registration-endpoint

# Install dependencies
pip install -r requirements.txt

# Run migration
python scripts/migrate_db.py
```

### Migration runs but columns not added

**Cause:** Database file permissions or locked database.

**Solution:**
```bash
# Stop service
sudo systemctl stop pvapp

# Check permissions
ls -la /opt/pvapp/data/pvapp.db

# Fix if needed
sudo chown pvapp:pvapp /opt/pvapp/data/pvapp.db

# Run migration
sudo -u pvapp python scripts/migrate_db.py

# Start service
sudo systemctl start pvapp
```

### "Database is locked" error

**Cause:** Service is still accessing the database.

**Solution:**
```bash
# Stop service first
sudo systemctl stop pvapp

# Run migration
python scripts/migrate_db.py

# Start service
sudo systemctl start pvapp
```

## Safety Features

✅ **Non-destructive** - Only adds columns, never removes or modifies existing data
✅ **Idempotent** - Safe to run multiple times, checks before adding
✅ **Transactional** - Uses database transactions, can rollback on error
✅ **Logged** - Clear progress and error messages
✅ **Backward compatible** - All new columns are nullable

## Best Practices

### Before Migration
1. **Backup database**
   ```bash
   cp /opt/pvapp/data/pvapp.db /opt/pvapp/data/pvapp.db.backup
   ```

2. **Stop service**
   ```bash
   sudo systemctl stop pvapp
   ```

### After Migration
1. **Verify columns added**
   ```bash
   sqlite3 /opt/pvapp/data/pvapp.db "PRAGMA table_info(invoice);"
   ```

2. **Test application**
   - Start service
   - Login to web interface
   - Try uploading an invoice
   - Verify no errors

3. **Check logs**
   ```bash
   journalctl -u pvapp -n 50
   ```

## Future Migrations

To add new migrations:

1. **Edit `scripts/migrate_db.py`**
2. **Add new migration function**
   ```python
   def migrate_new_table(engine):
       """Add new columns to new_table."""
       migrations = [
           {
               'column': 'new_column',
               'sql': 'ALTER TABLE new_table ADD COLUMN new_column VARCHAR(100)',
               'description': 'Description of column'
           }
       ]
       # ... (follow existing pattern)
   ```

3. **Call from `run_migrations()`**
   ```python
   def run_migrations():
       # ... existing migrations
       migrate_new_table(engine)
   ```

4. **Test thoroughly**
   - Test on fresh database
   - Test on existing database
   - Test multiple runs (idempotency)

## Recovery

### If Migration Fails

1. **Restore from backup**
   ```bash
   sudo systemctl stop pvapp
   cp /opt/pvapp/data/pvapp.db.backup /opt/pvapp/data/pvapp.db
   sudo systemctl start pvapp
   ```

2. **Check error logs**
   ```bash
   journalctl -u pvapp -n 100
   ```

3. **Fix issue and retry**

### If Database Corrupted

1. **Stop service**
   ```bash
   sudo systemctl stop pvapp
   ```

2. **Check database integrity**
   ```bash
   sqlite3 /opt/pvapp/data/pvapp.db "PRAGMA integrity_check;"
   ```

3. **If corrupted, restore or recreate**
   ```bash
   # From backup
   cp /opt/pvapp/data/pvapp.db.backup /opt/pvapp/data/pvapp.db
   
   # Or recreate (loses all data)
   rm /opt/pvapp/data/pvapp.db
   python scripts/init_db.py
   ```

## Additional Resources

- **Main Documentation:** README.md
- **Invoice Upload Guide:** INVOICE_UPLOAD.md
- **Troubleshooting:** TROUBLESHOOTING_UPLOAD.md
- **Raspberry Pi Guide:** RASPBERRY_PI.md

## Support

If migrations continue to fail:
1. Check you have latest code: `git pull`
2. Check dependencies installed: `pip install -r requirements.txt`
3. Check file permissions: `ls -la /opt/pvapp/data/`
4. Check disk space: `df -h`
5. Review error messages carefully
6. Check SQLite version: `sqlite3 --version` (should be 3.x)

## Summary

The migration system ensures that database schema evolves safely with the application. All migrations are:
- Safe to run multiple times
- Non-destructive to existing data
- Logged for transparency
- Integrated into the normal update process

For most users, migrations happen automatically during updates. Manual intervention is rarely needed.
