
---

## **1. Dokumentation und Benutzeranleitung**

Eine gut strukturierte und detaillierte Dokumentation erleichtert es sowohl Endbenutzern als auch Entwicklern, Ihr Projekt zu verstehen, zu nutzen und weiterzuentwickeln. Hier ist ein vollständiger Entwurf für die verschiedenen Unterpunkte:

### **1.1. Installation**

#### **1.1.1. Systemvoraussetzungen**

Stellen Sie sicher, dass Ihr System die folgenden Anforderungen erfüllt:

- **Betriebssystem:** Windows 10 oder höher, macOS 10.15 oder höher, Linux (Ubuntu 18.04 oder höher empfohlen)
- **Python:** Version 3.8 oder höher
- **Hardware:** Mindestens 4 GB RAM (empfohlen 8 GB für bessere Leistung)

#### **1.1.2. Schritt-für-Schritt Anleitung**

1. **Repository klonen:**

   ```bash
   git clone https://github.com/yourusername/OfferMee.git
   cd OfferMee
   ```

2. **Virtuelle Umgebung einrichten:**

   Es wird empfohlen, eine virtuelle Umgebung zu verwenden, um Abhängigkeiten zu isolieren.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Für Unix oder MacOS
   venv\Scripts\activate     # Für Windows
   ```

3. **Abhängigkeiten installieren:**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Selenium WebDriver einrichten:**

   - **ChromeDriver herunterladen:**
     Besuchen Sie [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads) und laden Sie die Version herunter, die Ihrer installierten Chrome-Version entspricht.
   
   - **ChromeDriver installieren:**
     Extrahieren Sie die heruntergeladene Datei und platzieren Sie den `chromedriver` im Verzeichnis `./scripts/` oder einem anderen Verzeichnis Ihrer Wahl. Aktualisieren Sie gegebenenfalls den Pfad in `selenium_utils.py`.

5. **Datenbank initialisieren:**

   Führen Sie das Skript `run_database.py` aus, um die Datenbank zu erstellen und mit Dummy-Daten zu füllen.

   ```bash
   python scripts/run_database.py
   ```

### **1.2. Konfiguration**

#### **1.2.1. Umgebungsvariablen**

Erstellen Sie eine `.env`-Datei im Stammverzeichnis des Projekts und fügen Sie die folgenden Variablen hinzu:

```env
# AI API KEYS
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_openai_model
GENAI_API_KEY=your_genai_api_key
GENAI_MODEL=your_genai_model

