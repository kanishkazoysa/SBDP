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
docker-compose up --build -d

# 3. Open in browser
#    Frontend:  http://localhost:3000
#    API Docs:  http://localhost:8000/docs
```

That's it! The app will be running at **http://localhost:3000**

```bash
# To stop
docker-compose down

# To restart
docker-compose up -d
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

## 🛠️ Tech Stack

| Layer          | Technology              | Purpose                                              |
| -------------- | ----------------------- | ---------------------------------------------------- |
| **ML Model**   | LightGBM                | Gradient-boosted decision trees for price prediction |
| **XAI**        | SHAP TreeExplainer      | Real-time feature importance per prediction          |
| **Backend**    | FastAPI + Uvicorn       | REST API serving model predictions                   |
| **Frontend**   | React 18 + Vite         | Interactive dashboard                                |
| **UI**         | Mantine v7 + Recharts   | Components & visualization                           |
| **Deployment** | Docker + Docker Compose | Containerized deployment                             |

---

## 📊 Model Performance

| Metric | Train     | Validation | Test      |
| ------ | --------- | ---------- | --------- |
| R²     | 0.8390    | 0.7793     | 0.8056    |
| MAE    | Rs. 10.2M | Rs. 11.9M  | Rs. 11.2M |
| RMSE   | Rs. 24.2M | Rs. 27.6M  | Rs. 25.3M |

---

## 🔗 API Endpoints

| Method | Endpoint   | Description                                      |
| ------ | ---------- | ------------------------------------------------ |
| GET    | `/meta`    | Returns locations, property types, model metrics |
| POST   | `/predict` | Predicts price + SHAP values for given property  |
| GET    | `/docs`    | Swagger UI (interactive API documentation)       |

### Example Prediction Request

```json
POST /predict
{
  "property_type": "House",
  "location": "Colombo",
  "bedrooms": 3,
  "bathrooms": 2,
  "land_size_perches": 10,
  "quality_tier": 1,
  "is_furnished": 0
}
```

---

## 📝 Generate PDF Report

```bash
pip install fpdf2
python generate_report.py
# Output: ML_Assignment_Report_214046N.pdf
```
