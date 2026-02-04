# Ghid de Dezinstalare - PV Management App

## 📋 Cuprins

1. [Înainte de Dezinstalare](#înainte-de-dezinstalare)
2. [Metode de Dezinstalare](#metode-de-dezinstalare)
3. [Dezinstalare Automată](#dezinstalare-automată)
4. [Dezinstalare Manuală](#dezinstalare-manuală)
5. [Salvarea Datelor](#salvarea-datelor)
6. [Ștergere Completă](#ștergere-completă)
7. [Depanare](#depanare)

---

## ⚠️ Înainte de Dezinstalare

### Ce Trebuie să Știi

**Dezinstalarea va elimina:**
- ✓ Aplicația și toate fișierele cod
- ✓ Serviciul systemd (pornire automată)
- ✓ Mediul virtual Python
- ✓ Scripturile de instalare

**Dezinstalarea NU va elimina (implicit):**
- ⚠️ Baza de date (`/opt/pvapp/data/pvapp.db`)
- ⚠️ Backup-urile existente (`/opt/pvapp/backups/`)
- ⚠️ Fișierele facturi încărcate (`/opt/pvapp/data/invoices/`)

Vei fi întrebat dacă vrei să ștergi datele.

### ⚠️ AVERTISMENT IMPORTANT

**Înainte de a dezinstala, asigură-te că:**
1. Ai făcut backup la toate datele importante
2. Ai exportat toate rapoartele necesare
3. Ai copiat orice informații critice
4. Ai verificat că nu mai ai nevoie de aplicație

**Ștergerea datelor este PERMANENTĂ și NU poate fi recuperată!**

---

## 🔧 Metode de Dezinstalare

### Metoda 1: Dezinstalare Automată (Recomandată) ⭐

**Cel mai simplu și mai sigur mod!**

```bash
cd /opt/pvapp
sudo ./uninstall.sh
```

Scriptul va:
1. Opri serviciul
2. Dezactiva pornirea automată
3. Întreba dacă vrei backup
4. Întreba dacă vrei să ștergi datele
5. Elimina aplicația
6. Confirma finalizarea

### Metoda 2: Dezinstalare Manuală

Pentru control complet, urmează pașii din secțiunea [Dezinstalare Manuală](#dezinstalare-manuală).

---

## 🤖 Dezinstalare Automată

### Pași Detaliați

#### 1. Rulează Scriptul de Dezinstalare

```bash
cd /opt/pvapp
sudo ./uninstall.sh
```

#### 2. Confirmă Dezinstalarea

```
Are you sure you want to uninstall? (yes/no): yes
```

**Tastează:** `yes`

#### 3. Backup Date (Opțional)

```
Do you want to backup your data before removal? (yes/no): yes
```

**Dacă vrei backup:** `yes`
**Dacă nu:** `no`

Backup-ul va fi creat în: `~/pvapp-backup-YYYYMMDD_HHMMSS`

#### 4. Ștergere Date (Opțional)

```
Do you want to PERMANENTLY DELETE the database and all data? (yes/no): no
```

**Pentru a păstra datele:** `no` (recomandat)
**Pentru a șterge tot:** `yes`

#### 5. Confirmare Finală (dacă ștergi datele)

```
Are you ABSOLUTELY SURE? This CANNOT be undone! (yes/no): yes
```

**ATENȚIE:** Aceasta va șterge PERMANENT toate datele!

#### 6. Finalizare

```
============================================
Uninstallation Complete!
============================================
```

✅ Aplicația a fost dezinstalată cu succes!

---

## 🔨 Dezinstalare Manuală

### Pas cu Pas

#### Pas 1: Oprește Serviciul

```bash
sudo systemctl stop pvapp
```

**Verifică:**
```bash
sudo systemctl status pvapp
# Ar trebui să fie "inactive (dead)"
```

#### Pas 2: Dezactivează Serviciul

```bash
sudo systemctl disable pvapp
```

Oprește pornirea automată la boot.

#### Pas 3: Elimină Fișierul Serviciu

```bash
sudo rm /etc/systemd/system/pvapp.service
sudo systemctl daemon-reload
```

#### Pas 4: Salvează Datele (Opțional)

**Dacă vrei să păstrezi datele:**

```bash
# Creează backup
mkdir -p ~/pvapp-backup
sudo cp -r /opt/pvapp/data ~/pvapp-backup/
sudo cp -r /opt/pvapp/backups ~/pvapp-backup/
sudo chown -R $USER:$USER ~/pvapp-backup

echo "Backup creat în: ~/pvapp-backup"
```

#### Pas 5: Elimină Aplicația

**Opțiunea A: Păstrează Datele**
```bash
# Elimină doar aplicația, păstrează datele
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

# Datele rămân în /opt/pvapp/data și /opt/pvapp/backups
```

**Opțiunea B: Ștergere Completă**
```bash
# ATENȚIE: Șterge TOT, inclusiv datele!
sudo rm -rf /opt/pvapp
```

#### Pas 6: Verifică

```bash
# Verifică că serviciul nu mai există
systemctl status pvapp
# Ar trebui: "Unit pvapp.service could not be found."

# Verifică directorul
ls -la /opt/pvapp
# Ar trebui: "No such file or directory" SAU doar data/backups dacă le-ai păstrat
```

---

## 💾 Salvarea Datelor

### Ce Date Există

**Locații Importante:**

1. **Baza de Date:**
   ```
   /opt/pvapp/data/pvapp.db
   ```
   Conține toate datele aplicației.

2. **Backup-uri:**
   ```
   /opt/pvapp/backups/
   ```
   Backup-uri automate ale bazei de date.

3. **Facturi Încărcate:**
   ```
   /opt/pvapp/data/invoices/
   ```
   Fișiere PDF/DOC/TXT/XML încărcate.

### Cum să Salvezi Datele

#### Metoda 1: Backup Complet

```bash
# Creează arhivă cu toate datele
mkdir -p ~/pvapp-backup
cd /opt/pvapp
sudo tar -czf ~/pvapp-backup/pvapp-data-$(date +%Y%m%d).tar.gz data/ backups/
sudo chown $USER:$USER ~/pvapp-backup/pvapp-data-*.tar.gz

echo "Backup salvat în: ~/pvapp-backup/pvapp-data-$(date +%Y%m%d).tar.gz"
```

#### Metoda 2: Copiere Simplă

```bash
# Copiază directoare
mkdir -p ~/pvapp-backup
sudo cp -r /opt/pvapp/data ~/pvapp-backup/
sudo cp -r /opt/pvapp/backups ~/pvapp-backup/
sudo chown -R $USER:$USER ~/pvapp-backup

echo "Date copiate în: ~/pvapp-backup"
```

#### Metoda 3: Export Bază de Date

```bash
# Export în format SQL
sudo sqlite3 /opt/pvapp/data/pvapp.db .dump > ~/pvapp-backup/pvapp-export.sql

echo "Baza de date exportată în: ~/pvapp-backup/pvapp-export.sql"
```

### Restaurare După Reinstalare

Dacă reinstalezi aplicația și vrei să restaurezi datele:

```bash
# După reinstalare, copiază datele înapoi
sudo cp -r ~/pvapp-backup/data /opt/pvapp/
sudo cp -r ~/pvapp-backup/backups /opt/pvapp/
sudo chown -R pvapp:pvapp /opt/pvapp/data
sudo chown -R pvapp:pvapp /opt/pvapp/backups

# Repornește serviciul
sudo systemctl restart pvapp
```

---

## 🗑️ Ștergere Completă

### Pentru Ștergere Totală

**Dacă vrei să elimini absolut tot:**

```bash
# 1. Oprește serviciul
sudo systemctl stop pvapp
sudo systemctl disable pvapp

# 2. Elimină fișierul serviciu
sudo rm /etc/systemd/system/pvapp.service
sudo systemctl daemon-reload

# 3. Șterge tot directorul
sudo rm -rf /opt/pvapp

# 4. Verifică
ls -la /opt/pvapp
# Ar trebui: "No such file or directory"
```

### ⚠️ Verificări După Ștergere

```bash
# Verifică serviciul
systemctl status pvapp
# Ar trebui: "Unit pvapp.service could not be found."

# Verifică directorul
ls /opt/ | grep pvapp
# Nu ar trebui să apară nimic

# Verifică procese
ps aux | grep pvapp
# Nu ar trebui să apară procese
```

---

## 🔍 Depanare

### Probleme Comune

#### 1. "Permission denied"

**Problemă:** Nu ai permisiuni root.

**Soluție:**
```bash
# Rulează cu sudo
sudo ./uninstall.sh
```

#### 2. Serviciul nu se oprește

**Problemă:** Serviciul are procese blocate.

**Soluție:**
```bash
# Forțează oprirea
sudo systemctl kill pvapp
sudo systemctl stop pvapp

# Apoi continuă cu dezinstalarea
```

#### 3. "No such file or directory"

**Problemă:** Aplicația nu este instalată sau este în alt loc.

**Soluție:**
```bash
# Caută instalația
sudo find / -name "pvapp" -type d 2>/dev/null

# Sau verifică serviciul
systemctl status pvapp
```

#### 4. Nu pot șterge directorul

**Problemă:** Permisiuni sau fișiere blocate.

**Soluție:**
```bash
# Verifică procesele
sudo lsof +D /opt/pvapp

# Omoară procesele
sudo fuser -k /opt/pvapp

# Încearcă din nou
sudo rm -rf /opt/pvapp
```

#### 5. Vreau să păstrez doar baza de date

**Soluție:**
```bash
# Copiază doar baza de date
sudo cp /opt/pvapp/data/pvapp.db ~/pvapp-database-backup.db
sudo chown $USER:$USER ~/pvapp-database-backup.db

# Apoi șterge tot
sudo rm -rf /opt/pvapp
```

---

## 📊 Checklist Dezinstalare

### Înainte de Dezinstalare

- [ ] Am făcut backup la toate datele importante
- [ ] Am exportat toate rapoartele necesare
- [ ] Am verificat că nu mai am nevoie de aplicație
- [ ] Am citit acest ghid complet
- [ ] Știu unde sunt salvate backup-urile

### În Timpul Dezinstalării

- [ ] Serviciul a fost oprit
- [ ] Serviciul a fost dezactivat
- [ ] Am decis dacă vreau backup
- [ ] Am decis dacă vreau să șterg datele
- [ ] Am confirmat acțiunile

### După Dezinstalare

- [ ] Serviciul nu mai apare în systemctl
- [ ] Directorul a fost eliminat (sau doar datele păstrate)
- [ ] Backup-ul este accesibil (dacă am făcut)
- [ ] Nu mai sunt procese pvapp active

---

## 🆘 Suport

### Întrebări Frecvente

**Î: Pot să reinstalez aplicația după dezinstalare?**
R: Da! Doar rulează din nou scriptul de instalare: `install_raspberry_pi.sh`

**Î: Datele mele vor fi păstrate?**
R: Da, implicit scriptul păstrează datele. Vei fi întrebat explicit dacă vrei să le ștergi.

**Î: Pot să recuperez datele după ce le-am șters?**
R: Nu, ștergerea este permanentă. De aceea scriptul cere confirmare dublă.

**Î: Ce se întâmplă cu backup-urile automate?**
R: Rămân în `/opt/pvapp/backups/` dacă nu le ștergi explicit.

**Î: Pot să reinstalez și să folosesc datele vechi?**
R: Da! Copiază directorul `data` înapoi după reinstalare.

### Documentație Conexă

- [Instalare](INSTALARE_ROMANA.md) - Ghid de instalare
- [Troubleshooting](TROUBLESHOOTING_RPI.md) - Depanare
- [Uninstall English](UNINSTALL.md) - English version

---

## ✅ Finalizare

După dezinstalare, sistemul tău va fi curat și poți:
- Reinstala aplicația când vrei
- Instala o altă aplicație
- Folosi Raspberry Pi pentru alte proiecte

**Mulțumim că ai folosit PV Management App!** 🌞

---

*Ultima actualizare: 2026-02-04*
