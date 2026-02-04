# Uninstallation Guide - PV Management App

## 📋 Table of Contents

1. [Before Uninstalling](#before-uninstalling)
2. [Uninstallation Methods](#uninstallation-methods)
3. [Automated Uninstallation](#automated-uninstallation)
4. [Manual Uninstallation](#manual-uninstallation)
5. [Data Preservation](#data-preservation)
6. [Complete Removal](#complete-removal)
7. [Troubleshooting](#troubleshooting)

---

## ⚠️ Before Uninstalling

### What You Need to Know

**Uninstallation will remove:**
- ✓ Application and all code files
- ✓ Systemd service (auto-start)
- ✓ Python virtual environment
- ✓ Installation scripts

**Uninstallation will NOT remove (by default):**
- ⚠️ Database (`/opt/pvapp/data/pvapp.db`)
- ⚠️ Existing backups (`/opt/pvapp/backups/`)
- ⚠️ Uploaded invoice files (`/opt/pvapp/data/invoices/`)

You will be asked if you want to delete the data.

### ⚠️ IMPORTANT WARNING

**Before uninstalling, make sure you have:**
1. Backed up all important data
2. Exported all necessary reports
3. Copied any critical information
4. Verified you no longer need the application

**Data deletion is PERMANENT and CANNOT be recovered!**

---

## 🔧 Uninstallation Methods

### Method 1: Automated Uninstallation (Recommended) ⭐

**The easiest and safest way!**

```bash
cd /opt/pvapp
sudo ./uninstall.sh
```

The script will:
1. Stop the service
2. Disable auto-start
3. Ask if you want a backup
4. Ask if you want to delete data
5. Remove the application
6. Confirm completion

### Method 2: Manual Uninstallation

For complete control, follow the steps in [Manual Uninstallation](#manual-uninstallation).

---

## 🤖 Automated Uninstallation

### Detailed Steps

#### 1. Run the Uninstallation Script

```bash
cd /opt/pvapp
sudo ./uninstall.sh
```

#### 2. Confirm Uninstallation

```
Are you sure you want to uninstall? (yes/no): yes
```

**Type:** `yes`

#### 3. Backup Data (Optional)

```
Do you want to backup your data before removal? (yes/no): yes
```

**If you want backup:** `yes`
**If not:** `no`

Backup will be created at: `~/pvapp-backup-YYYYMMDD_HHMMSS`

#### 4. Delete Data (Optional)

```
Do you want to PERMANENTLY DELETE the database and all data? (yes/no): no
```

**To keep data:** `no` (recommended)
**To delete everything:** `yes`

#### 5. Final Confirmation (if deleting data)

```
Are you ABSOLUTELY SURE? This CANNOT be undone! (yes/no): yes
```

**WARNING:** This will PERMANENTLY delete all data!

#### 6. Completion

```
============================================
Uninstallation Complete!
============================================
```

✅ Application successfully uninstalled!

---

## 🔨 Manual Uninstallation

### Step by Step

#### Step 1: Stop the Service

```bash
sudo systemctl stop pvapp
```

**Verify:**
```bash
sudo systemctl status pvapp
# Should show "inactive (dead)"
```

#### Step 2: Disable the Service

```bash
sudo systemctl disable pvapp
```

Prevents auto-start at boot.

#### Step 3: Remove Service File

```bash
sudo rm /etc/systemd/system/pvapp.service
sudo systemctl daemon-reload
```

#### Step 4: Save Data (Optional)

**If you want to keep the data:**

```bash
# Create backup
mkdir -p ~/pvapp-backup
sudo cp -r /opt/pvapp/data ~/pvapp-backup/
sudo cp -r /opt/pvapp/backups ~/pvapp-backup/
sudo chown -R $USER:$USER ~/pvapp-backup

echo "Backup created at: ~/pvapp-backup"
```

#### Step 5: Remove Application

**Option A: Keep Data**
```bash
# Remove only application, keep data
sudo rm -rf /opt/pvapp/.venv
sudo rm -rf /opt/pvapp/app
sudo rm -rf /opt/pvapp/frontend
sudo rm -rf /opt/pvapp/scripts
sudo rm -rf /opt/pvapp/examples
sudo rm -f /opt/pvapp/*.py
sudo rm -f /opt/pvapp/*.txt
sudo rm -f /opt/pvapp/*.md
sudo rm -f /opt/pvapp/*.sh
sudo rm -f /opt/pvapp/.env

# Data remains in /opt/pvapp/data and /opt/pvapp/backups
```

**Option B: Complete Removal**
```bash
# WARNING: Deletes EVERYTHING including data!
sudo rm -rf /opt/pvapp
```

#### Step 6: Verify

```bash
# Check that service no longer exists
systemctl status pvapp
# Should show: "Unit pvapp.service could not be found."

# Check directory
ls -la /opt/pvapp
# Should show: "No such file or directory" OR only data/backups if preserved
```

---

## 💾 Data Preservation

### What Data Exists

**Important Locations:**

1. **Database:**
   ```
   /opt/pvapp/data/pvapp.db
   ```
   Contains all application data.

2. **Backups:**
   ```
   /opt/pvapp/backups/
   ```
   Automatic database backups.

3. **Uploaded Invoices:**
   ```
   /opt/pvapp/data/invoices/
   ```
   PDF/DOC/TXT/XML files uploaded.

### How to Save Data

#### Method 1: Complete Backup

```bash
# Create archive with all data
mkdir -p ~/pvapp-backup
cd /opt/pvapp
sudo tar -czf ~/pvapp-backup/pvapp-data-$(date +%Y%m%d).tar.gz data/ backups/
sudo chown $USER:$USER ~/pvapp-backup/pvapp-data-*.tar.gz

echo "Backup saved to: ~/pvapp-backup/pvapp-data-$(date +%Y%m%d).tar.gz"
```

#### Method 2: Simple Copy

```bash
# Copy directories
mkdir -p ~/pvapp-backup
sudo cp -r /opt/pvapp/data ~/pvapp-backup/
sudo cp -r /opt/pvapp/backups ~/pvapp-backup/
sudo chown -R $USER:$USER ~/pvapp-backup

echo "Data copied to: ~/pvapp-backup"
```

#### Method 3: Database Export

```bash
# Export to SQL format
sudo sqlite3 /opt/pvapp/data/pvapp.db .dump > ~/pvapp-backup/pvapp-export.sql

echo "Database exported to: ~/pvapp-backup/pvapp-export.sql"
```

### Restore After Reinstallation

If you reinstall the application and want to restore data:

```bash
# After reinstalling, copy data back
sudo cp -r ~/pvapp-backup/data /opt/pvapp/
sudo cp -r ~/pvapp-backup/backups /opt/pvapp/
sudo chown -R pvapp:pvapp /opt/pvapp/data
sudo chown -R pvapp:pvapp /opt/pvapp/backups

# Restart service
sudo systemctl restart pvapp
```

---

## 🗑️ Complete Removal

### For Total Deletion

**If you want to remove absolutely everything:**

```bash
# 1. Stop service
sudo systemctl stop pvapp
sudo systemctl disable pvapp

# 2. Remove service file
sudo rm /etc/systemd/system/pvapp.service
sudo systemctl daemon-reload

# 3. Delete entire directory
sudo rm -rf /opt/pvapp

# 4. Verify
ls -la /opt/pvapp
# Should show: "No such file or directory"
```

### ⚠️ Post-Deletion Checks

```bash
# Check service
systemctl status pvapp
# Should show: "Unit pvapp.service could not be found."

# Check directory
ls /opt/ | grep pvapp
# Should return nothing

# Check processes
ps aux | grep pvapp
# Should show no pvapp processes
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. "Permission denied"

**Problem:** No root permissions.

**Solution:**
```bash
# Run with sudo
sudo ./uninstall.sh
```

#### 2. Service won't stop

**Problem:** Service has blocked processes.

**Solution:**
```bash
# Force stop
sudo systemctl kill pvapp
sudo systemctl stop pvapp

# Then continue with uninstallation
```

#### 3. "No such file or directory"

**Problem:** Application not installed or in different location.

**Solution:**
```bash
# Search for installation
sudo find / -name "pvapp" -type d 2>/dev/null

# Or check service
systemctl status pvapp
```

#### 4. Can't delete directory

**Problem:** Permissions or locked files.

**Solution:**
```bash
# Check processes
sudo lsof +D /opt/pvapp

# Kill processes
sudo fuser -k /opt/pvapp

# Try again
sudo rm -rf /opt/pvapp
```

#### 5. Want to keep only database

**Solution:**
```bash
# Copy only database
sudo cp /opt/pvapp/data/pvapp.db ~/pvapp-database-backup.db
sudo chown $USER:$USER ~/pvapp-database-backup.db

# Then delete everything
sudo rm -rf /opt/pvapp
```

---

## 📊 Uninstallation Checklist

### Before Uninstalling

- [ ] Backed up all important data
- [ ] Exported all necessary reports
- [ ] Verified no longer need application
- [ ] Read this guide completely
- [ ] Know where backups are saved

### During Uninstallation

- [ ] Service stopped
- [ ] Service disabled
- [ ] Decided on backup
- [ ] Decided on data deletion
- [ ] Confirmed actions

### After Uninstallation

- [ ] Service no longer in systemctl
- [ ] Directory removed (or only data kept)
- [ ] Backup accessible (if created)
- [ ] No pvapp processes running

---

## 🆘 Support

### Frequently Asked Questions

**Q: Can I reinstall after uninstalling?**
A: Yes! Just run the installation script again: `install_raspberry_pi.sh`

**Q: Will my data be preserved?**
A: Yes, by default the script preserves data. You'll be explicitly asked if you want to delete it.

**Q: Can I recover data after deletion?**
A: No, deletion is permanent. That's why the script asks for double confirmation.

**Q: What happens to automatic backups?**
A: They remain in `/opt/pvapp/backups/` unless explicitly deleted.

**Q: Can I reinstall and use old data?**
A: Yes! Copy the `data` directory back after reinstalling.

### Related Documentation

- [Installation](RASPBERRY_PI.md) - Installation guide
- [Troubleshooting](TROUBLESHOOTING_RPI.md) - Troubleshooting
- [Romanian Version](DEZINSTALARE.md) - Versiunea în română

---

## ✅ Completion

After uninstallation, your system will be clean and you can:
- Reinstall the application whenever you want
- Install a different application
- Use Raspberry Pi for other projects

**Thank you for using PV Management App!** 🌞

---

*Last updated: 2026-02-04*
