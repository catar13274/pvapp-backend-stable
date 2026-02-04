# PV Management App - Raspberry Pi Quick Reference

## 🚀 One-Line Installation

```bash
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/main/install_raspberry_pi.sh | sudo bash
```

## 📱 Access After Installation

```
http://YOUR_RASPBERRY_PI_IP:8000
```

Default login: **admin** / (password shown during install)

## 🔧 Essential Commands

### Service Management
```bash
sudo systemctl start pvapp      # Start
sudo systemctl stop pvapp       # Stop
sudo systemctl restart pvapp    # Restart
sudo systemctl status pvapp     # Check status
```

### View Logs
```bash
sudo journalctl -u pvapp -f     # Live logs
sudo journalctl -u pvapp -n 100 # Last 100 lines
```

### Maintenance
```bash
/opt/pvapp/backup.sh           # Backup database
/opt/pvapp/update.sh           # Update app
```

## 🌐 Network Setup

### Find IP Address
```bash
hostname -I
```

### Set Static IP
```bash
sudo nano /etc/dhcpcd.conf
```
Add:
```
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1
```

## 📊 Monitor System

### Check Temperature
```bash
vcgencmd measure_temp
```

### Check Memory
```bash
free -h
```

### Check Disk Space
```bash
df -h
```

## 🛠️ Troubleshooting

### Service Won't Start
```bash
sudo journalctl -u pvapp -n 50  # Check logs
sudo systemctl restart pvapp    # Restart
```

### Can't Access from Network
```bash
sudo systemctl status pvapp     # Is it running?
sudo netstat -tlnp | grep 8000  # Is port open?
curl http://localhost:8000      # Test locally
```

### Performance Issues
1. Check temperature: `vcgencmd measure_temp`
2. Reduce workers in: `/etc/systemd/system/pvapp.service`
3. Change `--workers 2` to `--workers 1`
4. Reload: `sudo systemctl daemon-reload && sudo systemctl restart pvapp`

## 📂 Important Paths

```
/opt/pvapp/              # Application
/opt/pvapp/data/         # Database
/opt/pvapp/backups/      # Backups
/opt/pvapp/.env          # Configuration
/etc/systemd/system/pvapp.service  # Service config
```

## 🔐 Security

### Change Admin Password
1. Login to web interface
2. Go to Settings
3. Or edit: `sudo nano /opt/pvapp/.env`
4. Change `ADMIN_PASSWORD`
5. Restart: `sudo systemctl restart pvapp`

### Generate New Secret Key
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```
Add to `/opt/pvapp/.env`

## 💾 Backup & Restore

### Manual Backup
```bash
/opt/pvapp/backup.sh
```

### Restore from Backup
```bash
sudo systemctl stop pvapp
cp /opt/pvapp/backups/db_YYYYMMDD_HHMMSS.sqlite3 /opt/pvapp/data/db.sqlite3
sudo systemctl start pvapp
```

### Automatic Daily Backup
Already configured! Runs at 2:00 AM daily.
Keeps last 30 days of backups.

## 📈 Performance Tips

### Raspberry Pi 3
- Use 1 worker: `--workers 1`
- Memory limit: 512M

### Raspberry Pi 4 (2GB)
- Use 2 workers: `--workers 2`
- Memory limit: 1G

### Raspberry Pi 4 (4GB+)
- Use 3-4 workers: `--workers 3`
- Memory limit: 2G

Edit in: `/etc/systemd/system/pvapp.service`

## 🌡️ Keep Cool

If temperature > 70°C:
1. Add heatsink
2. Install fan
3. Reduce workers
4. Improve case ventilation

## 📱 Mobile Access

### Same Network
```
http://192.168.1.100:8000
```
(Use your Pi's actual IP)

### From Internet (Advanced)
- Use Tailscale (recommended): https://tailscale.com
- Or ngrok for testing: https://ngrok.com
- Port forwarding (less secure)

## ⚡ Quick Fixes

### Database Locked
```bash
sudo systemctl stop pvapp
rm -f /opt/pvapp/data/db.sqlite3-journal
sudo systemctl start pvapp
```

### Restart Everything
```bash
sudo systemctl restart pvapp
sudo reboot  # If really stuck
```

### Check Everything
```bash
sudo systemctl status pvapp
vcgencmd measure_temp
free -h
df -h
```

## 📞 Get Help

1. **Check logs first:** `sudo journalctl -u pvapp -f`
2. **Read docs:** `/opt/pvapp/RASPBERRY_PI.md`
3. **GitHub Issues:** Report problems
4. **Community:** Ask questions

## 🎯 Common Tasks

### Access from Phone
1. Find Pi IP: `hostname -I`
2. Open browser on phone
3. Go to: `http://PI_IP:8000`

### Add to Home Screen (iOS/Android)
1. Open in browser
2. Use "Add to Home Screen"
3. Access like a native app!

### Check if Working
```bash
curl http://localhost:8000/api/v1
# Should return: {"ok":true}
```

### Completely Reset
```bash
sudo systemctl stop pvapp
sudo rm -rf /opt/pvapp/data/db.sqlite3
cd /opt/pvapp
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
python scripts/init_db.py
sudo systemctl start pvapp
```

---

## 📚 Full Documentation

- **English:** [RASPBERRY_PI.md](RASPBERRY_PI.md)
- **Română:** [INSTALARE_ROMANA.md](INSTALARE_ROMANA.md)
- **API Docs:** http://YOUR_PI_IP:8000/docs

## ✅ Installation Checklist

- [ ] Raspberry Pi 3B+ or newer
- [ ] 16GB+ microSD card
- [ ] Power supply
- [ ] Network connection
- [ ] Run installation script
- [ ] Note admin password
- [ ] Access web interface
- [ ] Change default password
- [ ] Set static IP (optional)
- [ ] Test from mobile device
- [ ] Set up backups (auto-configured)

---

**Need more help?** See full documentation above! 🌞
