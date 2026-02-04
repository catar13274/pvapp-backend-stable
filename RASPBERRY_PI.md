# Deploying PV Management App on Raspberry Pi

This guide will help you deploy the PV Management App on a Raspberry Pi, perfect for local installation management at PV installation sites.

## Table of Contents
- [Hardware Requirements](#hardware-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Production Deployment](#production-deployment)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)

## Hardware Requirements

### Minimum Requirements
- **Raspberry Pi**: Model 3B or newer (3B+, 4, 5)
- **RAM**: 1GB minimum (2GB+ recommended)
- **Storage**: 8GB SD card minimum (16GB+ recommended)
- **Power Supply**: Official Raspberry Pi power supply
- **Network**: Ethernet or WiFi connection

### Recommended Setup
- **Raspberry Pi 4** (4GB RAM) or **Raspberry Pi 5**
- **32GB** microSD card (Class 10 or better)
- **Ethernet connection** for stability
- **Case with cooling** (fan or heatsink)

## Quick Start

For fastest deployment, use the automated installation script:

```bash
# 1. Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/main/install_raspberry_pi.sh -o install.sh
chmod +x install.sh
sudo ./install.sh

# 2. The script will install everything and start the service
# Access the app at: http://raspberry-pi-ip:8000
```

Default credentials:
- Username: `admin`
- Password: Will be displayed during installation or set via `ADMIN_PASSWORD`

## Detailed Installation

### Step 1: Prepare Raspberry Pi

1. **Install Raspberry Pi OS (Lite recommended for headless)**
   ```bash
   # Use Raspberry Pi Imager from https://www.raspberrypi.com/software/
   # Choose: Raspberry Pi OS Lite (64-bit) for best performance
   ```

2. **Update system packages**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

3. **Set hostname (optional)**
   ```bash
   sudo raspi-config
   # Navigate to System Options > Hostname
   # Set to "pvapp" or your preferred name
   ```

### Step 2: Install Dependencies

```bash
# Install Python and system dependencies
sudo apt install -y python3 python3-pip python3-venv git

# Install additional libraries for PDF generation
sudo apt install -y python3-dev libffi-dev libssl-dev

# Install SQLite (usually pre-installed)
sudo apt install -y sqlite3
```

### Step 3: Clone and Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/pvapp
sudo chown $USER:$USER /opt/pvapp
cd /opt/pvapp

# Clone repository (or copy files)
git clone https://github.com/catar13274/pvapp-backend-stable.git .

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Application

```bash
# Create environment file
cp .env.example .env

# Edit configuration
nano .env
```

Recommended settings for Raspberry Pi:
```bash
# Database URL (SQLite for simplicity)
PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3

# Generate a secure secret key
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Set admin password
ADMIN_PASSWORD=your_secure_password_here

# CORS settings (allow access from local network)
CORS_ORIGINS=*
```

```bash
# Create data directory
mkdir -p /opt/pvapp/data

# Initialize database
source .venv/bin/activate
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
python scripts/init_db.py
```

### Step 5: Test Manual Start

```bash
# Test the application
source .venv/bin/activate
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
export SECRET_KEY=your-secret-key
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Access from another device on your network:
# http://raspberry-pi-ip:8000
```

Press `Ctrl+C` to stop.

## Production Deployment

### Using Systemd Service (Recommended)

1. **Create systemd service file**
   ```bash
   sudo nano /etc/systemd/system/pvapp.service
   ```

2. **Add the following content:**
   ```ini
   [Unit]
   Description=PV Management App
   After=network.target

   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/opt/pvapp
   Environment="PATH=/opt/pvapp/.venv/bin"
   Environment="PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3"
   EnvironmentFile=/opt/pvapp/.env
   ExecStart=/opt/pvapp/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. **Enable and start service**
   ```bash
   # Reload systemd
   sudo systemctl daemon-reload

   # Enable service to start on boot
   sudo systemctl enable pvapp

   # Start service now
   sudo systemctl start pvapp

   # Check status
   sudo systemctl status pvapp
   ```

4. **Service management commands**
   ```bash
   # Start service
   sudo systemctl start pvapp

   # Stop service
   sudo systemctl stop pvapp

   # Restart service
   sudo systemctl restart pvapp

   # View logs
   sudo journalctl -u pvapp -f

   # View recent logs
   sudo journalctl -u pvapp -n 50
   ```

### Performance Optimization for Raspberry Pi

1. **Use production server settings**
   ```bash
   # Edit service file to use optimal workers
   # For Pi 3: --workers 1
   # For Pi 4 (2GB): --workers 2
   # For Pi 4 (4GB+): --workers 3-4
   ```

2. **Reduce memory usage**
   ```bash
   # In .env file, keep database on SD card for better performance
   PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
   ```

3. **Enable swap if needed**
   ```bash
   # Check current swap
   free -h

   # Increase swap to 2GB if running multiple workers
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=2048
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

### Network Access Configuration

1. **Find Raspberry Pi IP address**
   ```bash
   hostname -I
   ```

2. **Set static IP (optional but recommended)**
   ```bash
   sudo nano /etc/dhcpcd.conf
   ```
   
   Add at the end:
   ```
   interface eth0
   static ip_address=192.168.1.100/24
   static routers=192.168.1.1
   static domain_name_servers=192.168.1.1 8.8.8.8
   ```

3. **Configure firewall (optional)**
   ```bash
   # Install UFW
   sudo apt install -y ufw

   # Allow SSH
   sudo ufw allow 22

   # Allow PV App
   sudo ufw allow 8000

   # Enable firewall
   sudo ufw enable
   ```

### Using Nginx as Reverse Proxy (Optional)

For professional deployment with HTTPS:

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/pvapp

# Add configuration:
server {
    listen 80;
    server_name pvapp.local;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/pvapp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Now access via http://raspberry-pi-ip (port 80)
```

## Maintenance

### Database Backup

Create automatic backup script:

```bash
# Create backup script
cat > /opt/pvapp/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/pvapp/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
cp /opt/pvapp/data/db.sqlite3 $BACKUP_DIR/db_$DATE.sqlite3

# Keep only last 30 days of backups
find $BACKUP_DIR -name "db_*.sqlite3" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sqlite3"
EOF

chmod +x /opt/pvapp/backup.sh

# Add to crontab for daily backups
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/pvapp/backup.sh") | crontab -
```

### Update Application

```bash
# Stop service
sudo systemctl stop pvapp

# Backup current data
/opt/pvapp/backup.sh

# Update code
cd /opt/pvapp
git pull

# Update dependencies
source .venv/bin/activate
pip install -r requirements.txt

# Restart service
sudo systemctl start pvapp
```

### Monitor Logs

```bash
# Real-time logs
sudo journalctl -u pvapp -f

# Last 100 lines
sudo journalctl -u pvapp -n 100

# Logs from today
sudo journalctl -u pvapp --since today

# Errors only
sudo journalctl -u pvapp -p err
```

### Check System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Check service status
sudo systemctl status pvapp

# Check temperature (important for Raspberry Pi)
vcgencmd measure_temp
```

## Troubleshooting

### Service Won't Start

1. **Check logs**
   ```bash
   sudo journalctl -u pvapp -n 50
   ```

2. **Check permissions**
   ```bash
   ls -la /opt/pvapp
   ls -la /opt/pvapp/data
   ```

3. **Test manual start**
   ```bash
   cd /opt/pvapp
   source .venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Can't Access from Network

1. **Check if service is running**
   ```bash
   sudo systemctl status pvapp
   ```

2. **Check if port is open**
   ```bash
   sudo netstat -tlnp | grep 8000
   ```

3. **Check firewall**
   ```bash
   sudo ufw status
   ```

4. **Check from Raspberry Pi itself**
   ```bash
   curl http://localhost:8000
   ```

### Performance Issues

1. **Reduce workers in service file**
   ```bash
   sudo nano /etc/systemd/system/pvapp.service
   # Change --workers 2 to --workers 1
   sudo systemctl daemon-reload
   sudo systemctl restart pvapp
   ```

2. **Check temperature**
   ```bash
   vcgencmd measure_temp
   # If >70°C, improve cooling
   ```

3. **Check memory**
   ```bash
   free -h
   # If swap is heavily used, reduce workers or increase swap
   ```

### Database Locked Errors

```bash
# Stop service
sudo systemctl stop pvapp

# Check for stuck processes
ps aux | grep uvicorn

# Remove lock if needed
rm -f /opt/pvapp/data/db.sqlite3-journal

# Restart service
sudo systemctl start pvapp
```

## Remote Access

### Access from Mobile Devices

1. **Find your Raspberry Pi IP**
   ```bash
   hostname -I
   ```

2. **Access from browser**
   - On same network: `http://192.168.1.100:8000` (use your Pi's IP)

### Access from Internet (Advanced)

⚠️ **Security Warning**: Only do this if you understand the security implications.

1. **Use a reverse proxy service** (recommended)
   - Install [Tailscale](https://tailscale.com) for secure access
   - Or use [ngrok](https://ngrok.com) for temporary access

2. **Port forwarding** (less secure)
   - Configure your router to forward port 8000 to your Raspberry Pi
   - Use strong passwords and SECRET_KEY
   - Consider adding HTTPS with Let's Encrypt

## Additional Tips

### Automatic Updates

```bash
# Create update script
cat > /opt/pvapp/update.sh << 'EOF'
#!/bin/bash
cd /opt/pvapp
sudo systemctl stop pvapp
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start pvapp
EOF

chmod +x /opt/pvapp/update.sh
```

### Monitoring Service Health

```bash
# Create health check script
cat > /opt/pvapp/healthcheck.sh << 'EOF'
#!/bin/bash
if ! curl -f http://localhost:8000/api/v1 > /dev/null 2>&1; then
    echo "Service down, restarting..."
    sudo systemctl restart pvapp
    echo "Service restarted at $(date)" >> /opt/pvapp/restarts.log
fi
EOF

chmod +x /opt/pvapp/healthcheck.sh

# Add to crontab (check every 5 minutes)
(crontab -l 2>/dev/null; echo "*/5 * * * * /opt/pvapp/healthcheck.sh") | crontab -
```

### LED Status Indicator (Fun!)

```bash
# Install GPIO library
pip install RPi.GPIO

# Create LED status script (uses GPIO 18)
# Green LED when service is running
```

## Getting Help

- Check logs: `sudo journalctl -u pvapp -f`
- GitHub Issues: [Report issues](https://github.com/catar13274/pvapp-backend-stable/issues)
- Check README: `/opt/pvapp/README.md`

## Summary of Commands

```bash
# Service Management
sudo systemctl start pvapp    # Start
sudo systemctl stop pvapp     # Stop
sudo systemctl restart pvapp  # Restart
sudo systemctl status pvapp   # Status

# Logs
sudo journalctl -u pvapp -f   # Real-time logs

# Backup
/opt/pvapp/backup.sh          # Manual backup

# Update
/opt/pvapp/update.sh          # Update application

# Access
http://raspberry-pi-ip:8000   # Web interface
```

---

**Ready to deploy?** Start with the [Quick Start](#quick-start) section above!
