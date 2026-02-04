# PV Management App - Raspberry Pi Troubleshooting Guide

## Quick Diagnostic Flow

```
Problem?
   │
   ├─ Can't access web interface
   │  │
   │  ├─ From same Pi?
   │  │  │
   │  │  ├─ YES → curl http://localhost:8000
   │  │  │         Works? → Network issue
   │  │  │         Fails? → Service issue
   │  │  │
   │  │  └─ NO → Check from Pi first:
   │  │           curl http://localhost:8000
   │  │
   │  └─ Service running?
   │     sudo systemctl status pvapp
   │     │
   │     ├─ Active → Check firewall/network
   │     └─ Inactive → Start service
   │
   ├─ Service won't start
   │  │
   │  └─ Check logs:
   │     sudo journalctl -u pvapp -n 50
   │     │
   │     ├─ "Permission denied" → Fix permissions
   │     ├─ "Port in use" → Kill other process
   │     ├─ "Module not found" → Reinstall dependencies
   │     └─ "Database locked" → Remove lock file
   │
   ├─ Slow performance
   │  │
   │  ├─ Check temperature:
   │  │  vcgencmd measure_temp
   │  │  > 70°C? → Add cooling
   │  │
   │  ├─ Check memory:
   │  │  free -h
   │  │  Swap used? → Reduce workers
   │  │
   │  └─ Too many workers?
   │     Edit service, use fewer workers
   │
   └─ Database issues
      │
      ├─ Database locked?
      │  1. Stop service
      │  2. Remove .sqlite3-journal
      │  3. Start service
      │
      └─ Corrupted?
         Restore from backup
```

## Common Problems & Solutions

### 1. Can't Access from Network

**Symptoms:**
- Works on Pi (localhost:8000)
- Doesn't work from other devices

**Solutions:**

```bash
# Check if service is listening on all interfaces
sudo netstat -tlnp | grep 8000
# Should show: 0.0.0.0:8000 not 127.0.0.1:8000

# If showing 127.0.0.1, edit service:
sudo nano /etc/systemd/system/pvapp.service
# Ensure: --host 0.0.0.0

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart pvapp

# Check firewall (if UFW installed)
sudo ufw status
sudo ufw allow 8000

# Test from Pi
curl http://$(hostname -I | awk '{print $1}'):8000

# Test from another device
curl http://192.168.1.100:8000
```

### 2. Service Won't Start

**Check logs first:**
```bash
sudo journalctl -u pvapp -n 50
```

**Common errors:**

#### Error: "Permission denied"
```bash
# Fix ownership
sudo chown -R pi:pi /opt/pvapp
sudo chown -R pi:pi /opt/pvapp/data

# Fix permissions
chmod 755 /opt/pvapp
chmod 644 /opt/pvapp/.env
chmod -R 755 /opt/pvapp/data
```

#### Error: "Address already in use"
```bash
# Find process using port 8000
sudo netstat -tlnp | grep 8000
# or
sudo lsof -i :8000

# Kill the process
kill <PID>

# Restart service
sudo systemctl restart pvapp
```

#### Error: "No module named 'app'"
```bash
# Reinstall dependencies
cd /opt/pvapp
source .venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl restart pvapp
```

#### Error: "Database is locked"
```bash
# Stop service
sudo systemctl stop pvapp

# Remove lock
rm -f /opt/pvapp/data/db.sqlite3-journal

# Start service
sudo systemctl start pvapp
```

### 2.5. Installation Failures

**Problem: "fatal: destination path 'pvapp' already exists and is not an empty directory"**

This error occurs when re-running the installation script after a failed installation.

**Solution (Automatic):**

The installation script now automatically detects this and offers options:
```bash
# Just re-run the installation script
sudo bash install_raspberry_pi.sh

# It will detect the existing directory and prompt you to:
# 1) Remove and reinstall (recommended)
# 2) Cancel installation
```

**Solution (Manual):**