# EMAIL
SENDER_EMAIL=your_email@example.com
SENDER_PASSWORD=your_email_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=465
```

**Hinweise:**

- **Sicherheit:** Stellen Sie sicher, dass die `.env`-Datei in Ihrer `.gitignore` enthalten ist, um die Exposition sensibler Informationen zu verhindern.
- **API-Schlüssel:** Ersetzen Sie `your_openai_api_key` und `your_genai_api_key` mit Ihren tatsächlichen API-Schlüsseln.
- **E-Mail:** Geben Sie Ihre E-Mail-Adresse und Ihr Passwort an. Für Gmail müssen Sie möglicherweise ein App-spezifisches Passwort erstellen.

#### **1.2.2. Umgebungsvariablen Beschreibung**

| Variable            | Beschreibung                                              | Beispiel                        |
|---------------------|-----------------------------------------------------------|---------------------------------|
| `OPENAI_API_KEY`    | API-Schlüssel für OpenAI                                 | `sk-XXXXXXXXXXXXXXXXXXXX`        |
| `OPENAI_MODEL`      | Modellname für OpenAI                                     | `gpt-4`                         |
| `GENAI_API_KEY`     | API-Schlüssel für Google Generative AI                    | `AIzaSyXXXXXXXXXXXXXXXXXXXX`      |
| `GENAI_MODEL`       | Modellname für Google Generative AI                       | `gemini-1.5-flash`               |
| `SENDER_EMAIL`      | Absender-E-Mail-Adresse für das Versenden von Angeboten   | `your_email@example.com`        |
| `SENDER_PASSWORD`   | Passwort für die Absender-E-Mail                           | `your_email_password`           |
| `SMTP_SERVER`       | SMTP-Server-Adresse                                      | `smtp.gmail.com`                |
| `SMTP_PORT`         | SMTP-Server-Port (Standard: 465 für SSL)                 | `465`                            |

### **1.3. Nutzung**

#### **1.3.1. Starten des Dashboards**

Führen Sie das Dashboard mit folgendem Befehl aus:

```bash
python scripts/run_dashboard.py
```

Alternativ können Sie direkt `streamlit` verwenden:

```bash
streamlit run offermee/dashboard/app.py
```

#### **1.3.2. Dashboard-Funktionen**

Das Dashboard bietet mehrere Seiten zur Verwaltung und Nutzung von OfferMee:

1. **CV hinterlegen:**
   - Laden Sie Ihren Lebenslauf (PDF) hoch.
   - Extrahieren und speichern Sie Ihre Fähigkeiten und gewünschten Stundensatz.

2. **Standardangebotstemplate:**
   - Bearbeiten und speichern Sie Ihr Angebotstemplate.
   - Nutzen Sie Platzhalter für dynamische Daten.

3. **Projektsuche:**
   - Suchen Sie nach Projekten basierend auf Startdatum, Ort, Stundensatz und gewünschten Fähigkeiten.

4. **Scrapper:**
   - Konfigurieren und starten Sie Scraper für verschiedene Plattformen (z.B. FreelancerMap).
   - Speichern und verwalten Sie gefundene Projekte.

5. **Projektübersicht:**
   - Anzeigen und bewerten Sie gefundene Projekte.
   - Erstellen und senden Sie Angebote an potenzielle Kunden.

6. **Angebotshistorie:**
   - Verfolgen Sie den Status Ihrer gesendeten Angebote.
   - Überprüfen Sie Kommentare und Reaktionen von Kunden.

#### **1.3.3. Nutzung der Scraper**

Um Projekte von FreelancerMap zu scrapen, navigieren Sie zur Seite **Scrapper** im Dashboard und konfigurieren Sie die Suchparameter:

- **Plattform auswählen:** Wählen Sie die gewünschte Plattform (z.B. FreelancerMap).
- **Suchbegriffe:** Geben Sie relevante Keywords ein (z.B. "Python Developer").
- **Ort:** Optional, geben Sie den gewünschten Standort ein.
- **Länder auswählen:** Wählen Sie die Länder, in denen Sie Projekte suchen möchten.
- **Contract Typ auswählen:** Wählen Sie die Art der Verträge (z.B. Contractor, Festanstellung).
- **Site auswählen:** Wählen Sie die Arbeitsform (Remote, Onsite, Hybrid).
- **Max. Seitenanzahl:** Geben Sie die maximale Anzahl der Seiten an, die durchsucht werden sollen.
- **Max. Projekte:** Legen Sie die maximale Anzahl der zu scrappenden Projekte fest.
- **Min. Stundensatz (€):** Geben Sie den minimalen Stundensatz an.
- **Max. Stundensatz (€):** Geben Sie den maximalen Stundensatz an.

Klicken Sie auf **Scraping starten**, um den Prozess zu initiieren.

### **1.4. Beitragen**

Wir begrüßen Beiträge von der Community! Folgen Sie den untenstehenden Richtlinien, um einen reibungslosen Beitrag zu gewährleisten.

#### **1.4.1. Beiträge einreichen**

1. **Forken Sie das Repository:**

   Klicken Sie auf den **Fork**-Button oben rechts auf der [GitHub-Seite von OfferMee](https://github.com/yourusername/OfferMee).

2. **Erstellen Sie einen neuen Branch:**

   ```bash
   git checkout -b feature/NeueFunktion
   ```

3. **Nehmen Sie Ihre Änderungen vor:**

   Bearbeiten Sie den Code, fügen Sie Funktionen hinzu oder beheben Sie Fehler.

4. **Committen Sie Ihre Änderungen:**

   ```bash
   git add .
   git commit -m "Beschreibung der Änderungen"
   ```

5. **Pushen Sie Ihren Branch:**

   ```bash
   git push origin feature/NeueFunktion
   ```

6. **Erstellen Sie einen Pull Request:**

   Gehen Sie zurück zu Ihrem Fork auf GitHub und klicken Sie auf **Compare & pull request**. Beschreiben Sie Ihre Änderungen detailliert.

#### **1.4.2. Code of Conduct**

Bitte halten Sie sich an unseren [Code of Conduct](CODE_OF_CONDUCT.md), um eine positive und respektvolle Community zu gewährleisten.

#### **1.4.3. Pull-Request-Richtlinien**

- **Beschreibung:** Geben Sie eine klare und prägnante Beschreibung Ihrer Änderungen.
- **Tests:** Stellen Sie sicher, dass alle neuen Funktionen getestet sind und bestehende Tests bestehen.
- **Dokumentation:** Aktualisieren Sie die Dokumentation entsprechend Ihren Änderungen.
- **Formatierung:** Folgen Sie den bestehenden Code-Formatierungsrichtlinien.

### **1.5. Lizenz**

**OfferMee** ist unter der [Mozilla Public License Version 2.0 (MPL 2.0)](LICENSE) lizenziert. Siehe die Lizenzdatei für weitere Informationen.

#### **Kurzfassung der Lizenzbedingungen:**

- **Freie Nutzung:** Sie dürfen das Projekt kostenlos nutzen, ändern und verteilen.
- **Quellcode Offenlegung:** Änderungen am Quellcode müssen ebenfalls unter der MPL 2.0 lizenziert werden.
- **Haftungsausschluss:** Das Projekt wird ohne jegliche Garantie bereitgestellt.

---

## **2. Deployment**

Die Bereitstellung von **OfferMee** kann auf verschiedene Weisen erfolgen, abhängig von Ihren Anforderungen und Ressourcen. Hier sind detaillierte Schritte und Optionen für das Deployment.

### **2.1. Lokale Nutzung**

Für Entwickler oder Nutzer, die **OfferMee** lokal ausführen möchten, folgen Sie der Installation und Konfiguration in **Punkt 7**. Stellen Sie sicher, dass alle Abhängigkeiten installiert und die `.env`-Datei korrekt eingerichtet ist.

#### **2.1.1. Starten der Anwendung**

- **Dashboard starten:**

  ```bash
  python scripts/run_dashboard.py
  ```

- **Scraper ausführen:**

  ```bash
  python scripts/run_scraper.py
  ```

### **2.2. Cloud Deployment**

Um **OfferMee** online zugänglich zu machen, können Sie verschiedene Cloud-Dienste nutzen. Hier sind einige beliebte Optionen:

#### **2.2.1. Heroku**

**Schritte:**

1. **Heroku CLI installieren:**
   
   Folgen Sie der Anleitung auf [Heroku Dev Center](https://devcenter.heroku.com/articles/heroku-cli).

2. **Anmelden bei Heroku:**

   ```bash
   heroku login
   ```

3. **Neues Heroku-Projekt erstellen:**

   ```bash
   heroku create offermee-dashboard
   ```

4. **Buildpacks hinzufügen:**

   Heroku benötigt ein Buildpack für Python.

   ```bash
   heroku buildpacks:set heroku/python
   ```

5. **Procfile erstellen:**

   Erstellen Sie eine `Procfile` im Stammverzeichnis mit folgendem Inhalt:

   ```procfile
   web: streamlit run offermee/dashboard/app.py --server.port=$PORT
   ```

6. **Abhängigkeiten und Dateien bereitstellen:**

   Stellen Sie sicher, dass alle notwendigen Dateien (einschließlich `requirements.txt` und `Procfile`) im Repository enthalten sind.

7. **Änderungen committen und pushen:**

   ```bash
   git add .
   git commit -m "Prepare for Heroku deployment"
   git push heroku main
   ```

8. **Umgebungsvariablen setzen:**

   Setzen Sie die erforderlichen Umgebungsvariablen auf Heroku.

   ```bash
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set SENDER_EMAIL=your_email@example.com
   heroku config:set SENDER_PASSWORD=your_email_password
   # Weitere Variablen nach Bedarf
   ```

9. **Anwendung starten:**

   Heroku sollte die Anwendung automatisch starten. Sie können die URL Ihres Dashboards über das Heroku-Dashboard oder die CLI abrufen.

#### **2.2.2. AWS (Amazon Web Services)**

**Optionen:**

- **EC2 (Elastic Compute Cloud):** Virtuelle Server für maximale Kontrolle.
- **Elastic Beanstalk:** Plattform-as-a-Service für einfaches Deployment.
- **AWS Lambda:** Serverless Computing für skalierbare Anwendungen.

**Schritte für Elastic Beanstalk:**

1. **AWS CLI installieren:**

   Folgen Sie der Anleitung auf [AWS CLI Installation](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html).

2. **Anmelden und konfigurieren:**

   ```bash
   aws configure
   ```

3. **Elastic Beanstalk Umgebung erstellen:**

   ```bash
   eb init -p python-3.8 offermee-dashboard
   eb create offermee-env
   ```

4. **Deployment:**

   ```bash
   eb deploy
   ```

5. **Umgebungsvariablen setzen:**

   Über das AWS Management Console oder die CLI.

   ```bash
   eb setenv OPENAI_API_KEY=your_openai_api_key SENDER_EMAIL=your_email@example.com SENDER_PASSWORD=your_email_password
   ```

6. **Anwendung überwachen:**

   Nutzen Sie die AWS-Konsole, um Logs und Status zu überwachen.

#### **2.2.3. DigitalOcean**

**Schritte:**

1. **Droplet erstellen:**

   Wählen Sie ein geeignetes Image (z.B. Ubuntu 20.04).

2. **SSH-Zugang einrichten:**

   ```bash
   ssh root@your_droplet_ip
   ```

3. **Abhängigkeiten installieren:**

   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv
   ```

