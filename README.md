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
### or
python -m uvicorn main:app --reload
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
