# Flask + Vue Template

> A minimal, ready-to-use template for building full-stack apps using Flask (Python) and Vue 3 (Vite).

---

## 🚀 Project Overview

This repository provides a clean structure for starting new projects with:

- ⚙️ Flask for the backend (API)
- 🌐 Vue 3 + Vite for the frontend (UI)
- 📦 Virtual Environment support (Windows)
- 🧰 Optional setup script (`setup.ps1`) for quick initialization

---

## 🧱 Project Structure

```bash
project-root/
│
├── backend/             # Flask app
│   ├── app/             # Application package (routes, models, etc.)
│   ├── config.py        # App configuration
│   ├── main.py          # Entry point
│   └── requirements.txt # Backend dependencies
│
├── frontend/            # Vue 3 application
│   ├── src/             # Vue components and assets
│   ├── index.html       # App HTML entry point
│   └── package.json     # Frontend dependencies
│
├── setup.ps1            # Windows setup script
└── README.md
```

---

## 📥 How to Use this Template

### ✅ Option 1: Use as a GitHub Template

1. Click **"Use this template"** on the top-right of the repo page
2. Clone your new repo:
   ```bash
   git clone https://github.com/YOUR_USERNAME/YOUR_PROJECT_NAME.git
   cd YOUR_PROJECT_NAME
   ```

---

## ⚙️ Setup Instructions

### 🔄 Option A: Auto Setup (Windows Only)

> ⚠️ Requires PowerShell + Python + Node.js

Run the setup script:
```powershell
./setup.ps1
```
This will:
- Create a Python virtual environment named `venv`
- Install backend requirements
- Install frontend dependencies
- Run database migration
- Start the backend and frontend

### 🛠️ Option B: Manual Setup

#### Backend (Flask)
```bash
python -m venv venv
./venv/Scripts/activate  # For Windows
pip install -r backend/requirements.txt
cd backend
flask db upgrade
python main.py
```

#### Frontend (Vue 3)
```bash
cd frontend
npm install
npm run dev
```

---

## 🔍 Testing the Setup

Once both backend and frontend are running:
- Open your browser at: `http://localhost:5173/`
- You should see a message fetched from the Flask API (`/api/`)

---

## 🧾 License

MIT – Use, modify, and distribute freely.