If you need to manually clean up:
```bash
# Remove the entire installation
sudo systemctl stop pvapp 2>/dev/null
sudo rm -rf /opt/pvapp

# Then re-run installation
sudo bash install_raspberry_pi.sh
```

**If you want to keep your data:**
```bash
# Backup data first
sudo cp -r /opt/pvapp/data /tmp/pvapp-backup

# Remove installation but keep backup
sudo systemctl stop pvapp 2>/dev/null
sudo rm -rf /opt/pvapp

# Re-run installation
sudo bash install_raspberry_pi.sh

# After installation completes, restore data
sudo systemctl stop pvapp
sudo cp -r /tmp/pvapp-backup/db.sqlite3 /opt/pvapp/data/
sudo chown -R pi:pi /opt/pvapp/data
sudo systemctl start pvapp
```

### 3. Performance Issues

**Check system resources:**
```bash
# Temperature
vcgencmd measure_temp

# Memory
free -h

# CPU usage
top -n 1 | head -20

# Disk space
df -h
```

**Solutions:**

#### High Temperature (>70°C)
```bash
# Reduce workers
sudo nano /etc/systemd/system/pvapp.service
# Change: --workers 2 to --workers 1

sudo systemctl daemon-reload
sudo systemctl restart pvapp

# Monitor temperature
watch -n 5 vcgencmd measure_temp
```

#### High Memory Usage
```bash
# Check swap
free -h

# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set: CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Reduce workers
sudo nano /etc/systemd/system/pvapp.service
# Reduce --workers

sudo systemctl daemon-reload
sudo systemctl restart pvapp
```

#### Slow Response Times
```bash
# Check database size
ls -lh /opt/pvapp/data/db.sqlite3

# Optimize database
sqlite3 /opt/pvapp/data/db.sqlite3 "VACUUM;"

# Restart service
sudo systemctl restart pvapp
```

### 4. Login Issues

**Can't login with admin credentials:**

```bash
# Reset admin password
cd /opt/pvapp
source .venv/bin/activate

# Edit .env
nano .env
# Set new ADMIN_PASSWORD

# Reinitialize (WARNING: Creates new admin, doesn't change existing)
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
export ADMIN_PASSWORD=new_password_here
python scripts/init_db.py

# Restart service
sudo systemctl restart pvapp
```

**Or reset database completely:**
```bash
# CAUTION: This deletes all data!
sudo systemctl stop pvapp
rm /opt/pvapp/data/db.sqlite3
cd /opt/pvapp
source .venv/bin/activate
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
python scripts/init_db.py
sudo systemctl start pvapp
```

### 5. Network Issues

**Static IP not working:**
```bash
# Check configuration
cat /etc/dhcpcd.conf

# Restart network
sudo systemctl restart dhcpcd

# Or reboot
sudo reboot

# Verify IP
hostname -I
```

**Can't connect to WiFi:**
```bash
# Configure WiFi
sudo raspi-config
# Navigate to: System Options > Wireless LAN

# Or manually
sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

# Add:
network={
    ssid="YourWiFiName"
    psk="YourWiFiPassword"
}

# Restart
sudo systemctl restart dhcpcd
```

### 6. Update Problems

**Update fails:**
```bash
# Manual update process
sudo systemctl stop pvapp

# Backup first
/opt/pvapp/backup.sh

# Update code
cd /opt/pvapp
git stash  # Save local changes if any
git pull
git stash pop  # Restore local changes

# Update dependencies
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Start service
sudo systemctl start pvapp
sudo systemctl status pvapp
```

**Git conflicts:**
```bash
cd /opt/pvapp
git status
git stash
git pull
# Manually reapply your changes if needed
```

### 7. Backup/Restore Issues

**Backup fails:**
```bash
# Check disk space
df -h

# Check permissions
ls -la /opt/pvapp/backups

# Manual backup
cp /opt/pvapp/data/db.sqlite3 /opt/pvapp/backups/db_manual_$(date +%Y%m%d).sqlite3
```

