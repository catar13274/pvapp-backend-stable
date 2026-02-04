# Instalare PV Management App pe Raspberry Pi

Ghid rapid în limba română pentru instalarea aplicației pe Raspberry Pi.

## Cerințe Minime

- Raspberry Pi 3B sau mai nou (recomandat: Pi 4 cu 2GB+ RAM)
- Card microSD 16GB+ (Clasa 10)
- Alimentator oficial Raspberry Pi
- Conexiune la internet (Ethernet sau WiFi)

## Instalare Rapidă (Metoda Automată)

### Pasul 1: Pregătește Raspberry Pi

```bash
# Actualizează sistemul
sudo apt update
sudo apt upgrade -y
```

### Pasul 2: Descarcă și Rulează Scriptul de Instalare

```bash
# Metoda 1: Descarcă scriptul
curl -fsSL https://raw.githubusercontent.com/catar13274/pvapp-backend-stable/copilot/add-user-registration-endpoint/install_raspberry_pi.sh -o install.sh

# Rulează instalarea (durează 5-10 minute)
sudo bash install.sh
```

**Metoda Alternativă: Clonează repository-ul**
```bash
git clone -b copilot/add-user-registration-endpoint https://github.com/catar13274/pvapp-backend-stable.git /tmp/pvapp-install
cd /tmp/pvapp-install
sudo bash install_raspberry_pi.sh
```

> **Notă**: Se folosește branch-ul `copilot/add-user-registration-endpoint` până la merge în main.

Scriptul va:
- Instala toate dependențele necesare
- Configura aplicația
- Crea baza de date
- Porni serviciul automat

### Pasul 3: Accesează Aplicația

După instalare, accesează aplicația în browser:
- **Interfață Web**: `http://adresa-ip-raspberry-pi:8000`

Găsește adresa IP:
```bash
hostname -I
```

**Date de conectare:**
- Utilizator: `admin`
- Parolă: (afișată în timpul instalării)

## Instalare Manuală (Pas cu Pas)

### 1. Instalează Dependențele

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git sqlite3
```

### 2. Clonează Aplicația

```bash
# Creează directorul
sudo mkdir -p /opt/pvapp
sudo chown $USER:$USER /opt/pvapp

# Descarcă codul
cd /opt/pvapp
git clone https://github.com/catar13274/pvapp-backend-stable.git .
```

### 3. Configurează Mediul Python

```bash
# Creează virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Instalează dependențele
pip install -r requirements.txt
```

### 4. Configurează Aplicația

```bash
# Copiază fișierul de configurare
cp .env.example .env

# Editează configurarea
nano .env
```

Setări importante:
```bash
PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
SECRET_KEY=genereaza-o-cheie-secreta-aici
ADMIN_PASSWORD=parola-ta-sigura
CORS_ORIGINS=*
```

### 5. Inițializează Baza de Date

```bash
# Creează directorul pentru date
mkdir -p /opt/pvapp/data

# Inițializează
source .venv/bin/activate
export PVAPP_DB_URL=sqlite:////opt/pvapp/data/db.sqlite3
python scripts/init_db.py
```

### 6. Testează Aplicația

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Accesează: `http://raspberry-pi-ip:8000`

Apasă `Ctrl+C` pentru a opri.

### 7. Configurează Serviciul Automat

```bash
# Copiază fișierul serviciului
sudo cp pvapp.service /etc/systemd/system/

# Activează și pornește serviciul
sudo systemctl daemon-reload
sudo systemctl enable pvapp
sudo systemctl start pvapp

# Verifică statusul
sudo systemctl status pvapp
```

## Comenzi Utile

### Gestionarea Serviciului

```bash
# Pornește serviciul
sudo systemctl start pvapp

# Oprește serviciul
sudo systemctl stop pvapp

# Repornește serviciul
sudo systemctl restart pvapp

# Verifică status
sudo systemctl status pvapp

# Vezi loguri în timp real
sudo journalctl -u pvapp -f
```

### Backup și Întreținere

```bash
# Backup manual
/opt/pvapp/backup.sh

# Actualizare aplicație
/opt/pvapp/update.sh

# Vezi loguri recente
sudo journalctl -u pvapp -n 50
```

## Acces din Rețea

### Găsește Adresa IP

```bash
hostname -I
```

### Accesează din Browser

De pe orice dispozitiv din aceeași rețea:
```
http://192.168.1.100:8000
```
(înlocuiește cu adresa IP a Raspberry Pi-ului tău)

### Accesează de pe Telefon/Tabletă

Deschide browser-ul și introdu:
```
http://adresa-ip-raspberry-pi:8000
```

## Setare IP Static (Recomandat)

Pentru ca adresa să nu se schimbe:

```bash
# Editează configurarea rețelei
sudo nano /etc/dhcpcd.conf

# Adaugă la sfârșit (adaptează la rețeaua ta):
interface eth0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=192.168.1.1 8.8.8.8

# Repornește rețeaua
sudo systemctl restart dhcpcd
```

## Optimizări pentru Raspberry Pi

### Pentru Raspberry Pi 3

```bash
# Editează serviciul pentru 1 worker
sudo nano /etc/systemd/system/pvapp.service

# Schimbă --workers 2 în --workers 1
# Salvează și repornește
sudo systemctl daemon-reload
sudo systemctl restart pvapp
```

### Pentru Raspberry Pi 4 (4GB+)

```bash
# Poți folosi mai mulți workers
# Editează: --workers 3
```

### Activează SWAP dacă este necesar

```bash
# Verifică SWAP-ul curent
free -h

# Mărește la 2GB dacă ai probleme de memorie
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Setează CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Rezolvarea Problemelor

### Serviciul Nu Pornește

```bash
# Vezi logurile
sudo journalctl -u pvapp -n 50

# Verifică permisiunile
ls -la /opt/pvapp

# Testează manual
cd /opt/pvapp
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Nu Pot Accesa din Rețea

```bash
# Verifică dacă serviciul rulează
sudo systemctl status pvapp

# Verifică dacă portul e deschis
sudo netstat -tlnp | grep 8000

# Testează local
curl http://localhost:8000
```

### Probleme de Performanță

```bash
# Verifică temperatura
vcgencmd measure_temp

# Verifică memoria
free -h

# Reduce numărul de workers
sudo nano /etc/systemd/system/pvapp.service
# Schimbă --workers la 1
sudo systemctl daemon-reload
sudo systemctl restart pvapp
```

## Backup Automat

Backup-ul se face automat zilnic la ora 2:00 AM.

Backup-urile se păstrează în: `/opt/pvapp/backups/`

Backup-urile mai vechi de 30 zile sunt șterse automat.

## Actualizare Aplicație

```bash
# Simplu - rulează scriptul de update
/opt/pvapp/update.sh
```

Sau manual:
```bash
sudo systemctl stop pvapp
cd /opt/pvapp
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl start pvapp
```

## Resurse Adiționale

- **Documentație Completă**: Vezi `RASPBERRY_PI.md` pentru detalii avansate
- **README Principal**: Vezi `README.md` pentru documentația API
- **GitHub**: [pvapp-backend-stable](https://github.com/catar13274/pvapp-backend-stable)

## Suport

Pentru probleme sau întrebări:
1. Verifică logurile: `sudo journalctl -u pvapp -f`
2. Citește documentația: `/opt/pvapp/RASPBERRY_PI.md`
3. Raportează probleme pe GitHub

---

**Succes cu instalarea! 🌞**
