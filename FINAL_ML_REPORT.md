# Machine Learning Assignment: Property Price Prediction in Sri Lanka

**Student Name:** [Your Name]  
**Algorithm:** LightGBM (Light Gradient Boosting Machine)  
**XAI Method:** SHAP (SHapley Additive exPlanations)  
**System:** Full-Stack API & React Dashboard

---

## 1. Problem Definition & Dataset Collection (15 Marks)

### 1.1 Problem Statement

The real estate market in Sri Lanka often lacks transparency. Property prices vary significantly based on location, quality tiers, and amenities, making it difficult for first-time buyers and investors to estimate fair market values. This project aims to develop a high-precision Property Price Predictor specifically for the Sri Lankan context.

### 1.2 Data Source

The dataset was compiled through automated web scraping of multiple primary real estate portals in Sri Lanka:

- **ikman.lk**: Largest online marketplace.
- **hitad.lk**: Traditional classifieds portal.
- **patpat.lk**: Modern property and automobile marketplace.

This multi-source approach ensures a broader representation of the Sri Lankan market, capturing over **13,000 raw listings** before filtering.

### 1.3 Features and Target Variable

- **Target Variable**: `price_lkr` (The advertised price of the property).
- **Key Features**:
  - `location`: Categorical (Districts and Major Cities).
  - `property_type`: House, Apartment, Land, or Commercial.
  - `bedrooms / bathrooms`: Numerical specifications.
  - `land_size_perches`: Numerical (Area of land).
  - `quality_tier`: Categorical (Standard, Modern, Luxury, Super Luxury).
  - `is_furnished`: Degree of furnishing.

### 1.4 Dataset Statistics & Preprocessing

- **Raw Data**: 13,497 listings.
- **Processed Data**: After cleaning and filtering, the model was trained on **12,281 high-quality records**.
- **Cleaning**:
  - Removal of extreme outliers (properties over Rs. 1 Billion or under Rs. 100,000).
  - Handling missing values: Bedroom/bathroom counts imputed with medians.
  - **Location Sanitization**: Raw scraped data from patpat.lk occasionally contained price tags inside the location field (e.g., "ColomboRs. 15M"). A robust Regex-based cleaner was implemented to strip these artifacts, ensuring a professional UI and improving model encoding accuracy.
  - **Keyword Extraction**: Due to varying data structures across sites, a fallback keyword-extraction algorithm was implemented to correctly identify property types.
- **Encoding**: Label Encoding was used for categorical features.
- **Normalization**: Target prices were log-transformed (`np.log1p`) to handle skewness.

---

## 2. Selection of Machine Learning Algorithm (15 Marks)

### 2.1 Algorithm Selection: LightGBM

For this assignment, **LightGBM (Light Gradient Boosting Machine)** was selected over traditional algorithms like Random Forest or Linear Regression.

### 2.2 Justification

1. **Histogram-based Learning**: LightGBM is significantly faster than traditional GBDT (Gradient Boosted Decision Trees) because it buckets continuous features into discrete bins.
2. **Category Handling**: It can handle categorical variables (like Sri Lankan cities) natively and more efficiently than one-hot encoding.
3. **Leaf-wise Growth**: It grows trees leaf-wise rather than level-wise, which allows it to capture complex non-linear relationships in luxury property pricing more accurately.

---

## 3. Model Training and Evaluation (20 Marks)

### 3.1 Training Process

- **Data Split**: 70% Training / 15% Validation / 15% Test.
- **Hyperparameters**: `num_leaves=63`, `learning_rate=0.05`, `n_estimators=1000`.

### 3.2 Performance Results

| **R² Score (Test - Log Space)** | **0.806** |
| **Mean Absolute Error (MAE)** | **Rs. 11.16M** |

### 3.3 Discussion of Results

An **R² of 0.806** indicates that the model explains over 80% of the variance in property prices in log-space. Given the diverse nature of local real estate (ranging from Rs. 5M land to Rs. 200M luxury homes), this represents a highly reliable predictive tool for the Sri Lankan market.

---

## 4. Explainability & Interpretation (20 Marks)

### 4.1 XAI Method: SHAP Analysis

To ensure the model is not a "black box," **SHAP (SHapley Additive exPlanations)** was applied. SHAP values allow us to see exactly how much each feature contributed to a specific price prediction.

### 4.2 Key Findings

- **Property Type**: Found to be the most influential factor. Apartments in Colombo carry a premium per perch compared to standalone houses.
- **Location Impact**: The model correctly learned that "Colombo" and "Gampaha" act as positive price drivers (uplifting the baseline), while rural districts lower the predicted value.
- **Quality Tiers**: The "Luxury" and "Super Luxury" tiers contribute significantly more to the final price than basic amenities like furnishing.

### 4.3 Domain Alignment

The model's behavior aligns perfectly with Sri Lankan domain knowledge: **Location** and **Land Size** are the primary drivers of wealth, while internal specifications act as secondary multipliers.

---

## 5. Critical Discussion (10 Marks)

### 5.1 Limitations

- **Economic Volatility**: The model is trained on ikman data but does not live-track Central Bank interest rates or cement price fluctuations in real-time.
- **Data Skew**: There is a higher density of data for the Western Province, which may lead to slight bias when predicting prices for the Northern or Eastern Provinces.

### 5.2 Ethical Considerations

The system uses publicly available listing data. To maintain privacy, all individual contact names and phone numbers were stripped during the preprocessing phase, ensuring the model only learns market trends, not personal data.

---

## 6. Bonus: Front-End Integration (10 Marks)

The trained LightGBM model was successfully integrated into a professional web-based dashboard:

- **Architecture**: FastAPI (Backend) + React / Mantine (Frontend).
- **Interactive Features**: Users can input property specs and get an instant valuation.
- **Live XAI**: The system displays a live SHAP importance chart for _every_ prediction, explaining to the user why that specific price was calculated.

---

## 7. Appendix - Visualizations

### [Image 1: Feature Importance]

_This chart shows the global impact of features on the model's decisions._

### [Image 2: Prediction Accuracy]

_The distribution shows how closely predicted prices follow the actual market values._

### [Image 3: Price Distribution]

_A histogram showing the spread of listing prices in the local market._