4. **Repository klonen und einrichten:**

   ```bash
   git clone https://github.com/yourusername/OfferMee.git
   cd OfferMee
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Supervisor oder systemd für Prozessmanagement einrichten:**

   Beispiel mit **systemd**:

   - Erstellen Sie eine Service-Datei:

     ```bash
     sudo nano /etc/systemd/system/offermee.service
     ```

     Inhalt:

     ```ini
     [Unit]
     Description=OfferMee Dashboard
     After=network.target

     [Service]
     User=root
     WorkingDirectory=/root/OfferMee
     ExecStart=/root/OfferMee/venv/bin/streamlit run offermee/dashboard/app.py --server.port=80
     Restart=always

     [Install]
     WantedBy=multi-user.target
     ```

   - Service starten und aktivieren:

     ```bash
     sudo systemctl start offermee
     sudo systemctl enable offermee
     ```

6. **Firewall konfigurieren:**

   ```bash
   sudo ufw allow 80
   sudo ufw enable
   ```

7. **Domain konfigurieren (optional):**

   Richten Sie Ihre Domain auf die IP-Adresse des Droplets ein und konfigurieren Sie ggf. SSL-Zertifikate mit **Let's Encrypt**.

### **2.3. Containerisierung mit Docker**

Die Nutzung von Docker ermöglicht eine konsistente Umgebung für die Anwendung und erleichtert das Deployment.

#### **2.3.1. Dockerfile erstellen**

Erstellen Sie eine `Dockerfile` im Stammverzeichnis:

```dockerfile
# Dockerfile

