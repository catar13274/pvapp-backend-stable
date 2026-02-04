# Installation Script Access

## Current Status

The Raspberry Pi installation scripts and documentation are currently in the feature branch:
- Branch: `copilot/add-user-registration-endpoint`
- Status: Pending merge to `main`

## How to Install

### Option 1: Direct Download (Recommended)

```bash
# Download the installation script
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/copilot/add-user-registration-endpoint/install_raspberry_pi.sh -o install.sh

# Make it executable
chmod +x install.sh

# Run installation
sudo ./install.sh
```

### Option 2: Clone Repository

```bash
# Clone the repository with the feature branch
git clone -b copilot/add-user-registration-endpoint https://github.com/catar13274/pvapp-backend-stable.git /tmp/pvapp-install

# Navigate to directory
cd /tmp/pvapp-install

# Run installation
sudo bash install_raspberry_pi.sh
```

### Option 3: Manual Installation

If you prefer to install manually, follow the complete guide in [RASPBERRY_PI.md](RASPBERRY_PI.md).

## After Installation

Once installed, access the application at:
```
http://YOUR_RASPBERRY_PI_IP:8000
```

Default credentials:
- Username: `admin`
- Password: Displayed during installation or set via `ADMIN_PASSWORD` env variable

## After Merge to Main

Once this pull request is merged to the `main` branch, the installation command will be simplified to:

```bash
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/main/install_raspberry_pi.sh | sudo bash
```

## Documentation

All Raspberry Pi documentation is available in this repository:

- **[README_RASPBERRY_PI.md](README_RASPBERRY_PI.md)** - Master hub
- **[RASPBERRY_PI.md](RASPBERRY_PI.md)** - Complete deployment guide  
- **[QUICKSTART_RPI.md](QUICKSTART_RPI.md)** - Quick reference
- **[INSTALARE_ROMANA.md](INSTALARE_ROMANA.md)** - Romanian guide
- **[ARCHITECTURE_RPI.md](ARCHITECTURE_RPI.md)** - System architecture
- **[TROUBLESHOOTING_RPI.md](TROUBLESHOOTING_RPI.md)** - Problem solving

## Troubleshooting

If you encounter any issues:

1. **404 Error**: Make sure you're using the correct branch URL (see Option 1 or 2 above)
2. **Permission Denied**: Run the script with `sudo`
3. **Directory Already Exists**: The script will detect if `/opt/pvapp` exists and offer to:
   - Remove and reinstall (recommended for failed installations)
   - Cancel and let you handle it manually
4. **Other Issues**: See [TROUBLESHOOTING_RPI.md](TROUBLESHOOTING_RPI.md)

### Re-running Installation

If a previous installation failed, the script is now smart enough to detect existing directories:
- If a git repository exists, it will update it
- If the directory exists but isn't a git repository, it will prompt you to remove it
- This prevents the "directory already exists" error

## Need Help?

- Check the [complete documentation](RASPBERRY_PI.md)
- Review the [troubleshooting guide](TROUBLESHOOTING_RPI.md)
- Open an issue on GitHub

---

**Note**: This file will be removed once the pull request is merged to main and the standard URLs become active.
