
# INSTALLATION AND SETUP

## 1. Documentation and User Guide

A clear and detailed documentation makes it easier for both end users and developers to understand, use, and further develop your project. Below is a comprehensive outline covering the main aspects.

---

### 1.1. Installation

#### 1.1.1. System Requirements

- **Operating System:** Windows 10 or later, macOS 10.15 or later, or a recent Linux distribution (e.g., Ubuntu 18.04 or higher recommended)
- **Python:** Version 3.8 or above
- **Hardware:** At least 4 GB RAM (8 GB recommended for better performance)

#### 1.1.2. Step-by-Step Guide

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/OfferMee.git
   cd OfferMee
   ```

2. **Create a Virtual Environment (Recommended)**:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Unix or MacOS
   venv\Scripts\activate     # For Windows
   ```

3. **Install Dependencies**:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **(Optional) Set up Selenium WebDriver** (if you intend to use scraping features):
   - **Download ChromeDriver**:  
     Visit [ChromeDriver Downloads](https://sites.google.com/a/chromium.org/chromedriver/downloads) and ensure you match the version to your installed Chrome browser.
   - **Place ChromeDriver**:  
     Extract the driver and place it in `./scripts/` or another chosen location. Update any paths in `selenium_utils.py` if required.

5. **(Optional) Initialize a Database**:
   - Run the script `scripts/run_database.py` if the project requires a local database initialization:
     ```bash
     python scripts/run_database.py
     ```

---

### 1.2. Configuration

#### 1.2.1. Environment Variables

**Only two environment variables are used** in the current setup:

- `OE_PUK` – Path to your RSA public key
- `OE_PRK` – Path to your RSA private key

These variables can be set in your system environment or by creating a local `.env` file (and using a package such as `python-dotenv` to load them). 

An example `.env`:

```bash
# RSA Key Paths
OE_PUK=/path/to/public_key.pem
OE_PRK=/path/to/private_key.pem
```

> Make sure your `.env` file is listed in `.gitignore` to avoid exposing sensitive data in version control.

#### 1.2.2. Local `.settings.json`

All other configuration data is stored in an encrypted local settings file (by default referred to here as `.settings.json`). Once a user logs in, these settings are loaded and used by the system. The kind of information typically stored in `.settings.json` includes (but is not limited to):

- **Email**  
  - `email_address` (sender email)  
  - `email_password`  
  - `smtp_server` (e.g., `smtp.gmail.com`)  
  - `smtp_port` (e.g., `465` for SSL)  
  - `receiver_email` (if different from sender)  
  - `receiver_password`  
  - `receiver_server` (IMAP server, e.g. `imap.gmail.com`)  
  - `receiver_port`  

- **RFP Filtering**  
  - `rfp_mailbox` (name of the mailbox/folder to watch for RFPs)  
  - `rfp_email_subject_filter` (e.g., `RFP`)  
  - `rfp_email_sender_filter` (sender filter for RFP emails)  

- **AI Families**  
  - `ai_families` (a dictionary defining various AI model configurations and API keys)  
  - `ai_selected_family` (which AI family is currently selected)

- **User Profile**  
  - `first_name`, `last_name`  
  - Other personal or project-specific fields

> **Note:** The `.settings.json` file is typically encrypted with RSA using your `OE_PUK` and `OE_PRK`. Access to these keys is crucial for decrypting/encrypting this file.

---

### 1.3. Usage

#### 1.3.1. Starting the Dashboard

You can start the Streamlit dashboard with:

```bash
python scripts/run_dashboard.py
```

Alternatively, run Streamlit directly:

```bash
streamlit run offermee/dashboard/app.py
```

#### 1.3.2. Dashboard Features

1. **Manage CV**  
   - Upload and parse your resume (PDF).
   - Extract and store skills and desired hourly rate.

2. **Standard Offer Template**  
   - Edit and save a default offer template.
   - Use placeholders for dynamic data.

3. **Project Search**  
   - Search for projects by start date, location, hourly rate, and required skills.

4. **Scrapper**  
   - Configure and launch scrapers for various platforms (e.g. FreelancerMap).
   - Save and manage found projects.

5. **Project Overview**  
   - View and evaluate scraped or incoming projects.
   - Create and send offers to potential clients.

6. **Offer History**  
   - Track the status of your sent offers.
   - Check customer comments and responses.

#### 1.3.3. Using Scrapers

To scrape projects from FreelancerMap, navigate to the **Scrapper** page in the dashboard and configure the parameters:

- **Platform**: e.g., FreelancerMap  
- **Search Terms**: e.g., "Python Developer"  
- **Location**: optional  
- **Countries**: to filter by country  
- **Contract Type**: e.g. Contractor, Permanent, etc.  
- **Site**: Remote, Onsite, or Hybrid  
- **Max Pages**: how many pages to scan  
- **Max Projects**: maximum number of projects to scrape  
- **Min Hourly Rate (€)**: minimum hourly rate  
- **Max Hourly Rate (€)**: maximum hourly rate  

Click **Start Scraping** to begin.

---

### 1.4. Contributing

We welcome contributions from the community! Follow the guidelines below to ensure a smooth contribution process.

#### 1.4.1. Submitting Contributions

1. **Fork the Repository**  
   Click the **Fork** button in the top-right corner on [GitHub](https://github.com/yourusername/OfferMee).

2. **Create a New Branch**  
   ```bash
   git checkout -b feature/NewFeature
   ```

3. **Make Your Changes**  
   Add new features or fix bugs.

4. **Commit Your Changes**  
   ```bash
   git add .
   git commit -m "Describe your changes"
   ```

5. **Push Your Branch**  
   ```bash
   git push origin feature/NewFeature
   ```

6. **Open a Pull Request**  
   In your GitHub fork, click on **Compare & pull request** and provide a detailed description.

#### 1.4.2. Code of Conduct

Please follow our [Code of Conduct](CODE_OF_CONDUCT.md) to foster a positive community environment.

#### 1.4.3. Pull Request Guidelines

- **Description**: Provide a clear and concise description of your changes.
- **Tests**: Ensure any new features include tests, and that all existing tests pass.
- **Documentation**: Update the documentation if your changes affect usage or features.
- **Formatting**: Match the existing code style and formatting.

---

### 1.5. License

**OfferMee** is licensed under the [Mozilla Public License Version 2.0 (MPL 2.0)](LICENSE). See the license file for further information.

**Summary**:

- **Open Usage**: You may freely use, modify, and distribute this software.
- **Source Code Disclosure**: Modifications must also be made available under MPL 2.0.
- **Disclaimer**: Provided without warranty of any kind.

---

## 2. Deployment

You can deploy **OfferMee** in various ways depending on your requirements and available resources. Below are detailed deployment steps and options.

### 2.1. Local Usage

For developers or users wanting to run **OfferMee** locally, follow the installation steps in [1.1](#11-installation). Ensure all dependencies are installed and that your environment variables (`OE_PUK`, `OE_PRK`) are set. Make sure your `.settings.json` is properly configured (or generated via the application upon login).

**Starting the Application**:

- **Dashboard**:
  ```bash
  python scripts/run_dashboard.py
  ```
- **Scraper**:
  ```bash
  python scripts/run_scraper.py
  ```
  *(Only needed if you are actively scraping projects.)*

### 2.2. Cloud Deployment

Common platforms include Heroku, AWS (EC2, Elastic Beanstalk), DigitalOcean, etc. Each requires environment configuration for `OE_PUK` and `OE_PRK`, plus hosting of the application code. Because all other settings are in `.settings.json`, you’ll need to manage that file (and its encryption keys) accordingly.

### 2.3. Containerization with Docker

1. **Dockerfile**  
   Create a `Dockerfile` in the repository root that installs dependencies, copies source files, and exposes the relevant port (e.g., 8501 for Streamlit).

2. **Build**  
   ```bash
   docker build -t offermee-dashboard .
   ```
3. **Run**  
   ```bash
   docker run -d -p 8501:8501 -e OE_PUK=/path/to/public_key.pem -e OE_PRK=/path/to/private_key.pem offermee-dashboard
   ```
   Make sure the `.settings.json` is present inside the container or mounted as a volume, depending on your workflow.

4. **(Optional) Docker Compose**  
   You can use `docker-compose.yml` for multi-container setups or more complex configurations.

### 2.4. Continuous Integration/Continuous Deployment (CI/CD)

Automate build, test, and deployment workflows with tools like GitHub Actions, GitLab CI, or Jenkins. The main environment variables you must supply are `OE_PUK` and `OE_PRK` so that your CI/CD pipeline can properly encrypt/decrypt local settings if needed.

---
