import os
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
import xgboost as xgb
import pickle
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEMAND_CSV = os.path.join(BASE_DIR, 'village_demand_dataset.csv')
DEMAND_MODEL_PKL = os.path.join(BASE_DIR, 'model_demand.pkl')

def optimize_demand_model():
    print("\n--- INITIATING HYPERPARAMETER OPTIMIZATION (OFFLINE) ---")
    try:
        if not os.path.exists(DEMAND_CSV):
            print(f"Error: Dataset {DEMAND_CSV} not found.")
            return

        df = pd.read_csv(DEMAND_CSV)
        df['season'] = df['season'].astype('category')
        df['job_type'] = df['job_type'].astype('category')
        features = ['month', 'season', 'job_type', 'village_population']
        X = df[features]
        y = df['num_jobs_posted']
        
        # Heavy Compute Random Search on Demand Model
        param_grid = {
            'max_depth': [6, 8, 10],
            'learning_rate': [0.01, 0.05, 0.1],
            'n_estimators': [500, 1000]
        }
        
        base_model = xgb.XGBRegressor(random_state=42, n_jobs=-1, enable_categorical=True)
        search = RandomizedSearchCV(base_model, param_distributions=param_grid, n_iter=5, cv=3, verbose=2, n_jobs=-1)
        search.fit(X, y)
        
        print(f"Optimization Complete! Best Params: {search.best_params_}")
        
        # Save the optimized model
        payload = {
            'model': search.best_estimator_, 
            'features': features, 
            'r2': round(search.best_score_ * 100, 1)
        }
        
        with open(DEMAND_MODEL_PKL, 'wb') as f:
            pickle.dump(payload, f)
            
        print(f"Model saved to {DEMAND_MODEL_PKL} with R2 score: {payload['r2']}%")
        
    except Exception as e:
        print("Optimization failed:")
        traceback.print_exc()

if __name__ == "__main__":
    optimize_demand_model()
