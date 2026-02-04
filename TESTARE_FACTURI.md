# 🧪 Ghid de Testare - Încărcare Facturi

Acest document te ajută să testezi funcționalitatea de încărcare și procesare automată a facturilor.

## 📋 Introducere

Funcția de încărcare facturi permite:
- Încărcarea facturilor în format PDF, DOC, TXT sau XML
- Extragerea automată a informațiilor (furnizor, număr, data, articole)
- Matching inteligent cu materialele existente
- Crearea automată de materiale noi
- Adăugarea în stoc cu un singur click

## 🎯 Pregătire pentru Testare

### Cerințe
1. ✅ Aplicația pornită și funcțională
2. ✅ Cont de utilizator autentificat
3. ✅ Baza de date migrată (dacă ai instalare veche, rulează `./fix_database.sh`)
4. ✅ Fișiere de test disponibile în directorul `examples/`

### Verificare Rapidă
```bash
# Verifică că aplicația rulează
curl http://localhost:8000/docs

# Verifică că ai fișierele de test
ls examples/
# Ar trebui să vezi: sample_invoice_ro.txt, sample_invoice_en.txt, sample_invoice.xml
```

## 📁 Fișiere de Test Disponibile

### 1. sample_invoice_ro.txt (Recomandat pentru început)
- **Format**: Text simplu
- **Limba**: Română
- **Articole**: 6 articole (panouri, invertoare, cabluri, conectori, structuri, tablou)
- **Total**: 19,890.85 RON
- **Nivel dificultate**: ⭐ Ușor

### 2. sample_invoice_en.txt
- **Format**: Text simplu
- **Limba**: Engleză
- **Articole**: 8 articole (panouri 400W, inverter hibrid, cabluri, întrerupătoare)
- **Total**: 17,879.75 EUR
- **Nivel dificultate**: ⭐⭐ Mediu

### 3. sample_invoice.xml
- **Format**: XML (compatibil e-factura)
- **Limba**: Română
- **Articole**: 6 articole cu structură XML completă
- **Total**: 33,409.25 RON
- **Nivel dificultate**: ⭐⭐⭐ Avansat

## 🧪 Scenarii de Testare

### Scenariul 1: Factură Simplă în Română (Recomandat)

**Obiectiv**: Testează fluxul complet de la upload la confirmare

**Pași**:
1. Încarcă `examples/sample_invoice_ro.txt`
2. Verifică extragerea datelor
3. Validează matching-ul materialelor
4. Creează materiale noi unde e necesar
5. Confirmă factura
6. Verifică stocul actualizat

**Rezultat așteptat**:
- ✅ Furnizor: SOLAR ENERGY SRL
- ✅ Număr factură: FAC-2024-001
- ✅ Data: 15.01.2024
- ✅ 6 articole extrase corect
- ✅ Matching sugerat pentru articole comune
- ✅ Posibilitate de creare materiale noi
- ✅ Stoc actualizat după confirmare

### Scenariul 2: Factură în Engleză

**Obiectiv**: Testează suportul multi-limbă

**Pași**:
1. Încarcă `examples/sample_invoice_en.txt`
2. Verifică că sistemul recunoaște limba engleză
3. Validează extragerea articolelor în engleză
4. Testează matching-ul cu materiale existente

**Rezultat așteptat**:
- ✅ Furnizor: GREEN POWER SYSTEMS LTD
- ✅ Număr factură: INV-2024-042
- ✅ 8 articole extrase
- ✅ Descrieri în engleză păstrate

### Scenariul 3: Factură XML (e-factura)

**Obiectiv**: Testează parsing-ul XML structurat

**Pași**:
1. Încarcă `examples/sample_invoice.xml`
2. Verifică că XML-ul e parsat corect
3. Validează structura completă
4. Testează toate câmpurile extrase

**Rezultat așteptat**:
- ✅ Toate tag-urile XML parsate
- ✅ Structură completă cu TVA
- ✅ Detalii furnizor și client
- ✅ 6 articole cu toate detaliile

## 🔍 Pași Detalați de Testare

### Pasul 1: Pornește Aplicația

```bash
# Pentru instalare Raspberry Pi (producție)
sudo systemctl status pvapp
# Dacă nu rulează:
sudo systemctl start pvapp

# Pentru dezvoltare
cd /opt/pvapp
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Pasul 2: Deschide Interfața Web

1. Deschide browser-ul
2. Navighează la: `http://localhost:8000` (sau IP-ul Raspberry Pi)
3. Ar trebui să vezi pagina de login

### Pasul 3: Autentifică-te

