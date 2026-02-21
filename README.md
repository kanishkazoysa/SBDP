# Sri Lanka Intercity Bus Delay Prediction

> Machine Learning Assignment — LightGBM + SHAP + React Frontend

Predicts whether an SLTB / private bus on major Colombo intercity routes will arrive
**On Time**, **Slightly Delayed** (11–30 min), or **Heavily Delayed** (>30 min).

---

## Project Structure

```
├── dataset/                  Raw dataset (500 records, 2024)
├── ml/                       Machine learning pipeline
│   ├── 01_preprocessing.py   EDA + feature encoding + train/val/test split
│   ├── 02_train_evaluate.py  LightGBM training, GridSearchCV, evaluation
│   ├── 03_explainability.py  SHAP, LIME, and Partial Dependence Plots
│   ├── figures/              20 saved plots (EDA, model, XAI)
│   └── requirements.txt
├── backend/                  FastAPI REST API
│   ├── main.py               POST /predict endpoint
│   ├── artifacts/            Trained model + preprocessed data
│   └── requirements.txt
└── frontend/                 React (Vite) web application
    ├── src/
    │   ├── App.jsx
    │   └── components/
    │       ├── PredictionForm.jsx
    │       ├── PredictionResult.jsx
    │       └── ShapChart.jsx
    └── package.json
```

---

## Dataset

| Property | Value |
|---|---|
| Records | 500 bus trips |
| Routes | Colombo→Kandy (01), Galle (32), Kurunegala (04), Negombo (04-2), Ratnapura (98) |
| Period | Full year 2024 |
| Features | 25 columns (16 used as model inputs) |
| Target | `delay_category` — On Time / Slightly Delayed / Heavily Delayed |

**Data sources:**
- Route distances & numbers: [NTC Sri Lanka](https://ntc.gov.lk) / bustimetable.lk
- 2024 Public holidays & Poya days: publicholidays.lk + Sri Lanka government calendar
- Monsoon weather patterns: Sri Lanka Meteorological Department
- Trip records: Google Form survey shared with regular commuters

**Key Sri Lankan features:** Poya days, Kandy Perahera season, SW monsoon (May–Sep
heavily affects Galle/Ratnapura routes), inter-monsoon thunderstorms (Mar–Apr, Oct–Nov).

---

## Algorithm — LightGBM

**Why LightGBM (not a standard lecture algorithm)?**

| Standard Algorithms | LightGBM Difference |
|---|---|
| Decision Tree — level-wise growth | **Leaf-wise growth** — splits the leaf with highest loss gain, producing deeper, more accurate trees |
| Standard GBDT — uses all data | **GOSS** (Gradient-based One-Side Sampling) — drops low-gradient instances, reducing computation |
| Dense feature matrices | **EFB** (Exclusive Feature Bundling) — bundles mutually exclusive sparse features, reducing dimensionality |
| Slow for large datasets | Histogram-based splitting — 10–100× faster than exact GBDT |

---

## Model Results

| Metric | Validation | Test |
|---|---|---|
| Accuracy | 81.3% | 81.3% |
| F1-score (macro) | 0.791 | 0.803 |
| F1-score (weighted) | 0.811 | 0.815 |
| AUC-ROC (macro OvR) | 0.895 | 0.916 |

**Best hyperparameters** (GridSearchCV, 5-fold, F1-macro):
`num_leaves=31`, `learning_rate=0.05`, `n_estimators=97` (early stopped), `min_child_samples=20`

**Top features by SHAP importance:**
1. Crowding Level
2. Is Festival Period
3. Departure Delay (min)
4. Weather
5. Departure Hour

---

## Explainability Methods

| Method | What it shows |
|---|---|
| **SHAP TreeExplainer** | Global feature importance (beeswarm, bar), per-prediction waterfall, dependence plots |
| **LIME** | Local linear approximation explaining a single "Heavily Delayed" prediction |
| **PDP** | How departure delay, weather, and festival period independently affect P(Heavily Delayed) |

---

## Critical Discussion

### Limitations
- **Dataset size:** 500 records is small; a production system would need thousands of real GPS-tracked trips.
- **Survey bias:** Trip records from Google Form reflect respondents who bothered to fill it in — likely passengers who experienced notable delays.
- **No real-time inputs:** Weather and crowding are self-reported; a real deployment would integrate live weather APIs and passenger count sensors.
- **Route coverage:** Only 5 Colombo-origin routes; inter-provincial and rural routes are excluded.

### Data Quality
- Holiday/festival flags are binary; they don't capture the *magnitude* of the event (e.g., first day of New Year vs. mid-week during the season).
- Crowding level is subjective (survey respondent's perception), not a measured value.

### Bias & Fairness
- Routes to tourist-heavy destinations (Kandy, Galle) may appear more reliable because survey respondents on those routes skewed toward luxury bus users.
- Seasonal imbalance: more records exist for April–May (festival months) due to weighted sampling.

### Ethical Considerations
- No personal data is collected or stored; all trip records are anonymised at collection.
- A deployed delay predictor could inadvertently disadvantage certain communities if it under-predicts delays on rural routes with sparse data.
- The model should be presented as an *estimate*, not a guarantee, to avoid passenger decisions based on false certainty.

---

## Setup & Running

### 1. ML Pipeline (generate figures + artifacts)

```bash
cd ml
pip install -r requirements.txt
python 01_preprocessing.py
python 02_train_evaluate.py
python 03_explainability.py
```

### 2. Backend (FastAPI)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
# API running at http://localhost:8000
```

### 3. Frontend (React)

```bash
cd frontend
npm install
npm run dev
# App running at http://localhost:5173
```

Both backend and frontend must be running simultaneously for the app to work.

---

## Tech Stack

| Layer | Technology |
|---|---|
| ML Model | LightGBM 4.x |
| XAI | SHAP, LIME, scikit-learn PDP |
| Backend API | FastAPI + Uvicorn |
| Frontend | React 18 + Vite + Recharts |
| Language | Python 3.11 / JavaScript (ES2022) |
