# 🌿 LankaTea Intelligence Yield Forecast

**Machine Learning Assignment** — De Zoysa L.K.L.K (214046N)

A state-of-the-art predictive system for Sri Lankan tea estates. This application uses LightGBM and XAI (SHAP) to forecast monthly harvest yields based on environmental and soil chemical profiles.

````

The system will be live at **http://localhost:3000** with pre-trained models.

### 💻 Local Development (Manual Setup)

If you prefer to run the services without Docker:

**1. Backend (FastAPI)**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Mac/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
````

**2. Frontend (React + Vite)**

```bash
cd frontend
npm install
npm run dev
```

---

## 🔬 Scientific Context

Tea cultivation in Sri Lanka relies on precise environmental triggers. This project transitions from chaotic market data to logical agricultural biological curves.

### Key Predictors (Features):

- **Meteorology**: Monthly Rainfall (mm) and Average Temperature (°C).
- **Soil Chemistry (NPK)**: Nitrogen, Phosphorus, and Potassium concentrations.
- **Estate Geography**: Elevation zones (High-grown, Mid-grown, Low-grown).
- **Management**: Fertilizer practicing and Drainage quality.

### Model Accuracy:

- **R² Score**: ~0.99 (Extremely high precision due to logical biological correlation).
- **MAE (Mean Absolute Error)**: ~0.02 Metric Tons per Hectare.

---

## 📁 Technical Architecture

```
ML-Assignment/
├── backend/
│   ├── main.py                    # FastAPI REST API
│   └── ml/
│       ├── 01_preprocessing.py    # Soil & Weather data normalization
│       ├── 02_train_evaluate.py   # LightGBM Yield Regressor
│       ├── 03_explainability.py   # SHAP driver analysis (XAI)
│       └── artifacts/             # Serialized models and encoders
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # "Green" themed Dashboard
│   │   └── components/            # Data entry and visualization components
└── dataset/
    └── tea_yield_historical_data.csv # Historical archive (TRI modeled)
```

---

## 🛠️ Performance Tuning (Optional)

To retrain the model with the latest dataset:

```bash
cd backend/ml
python 01_preprocessing.py
python 02_train_evaluate.py
python 03_explainability.py
```

Retraining updates the `artifacts/` folder used by the API.

---

```bash
# 1. Create network
docker network create lankatea-net

# 2. Run Backend
docker run -d --name backend --network lankatea-net -p 8000:8000 lkzoysa/lankatea-backend:latest

# 3. Run Frontend
docker run -d --name lankatea_frontend --network lankatea-net -p 3000:80 lkzoysa/lankatea-frontend:latest
```

---