1. Introdu credențialele:
   - **Username**: `admin`
   - **Password**: (parola setată la instalare)
2. Click pe "Login"
3. Ar trebui să vezi dashboard-ul

### Pasul 4: Navighează la Facturi

1. În sidebar-ul din stânga, găsește "🧾 Invoices"
2. Click pe "Invoices"
3. Ar trebui să vezi lista de facturi (probabil goală)

### Pasul 5: Încarcă Factura

1. Click pe butonul "📤 Upload Invoice" (sus, lângă titlu)
2. Se va deschide un dialog de upload
3. Click pe "Choose File" sau drag-and-drop
4. Navighează la directorul `examples/`
5. Selectează `sample_invoice_ro.txt`
6. Click "Upload & Parse"

### Pasul 6: Așteaptă Procesarea

Ar trebui să vezi:
```
Uploading...
Processing file...
Parsing invoice...
Extracting items...
```

După câteva secunde (1-3), se va deschide ecranul de validare.

### Pasul 7: Validează Datele Extrase

Ecranul de validare arată:

**Header Factură:**
- Supplier: SOLAR ENERGY SRL ✓
- Invoice #: FAC-2024-001 ✓
- Date: 15.01.2024 ✓
- Total: 19,890.85 RON ✓

**Articole Extrase (6):**

| # | Descriere | Cant | UM | Preț | Acțiune | Material Sugerat |
|---|-----------|------|----|----- |---------|------------------|
| 1 | Panou solar fotovoltaic 300W policristalin | 20 | buc | 450.00 | Selectează ▼ | Solar Panel 300W (85% match) |
| 2 | Inverter solar on-grid 5kW trifazat | 4 | buc | 1,200.00 | Selectează ▼ | Inverter 5kW (78% match) |
| 3 | Cablu solar 6mm² UV rezistent | 50 | m | 8.50 | Creează Nou | - |
| 4 | Conector MC4 pereche | 40 | set | 3.50 | Selectează ▼ | MC4 Connector (92% match) |
| 5 | Structura montaj tabla inclinata | 20 | buc | 75.00 | Creează Nou | - |
| 6 | Tablou protectie si monitorizare | 1 | buc | 850.00 | Creează Nou | - |

### Pasul 8: Alege Acțiunea pentru Fiecare Articol

Pentru fiecare articol, ai două opțiuni:

#### Opțiunea A: Folosește Material Existent
1. Selectează "Use Existing Material"
2. Alege din dropdown materialul potrivit
3. Sistemul arată procentul de matching (ex: 85%)
4. Alege materialul cu cel mai mare procent

#### Opțiunea B: Creează Material Nou
1. Selectează "Create New Material"
2. Completează formularul:
   - **Name**: (pre-completat din descriere)
   - **Category**: Alege categorie (Solar Panels, Inverters, Cables, etc.)
   - **Unit**: (pre-completat din factură: buc, m, set)
   - **Minimum Stock**: Setează un minim (ex: 10)
3. Materialul va fi creat automat

### Pasul 9: Validează și Confirmă

După ce ai configurat toate articolele:
1. Verifică că toate articolele au o acțiune setată
2. Click "✓ Validate & Confirm Invoice"
3. Opțional: Bifează "Also confirm invoice now" pentru confirmare imediată
4. Click "Confirm"

**Ce se întâmplă:**
- ✅ Materiale noi sunt create în baza de date
- ✅ Articolele facturii sunt mapate la materiale
- ✅ Status factură: VALIDATED (sau CONFIRMED dacă ai bifat)
- ✅ Dacă ai confirmat: mișcări stoc IN create automat
- ✅ Dacă ai confirmat: inventarul e actualizat

### Pasul 10: Verifică Rezultatele

#### În secțiunea Facturi:
- Factura apare în listă
- Status: VALIDATED sau CONFIRMED
- Click "View" pentru detalii complete

#### În secțiunea Materiale:
1. Mergi la "📦 Materials"
2. Ar trebui să vezi materialele noi create
3. Verifică că au:
   - Numele corect
   - Categoria setată
   - Unitatea de măsură
   - Stocul actualizat (dacă ai confirmat factura)

#### În secțiunea Stoc:
1. Mergi la "📋 Stock"
2. Dacă ai confirmat factura, ar trebui să vezi:
   - Mișcări de tip "IN"
   - Linked to invoice (număr factură)
   - Cantitățile din factură
   - Data și ora

## ✅ Ce Să Verifici

### Verificare Upload
- [ ] Fișierul se încarcă fără erori
- [ ] Progres bar apare și se completează
- [ ] Se deschide ecranul de validare după upload