FROM python:3.9-slim

# Arbeitsverzeichnis festlegen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Abhängigkeiten kopieren
COPY requirements.txt .

# Abhängigkeiten installieren
RUN pip install --no-cache-dir -r requirements.txt

# Restliche Dateien kopieren
COPY . .

# Port freigeben
EXPOSE 8501

# Startbefehl
CMD ["streamlit", "run", "offermee/dashboard/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### **2.3.2. Docker-Image bauen**

```bash
docker build -t offermee-dashboard .
```

#### **2.3.3. Docker-Container starten**

```bash
docker run -d -p 8501:8501 --env-file .env offermee-dashboard
```

**Hinweise:**

- **Umgebungsvariablen:** Stellen Sie sicher, dass die `.env`-Datei korrekt ist und die erforderlichen Variablen enthält.
- **Persistente Daten:** Für die Datenbank können Sie Volumes verwenden, um Daten zwischen Neustarts zu behalten.

#### **2.3.4. Docker Compose (Optional)**

Für komplexere Setups können Sie **Docker Compose** verwenden.

1. **`docker-compose.yml` erstellen:**

   ```yaml
   version: '3.8'

   services:
     offermee-dashboard:
       build: .
       ports:
         - "8501:8501"
       env_file:
         - .env
       volumes:
         - .:/app
   ```

2. **Container mit Docker Compose starten:**

   ```bash
   docker-compose up -d
   ```

### **2.4. Continuous Integration/Continuous Deployment (CI/CD)**

Automatisieren Sie den Build- und Deployment-Prozess mit CI/CD-Tools wie **GitHub Actions**, **GitLab CI**, oder **Jenkins**.

#### **2.4.1. Beispiel für GitHub Actions**

Erstellen Sie eine Datei `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Heroku

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: "your-heroku-app-name"
        heroku_email: "your-email@example.com"
```

**Hinweise:**

- **Heroku API Key:** Fügen Sie Ihren Heroku API Key als Geheimnis (`HEROKU_API_KEY`) in den Repository-Einstellungen hinzu.
- **Anwendungsname:** Ersetzen Sie `your-heroku-app-name` durch den Namen Ihrer Heroku-App.

---
