# California Housing Price Prediction — Week 1 Mini Project

## Project Overview
Statistical analysis and regression modeling on the California Housing dataset, covering data cleaning, EDA, Simple & Multiple Linear Regression, and a Random Forest comparison with deployment.

## How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Open `Week1_Statistics_Regression.ipynb` in Jupyter/VSCode
3. Run all cells top to bottom
4. Run the dashboard: `streamlit run app.py`

## Live Dashboard
https://vcti-california-housing-dashboard-npgtu2bsf4pducwcepy8ks.streamlit.app/

## Libraries Required
See `requirements.txt`

## Key Findings
1. Median Income (MedInc) is the strongest single predictor of house value (r = 0.688)
2. Latitude and Longitude, though weakly correlated with price individually, jointly capture major geographic pricing patterns
3. Multiple Linear Regression (5 features) improved R² from 0.4980 to 0.6175 over Simple Linear Regression
4. Random Forest substantially outperformed both linear models (R² = 0.8341), capturing non-linear location and income effects
5. The target variable is capped at $500,000, visible as a data artifact in residual plots
6. AveRooms, AveBedrms, and AveOccup contain extreme outliers from small-population block groups, kept intentionally rather than removed
7. Feature importance analysis confirmed income and location as the dominant predictive factors across all models

## Author
Shahbaz Athar