### Verificare Extragere Date
- [ ] Nume furnizor extras corect
- [ ] Număr factură identificat
- [ ] Data extrasă (dacă există în factură)
- [ ] Total calculat (dacă există)

### Verificare Articole
- [ ] Toate articolele din factură sunt extrase
- [ ] Descrierile sunt complete
- [ ] Cantitățile sunt corecte
- [ ] Unitățile de măsură identificate
- [ ] Prețurile extrase corect

### Verificare Matching
- [ ] Matching-ul sugerează materiale existente
- [ ] Procentul de matching e rezonabil (>30%)
- [ ] Materialele sugerate sunt relevante
- [ ] Poți selecta alt material din dropdown

### Verificare Creare Materiale
- [ ] Formularul de material nou e pre-completat
- [ ] Poți edita toate câmpurile
- [ ] Materialul e creat după confirmare
- [ ] Apare în lista de materiale

### Verificare Confirmare
- [ ] Validarea funcționează
- [ ] Status factură se schimbă
- [ ] Mișcările stoc sunt create
- [ ] Inventarul e actualizat
- [ ] Totul e legat corect (invoice → items → materials → stock)

## 🎯 Rezultate Așteptate

### Pentru sample_invoice_ro.txt

**Date Extrase:**
```
Supplier: SOLAR ENERGY SRL
Invoice Number: FAC-2024-001
Date: 15.01.2024
Total: 19,890.85 RON
Status: PARSED

Items (6):
1. Panou solar fotovoltaic 300W policristalin
   Qty: 20 buc @ 450.00 = 9,000.00
   
2. Inverter solar on-grid 5kW trifazat
   Qty: 4 buc @ 1,200.00 = 4,800.00
   
3. Cablu solar 6mm² UV rezistent
   Qty: 50 m @ 8.50 = 425.00
   
4. Conector MC4 pereche
   Qty: 40 set @ 3.50 = 140.00
   
5. Structura montaj tabla inclinata
   Qty: 20 buc @ 75.00 = 1,500.00
   
6. Tablou protectie si monitorizare
   Qty: 1 buc @ 850.00 = 850.00
```

**Matching Sugerat:**
- Panou solar → Match cu "Solar Panel 300W" (80-90%)
- Inverter → Match cu "Inverter 5kW" (75-85%)
- Cablu solar → Creează nou sau match parțial (40-60%)
- Conector MC4 → Match înalt (85-95%)
- Structura → Probabil creează nou
- Tablou → Probabil creează nou

### Pentru sample_invoice_en.txt

**Date Extrase:**
```
Supplier: GREEN POWER SYSTEMS LTD
Invoice Number: INV-2024-042
Date: January 20, 2024
Total: 17,879.75 EUR
Status: PARSED

Items (8):
- Solar Panel 400W Monocrystalline
- Hybrid Inverter 8kW with Battery Support
- Solar Cable 4mm² Black UV Resistant
- MC4 Solar Connectors (Male + Female)
- DC Disconnect Switch 1000V 32A
- AC Circuit Breaker 40A 3-Phase
- Aluminum Mounting Rail 4.2m
- End Clamps and Mid Clamps Set
```

### Pentru sample_invoice.xml

**Date Extrase:**
```
Supplier: RENEWABLE TECH SRL
Invoice Number: XML-2024-015
Date: 2024-01-25
Total: 33,409.25 RON
VAT: 19%
Status: PARSED

Items (6):
- Complete XML structure parsed
- All fields extracted
- VAT breakdown available
- Customer details included
```

## 🔧 Probleme Comune și Soluții

### 1. Eroare 405 (Method Not Allowed)

**Cauză**: Server-ul nu a fost repornit după actualizare

**Soluție**:
```bash
sudo systemctl restart pvapp
# sau pentru dev:
# Ctrl+C și apoi repornește cu: uvicorn app.main:app --reload
```

### 2. Eroare 401 (Unauthorized)

**Cauză**: Nu ești autentificat sau token-ul a expirat

**Soluție**:
1. Logout
2. Login din nou
3. Încearcă upload-ul din nou

### 3. Eroare: "table invoice has no column named file_path"

**Cauză**: Baza de date nu e migrată

**Soluție**:
```bash
cd /opt/pvapp
./fix_database.sh
sudo systemctl restart pvapp
```

### 4. Nu se extrag articole

**Cauze posibile**:
- Format nerecunoscut
- Lipsesc coloane clare (Qty, Price)
- Text neclar sau prea complex

**Soluții**:
- Verifică că factura are o structură clară
- Asigură-te că articolele sunt în format tabel
- Încercă cu unul din fișierele de test mai întâi

