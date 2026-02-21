# Sri Lanka Property Price Predictor & Forecaster

> **Machine Learning Assignment** — LightGBM Regression + SHAP Explainability + Economic Forecasting + React Frontend

A comprehensive machine learning application designed to estimate current property values and forecast future price trends in Sri Lanka (2026–2030) using real-world real estate data.

---

## 🏗️ Project Structure

```text
├── dataset/
│   ├── scrape_properties.py    # Multi-source web scraper (ikman.lk, LankaPropertyWeb)
│   └── properties_raw.csv      # Raw dataset (9,022 listings)
├── backend/
│   ├── main.py                 # FastAPI REST API (Predict & Forecast endpoints)
│   ├── requirements.txt        # Backend dependencies
│   ├── ml/                     # Machine Learning Pipeline
│   │   ├── 01_preprocessing.py # Data cleaning, City extraction, Quality tiering
│   │   ├── 02_train_evaluate.py# LightGBM training + Performance metrics
│   │   ├── 03_explainability.py# XAI: SHAP values & Feature importance
│   │   ├── 05_train_forecast.py# LSTM/Proph-style future price trend modeling
│   │   ├── artifacts/          # Trained models, encoders, and metrics JSON
│   │   └── figures/            # Training plots (Actual vs Pred, SHAP Beeswarm, etc.)
├── frontend/
│   ├── src/                    # React 18 + Mantine UI
│   │   ├── App.jsx             # Main logic + Tabbed Forecast auto-fill system
│   │   └── components/         # Modular UI (ShapChart, ForecastPlot, etc.)
│   └── package.json            # Frontend dependencies
└── docker-compose.yml          # Container orchestration for easy deployment
```

---

## 📊 Dataset & Feature Engineering

The model is trained on **9,022 listings** scraped from major Sri Lankan property portals.

| Feature Type       | Details                                                                              |
| ------------------ | ------------------------------------------------------------------------------------ |
| **Location**       | City-level granularity (**129 unique locations**) extracted from listing titles.     |
| **Property Type**  | Land, House, Apartment.                                                              |
| **Specifications** | Bedrooms, Bathrooms, Land Size (Perches).                                            |
| **Quality Tier**   | **New Feature**: Classifies listings into Standard, Modern, Luxury, or Super Luxury. |
| **Furnishing**     | Detects Unfurnished, Semi-Furnished, or Fully Furnished status.                      |

---

## 🤖 Algorithm — LightGBM

The core predictor uses **LightGBM**, a high-performance gradient boosting framework.

**Why LightGBM?**

- **Categorical Handling:** Efficiently manages 129+ location categories without one-hot encoding.
- **Speed:** 10–100x faster training than standard GBDT on tabular data.
- **Accuracy:** Leaf-wise growth allows for higher precision in complex real estate price distributions.

### Model Performance (Current Version)

- **Test R² (log-space):** 0.8492
- **Test MAE:** Rs. 11,592,928
- **Validation R²:** 0.8530

---

## 🔮 Future Forecasting (2026–2030)

The application includes an economics-aware forecasting engine that uses historical property trends combined with microeconomic signals to predict market shifts over the next 5 years.

**Features:**

- Automatic Investment Signal (Strong Buy, Hold, Sell).
- Regional Growth Analysis (District-specific multipliers).
- Integrated UX: Predict a current price and immediately switch to the Forecast tab to see its 5-year outlook auto-populated.

---

## 🔍 Explainability (XAI)

Every prediction is backed by **SHAP (SHapley Additive exPlanations)**.

- **SHAP Bar Charts:** Shows the global importance of features (Property Type is rank #1).
- **Individual Waterfall:** Explains exactly why a specific property was priced the way it was (e.g., "This property is Rs 2M higher because it is in Nugegoda").

---

## 🛠️ Setup & Execution

### 1. ML Pipeline

Generate models and artifacts:

```bash
cd backend/ml
pip install -r ../requirements.txt
python 01_preprocessing.py
python 02_train_evaluate.py
python 03_explainability.py
```

### 2. Backend (FastAPI)

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Frontend (Vite + React)

```bash
cd frontend
npm install
npm run dev
```

---

## 🛠️ Tech Stack

- **AI/ML:** LightGBM, SHAP, Scikit-Learn, Pandas.
- **Backend:** FastAPI, Pydantic, Uvicorn.
- **Frontend:** React 18, Vite, Mantine UI, Recharts, Lucide Icons.
- **DevOps:** Docker, Docker Compose.