**Restore from backup:**
```bash
# Stop service
sudo systemctl stop pvapp

# List backups
ls -lh /opt/pvapp/backups/

# Restore (replace DATE with actual)
cp /opt/pvapp/backups/db_DATE.sqlite3 /opt/pvapp/data/db.sqlite3

# Fix permissions
chown pi:pi /opt/pvapp/data/db.sqlite3

# Start service
sudo systemctl start pvapp
```

### 8. Service Keeps Restarting

**Check logs for crash reason:**
```bash
# Watch logs live
sudo journalctl -u pvapp -f

# See recent crashes
sudo journalctl -u pvapp -n 200 | grep -i error

# Check system logs
dmesg | tail -50
```

**Common causes:**

#### Out of Memory
```bash
# Increase swap or reduce workers
sudo nano /etc/systemd/system/pvapp.service
# Reduce --workers to 1

sudo systemctl daemon-reload
sudo systemctl restart pvapp
```

#### Corrupted Database
```bash
# Check database integrity
sqlite3 /opt/pvapp/data/db.sqlite3 "PRAGMA integrity_check;"

# If corrupted, restore from backup
sudo systemctl stop pvapp
cp /opt/pvapp/backups/db_LATEST.sqlite3 /opt/pvapp/data/db.sqlite3
sudo systemctl start pvapp
```

## Diagnostic Commands

### Check Everything
```bash
#!/bin/bash
echo "=== PV App Diagnostics ==="
echo ""
echo "Service Status:"
sudo systemctl status pvapp
echo ""
echo "Port Status:"
sudo netstat -tlnp | grep 8000
echo ""
echo "Recent Logs:"
sudo journalctl -u pvapp -n 20
echo ""
echo "Temperature:"
vcgencmd measure_temp
echo ""
echo "Memory:"
free -h
echo ""
echo "Disk Space:"
df -h /opt/pvapp
echo ""
echo "Database:"
ls -lh /opt/pvapp/data/
echo ""
```

### Test Local Access
```bash
# Test API
curl http://localhost:8000/api/v1

# Expected: {"ok":true}
```

### Test Network Access
```bash
# From Raspberry Pi, test external access
IP=$(hostname -I | awk '{print $1}')
curl http://$IP:8000/api/v1
```

### Monitor Service
```bash
# Watch logs
sudo journalctl -u pvapp -f

# In another terminal, test requests
curl http://localhost:8000/api/v1
```

## Emergency Recovery

### Complete Reset (Nuclear Option)

**CAUTION: This deletes everything!**

```bash
# Stop service
sudo systemctl stop pvapp
sudo systemctl disable pvapp

# Backup data if needed
cp -r /opt/pvapp/data /tmp/pvapp-backup

# Remove everything
sudo rm -rf /opt/pvapp
sudo rm /etc/systemd/system/pvapp.service

# Reinstall
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/main/install_raspberry_pi.sh -o install.sh
sudo bash install.sh

# Restore data if needed
sudo systemctl stop pvapp
cp /tmp/pvapp-backup/db.sqlite3 /opt/pvapp/data/
sudo systemctl start pvapp
```

## Getting Help

1. **Check logs first:**
   ```bash
   sudo journalctl -u pvapp -n 100
   ```

2. **Run diagnostics:**
   ```bash
   sudo systemctl status pvapp
   vcgencmd measure_temp
   free -h
   ```

3. **Search documentation:**
   - RASPBERRY_PI.md
   - QUICKSTART_RPI.md
   - README.md

4. **Report issue:**
   - Include log output
   - Include system info (Pi model, OS version)
   - Include error messages
   - GitHub Issues

## Prevention Tips

1. **Regular backups** (automatic daily)
2. **Monitor temperature** (especially in summer)
3. **Keep updated** (run update.sh monthly)
4. **Check logs** occasionally
5. **Monitor disk space**
6. **Use stable power supply**
7. **Proper cooling** (heatsink/fan)

---

**Still stuck?** Check the full documentation:
- RASPBERRY_PI.md (complete guide)
- INSTALARE_ROMANA.md (Romanian)
- QUICKSTART_RPI.md (quick reference)