### 5. Matching-ul e slab (sub 30%)

**Cauză**: Descrierile din factură diferă mult de cele din baza de date

**Soluții**:
- Creează materiale noi cu denumiri clare
- Folosește termeni standard (ex: "Solar Panel" nu "Panou PV")
- Include specificații (watt, dimensiuni) în nume

### 6. Nu văd butonul "Upload Invoice"

**Cauze**:
- Nu ești autentificat
- Cache-ul browser-ului e vechi
- Nu ai permisiuni

**Soluții**:
1. Refresh (Ctrl+F5)
2. Clear cache browser
3. Logout și login din nou
4. Verifică că ai rol ADMIN

## 💡 Sfaturi pentru Rezultate Bune

### Pentru Facturi Text (TXT)
1. **Structură clară**: Folosește tabele cu coloane aliniate
2. **Header-e vizibile**: "Supplier:", "Invoice #:", "Date:"
3. **Articole în tabel**: Coloane clare: Descriere, Cant, UM, Preț
4. **Total marcat**: Clar "TOTAL:" sau "Total:"

### Pentru Matching Bun
1. **Descrieri detaliate**: Include specificații (watt, dimensiuni)
2. **Termeni standard**: Folosește termeni din industrie
3. **Consistență**: Folosește aceleași denumiri în toate facturile
4. **Completează baza de date**: Adaugă materiale folosite frecvent

### Pentru Testare Eficientă
1. **Începe cu sample_invoice_ro.txt**: E cel mai simplu
2. **Testează fiecare funcție**: Upload → Extract → Match → Create → Confirm
3. **Verifică rezultatele**: Materials, Stock, Invoice details
4. **Încearcă scenarii reale**: După testele de bază, încarcă facturi reale

### Pentru Debugging
1. **Verifică logs**: `sudo journalctl -u pvapp -f`
2. **Folosește browser console**: F12 → Console pentru erori JavaScript
3. **Testează API direct**: Folosește `/docs` pentru API testing
4. **Verifică baza de date**: `sqlite3 /opt/pvapp/data/pvapp.db`

## 📊 Metrici de Succes

După testare completă, ar trebui să ai:

- ✅ **3 facturi** încărcate și procesate (ro, en, xml)
- ✅ **15-20 materiale** create sau mapate
- ✅ **20+ mișcări stoc** (dacă ai confirmat)
- ✅ **Inventar actualizat** pentru toate materialele
- ✅ **0 erori** în procesare
- ✅ **Matching >70%** pentru articole comune

## 🎓 Ce Urmează?

După ce testarea e completă:

1. **Încarcă facturi reale**: Încearcă cu facturi reale de la furnizori
2. **Optimizează matching-ul**: Adaugă mai multe materiale în baza de date
3. **Creează categorii**: Organizează materialele în categorii
4. **Monitorizează stocul**: Folosește alertele de stoc minim
5. **Generează rapoarte**: Folosește funcția de balance pentru proiecte

## 📞 Ajutor și Suport

Dacă întâmpini probleme:

1. **Documentație**:
   - `INVOICE_UPLOAD.md` - Ghid complet funcție
   - `TROUBLESHOOTING_UPLOAD.md` - Probleme și soluții
   - `DATABASE_MIGRATION.md` - Migrare bază de date

2. **Scripts utile**:
   - `./fix_database.sh` - Repară schema baza de date
   - `./update.sh` - Actualizează aplicația
   - `/opt/pvapp/backup.sh` - Backup bază de date

3. **Logs**:
   ```bash
   # Vezi logs aplicație
   sudo journalctl -u pvapp -f
   
   # Vezi ultimele 50 linii
   sudo journalctl -u pvapp -n 50
   ```

## ✅ Checklist Testare Completă

- [ ] Am pornit aplicația
- [ ] M-am autentificat cu succes
- [ ] Am încărcat sample_invoice_ro.txt
- [ ] Am validat extragerea datelor
- [ ] Am testat matching-ul materialelor
- [ ] Am creat materiale noi
- [ ] Am confirmat factura
- [ ] Am verificat mișcările stoc
- [ ] Am încărcat sample_invoice_en.txt
- [ ] Am încărcat sample_invoice.xml
- [ ] Am verificat toate materialele create
- [ ] Am verificat inventarul actualizat
- [ ] Toate funcțiile merg perfect! 🎉

---

**Succes la testare! 🌞**

Dacă totul merge bine, vei avea un sistem complet funcțional de management facturi cu procesare automată și actualizare stoc!
