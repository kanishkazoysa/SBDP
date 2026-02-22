# 🏠 Sri Lanka Property Price Prediction

**Machine Learning Assignment** — De Zoysa L.K.L.K (214046N)

A full-stack ML application that predicts Sri Lankan property prices using LightGBM with real-time SHAP explainability.

---

## 🚀 Quick Start (Docker — Recommended)

**Only requirement: [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed**

No Python, Node.js, or any other setup needed!

```bash
# 1. Clone or extract the project
cd ML-Assignment

# 2. Build and start everything (first time takes ~3 minutes)
docker compose up --build -d

# 3. Open in browser
#    Frontend:  http://localhost:3000
#    API Docs:  http://localhost:8000/docs
```

That's it! The app will be running at **http://localhost:3000**

```bash
# To stop
docker compose down

# To restart
docker compose up -d
```

---

## 🛠️ Manual Setup (Without Docker)

If you prefer running locally without Docker:

### Prerequisites

- Python 3.11+
- Node.js 18+
- pip

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

The backend starts at http://localhost:8000

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend starts at http://localhost:5173

### 3. Re-train the Model (Optional)

The trained model is already included in `backend/ml/artifacts/`. If you want to retrain:

```bash
cd backend/ml
python 01_preprocessing.py    # Clean raw data
python 02_train_evaluate.py   # Train LightGBM model
python 03_explainability.py   # Generate SHAP analysis
```

---

## 📁 Project Structure

```
ML-Assignment/
├── backend/
│   ├── main.py                    # FastAPI REST API
│   ├── requirements.txt           # Python dependencies
│   ├── Dockerfile                 # Backend container
│   └── ml/
│       ├── 01_preprocessing.py    # Data cleaning & feature engineering
│       ├── 02_train_evaluate.py   # LightGBM training & evaluation
│       ├── 03_explainability.py   # SHAP explainability analysis
│       └── artifacts/             # Trained model & encoders (pre-built)
│           ├── lgbm_model.pkl     # Trained LightGBM model
│           ├── label_encoders.pkl # Categorical encoders
│           ├── feature_info.json  # Feature metadata
│           ├── metrics.json       # Model performance metrics
│           └── shap_importance.json
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Main application
│   │   └── components/            # React components
│   ├── Dockerfile                 # Frontend container (nginx)
│   ├── nginx.conf                 # Production proxy config
│   └── package.json
├── dataset/
│   └── properties_raw.csv         # Raw scraped dataset (13,497 records)
├── notebook/
│   └── ML_Property_Price_Prediction.ipynb  # Jupyter notebook (with outputs)
├── report_assets/                 # Figures for the PDF report
├── generate_report.py             # Generates the PDF report
├── docker-compose.yml             # One-command deployment
└── README.md
```

---
