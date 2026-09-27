# 🌐 Zoho Deluge AI Assistant & Enterprise ERP

An enterprise-grade Developer ERP and AI Copilot purpose-built for **Zoho Creator**, **Deluge Scripting**, HTML/CSS, and Client-Side JavaScript. Powered by **Meta Llama 3 8B** (`llama3:8b`) and Retrieval-Augmented Generation (RAG) with adaptive markdown chunking and ChromaDB.

Designed with a high-contrast Corporate ERP design system, Role-Based Access Control (RBAC), lazy-loaded documentation, automated scrapers, and advanced system orchestration.

---

## 🚀 Key Features

- **⚡ Optimized Llama 3 8B Engine**: Pre-configured with low-latency inference parameters (`llama3:8b`, temperature `0.2`, context window `4096`, max tokens `1536`) to deliver rapid code generation without lagging.
- **🛡️ Rigid Deluge Syntax Guardrails**: Explicitly trained to enforce Zoho Deluge syntax rules (strict data types, `list.add()`, `map.put()`, no `while` loops, strict API limits).
- **🔒 Enterprise RBAC Login**:
  - **Administrator (`admin`)**: Full system access to all ERP modules, terminal runner, vector indexing, scheduler, and model settings.
  - **Developer (`developer`)**: Focused access strictly restricted to the Deluge AI Assistant copilot.
- **📚 On-Demand Documentation**: Lazy-loaded, memory-cached documentation viewer under *Operations & Data* preventing high memory spikes or browser crashes on large files.
- **🛠️ Centralized Admin & Settings**:
  - Model hyperparameter tuning & diagnostics.
  - CMD-equivalent CLI execution & system diagnostics.
  - Vector database query & adaptive chunking controls.
  - Document & syntax injection directly into vector memory.
- **☁️ Streamlit Community Cloud Ready**: Zero Docker dependencies, lightweight `requirements.txt`, clean `.gitignore` preventing GitHub file-limit errors, and seamless support for remote Ollama endpoints via Streamlit Secrets.

---

## 👥 Default User Credentials

| Username | Password | Role | Permissions |
| :--- | :--- | :--- | :--- |
| `admin` | `admin123` | **Enterprise Admin** | Full access to Dashboard, AI Assistant, Documentation, Automation Scheduler, and Settings & Admin |
| `developer` | `dev123` | **Developer** | Limited access restricted exclusively to the **Deluge AI Assistant** |

---

## 📂 Project Structure

```text
Zoho_AI_Assistant/
│
├── App.py                     # Main application entry point & RBAC router
├── auth.py                    # Role-Based Access Control & session state
├── vector_setup.py            # Vector database engine & adaptive chunking
├── scraper_manager.py         # Documentation crawler & changelog sync
├── requirements.txt           # Python dependencies optimized for Streamlit Cloud
├── .gitignore                 # GitHub exclusion rules (filters out large DB & binary files)
│
├── .streamlit/
│   ├── config.toml            # Corporate ERP theme & server settings
│   └── secrets.toml.example   # Example template for remote Ollama host secrets
│
├── views/
│   ├── dashboard.py           # Minimalist ERP Dashboard & system metrics
│   ├── assistant.py           # Deluge AI Assistant with Llama 3 8B copilot
│   ├── documentation.py       # On-demand, lazy-loaded Zoho Deluge documentation
│   ├── scheduler.py           # Scraping automation & scheduled tasks
│   └── admin_settings.py      # Consolidated Settings & Admin panel
│
└── data/
    └── zoho_deluge_all_docs.md # Complete Zoho Deluge documentation knowledge base
```

---

## 💻 Local Quickstart

### 1. Prerequisites
- **Python 3.10+**
- **Ollama** installed and running locally ([ollama.com](https://ollama.com))

### 2. Pull the Llama 3 8B Model
```bash
ollama pull llama3:8b
ollama pull nomic-embed-text
```

### 3. Clone & Install Dependencies
```bash
git clone https://github.com/<your-username>/zoho-deluge-ai-assistant.git
cd zoho-deluge-ai-assistant

python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the Streamlit Application
```bash
streamlit run App.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser and sign in using `admin` / `admin123`.

---

## ☁️ Streamlit Community Cloud Deployment Guide

Follow these steps to deploy this repository to **Streamlit Community Cloud** ([share.streamlit.io](https://share.streamlit.io)):

### Step 1: Initialize Git and Push to GitHub

> **Note**: Local vector databases (`chroma_db/`) contain binary SQLite indexes exceeding GitHub's 100MB limit. The `.gitignore` automatically excludes them.

```bash
git init
git add .
git commit -m "Initial commit: Zoho Deluge AI Assistant with Llama 3 8B"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo-name>.git
git push -u origin main
```

### Step 2: Deploy on Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with your GitHub account.
2. Click **New app**.
3. Select your repository: `<your-username>/<your-repo-name>`.
4. Set the **Main file path** to: `App.py`.
5. Click **Advanced settings...**.

### Step 3: Configure Ollama Remote Endpoint (Secrets)
Because Streamlit Community Cloud runs inside a hosted container, it cannot access your local machine's `localhost:11434` without a public tunnel or cloud LLM host.

In the **Secrets** section of the Streamlit deployment settings, enter:
```toml
OLLAMA_HOST = "https://your-remote-ollama-host.com"
```

#### Tunneling Options for Local Ollama:
If you are running Ollama on your local machine / GPU workstation and want the Cloud app to use it:
- **Cloudflare Tunnel**: `cloudflared tunnel --url http://localhost:11434`
- **ngrok**: `ngrok http 11434 --host-header="localhost:11434"`
- **VPS / Cloud Instance**: Deploy Ollama on AWS, RunPod, or DigitalOcean and provide the public URL.

Click **Deploy**!

---

## ⚙️ Model Performance & Optimization Settings

The application defaults to **Meta Llama 3 8B** with the following optimized parameters:

| Parameter | Default Value | Purpose |
| :--- | :--- | :--- |
| **Model** | `llama3:8b` | Fast token generation and state-of-the-art coding performance |
| **Temperature** | `0.2` | Minimal hallucination; strictly produces valid Deluge code |
| **Context Window (`num_ctx`)** | `4096` | Low latency response times while fitting rich Deluge reference docs |
| **Max Tokens (`num_predict`)** | `1536` | Prevents runaway generations; speeds up TTFT (Time to First Token) |
| **Repetition Penalty** | `1.15` | Suppresses repetitive loop patterns common in code generation |

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
