import os
import pandas as pd
import numpy as np
import pickle
import json
from datetime import datetime
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, confusion_matrix,
    mean_absolute_error, mean_squared_error, r2_score
)
from sentence_transformers import SentenceTransformer
import torch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Data Paths
CSV = {
    'attendance': os.path.join(BASE_DIR, 'village_attendance_dataset.csv'),
    'availability': os.path.join(BASE_DIR, 'village_availability_dataset.csv'),
    'demand': os.path.join(BASE_DIR, 'village_demand_dataset.csv'),
    'skill': os.path.join(BASE_DIR, 'village_skill_dataset.csv'),
    'fraud': os.path.join(BASE_DIR, 'village_fraud_dataset.csv'),
    'wage': os.path.join(BASE_DIR, 'village_demand_dataset.csv')
}

PKL = {
    'attendance': os.path.join(BASE_DIR, 'model_attendance.pkl'),
    'availability': os.path.join(BASE_DIR, 'model_availability.pkl'),
    'demand': os.path.join(BASE_DIR, 'model_demand.pkl'),
    'skill': os.path.join(BASE_DIR, 'model_skill.pkl'),
    'fraud': os.path.join(BASE_DIR, 'model_fraud.pkl'),
    'wage': os.path.join(BASE_DIR, 'model_wage.pkl')
}

def load_model(name):
    if not os.path.exists(PKL[name]): return None
    with open(PKL[name], 'rb') as f: return pickle.load(f)

def generate_report():
    print("Running Mathematical Evaluation across all 6 AI Engines...")
    report = []
    
    # 1. ATTENDANCE (Classification)
    print("Evaluating Attendance Engine (LightGBM)...")
    payload = load_model('attendance')
    if payload:
        df = pd.read_csv(CSV['attendance'])
        
        df['job_role'] = df['job_role'].astype('category')
        X = df[payload['features']]
        y_true = df['present']
        y_pred = payload['model'].predict(X)
        
        report.append({
            "Engine": "Attendance Predictor",
            "Type": "Classification (LightGBM)",
            "Metrics": {
                "Accuracy": round(accuracy_score(y_true, y_pred), 3),
                "Precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
                "Recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
                "F1 Score": round(f1_score(y_true, y_pred, zero_division=0), 3)
            }
        })
    
    # 2. FRAUD DETECTION (Classification)
    print("Evaluating Fraud Detection Engine (RandomForest)...")
    payload = load_model('fraud')
    if payload:
        df = pd.read_csv(CSV['fraud'])
        X = df[payload['features']]
        y_true = df['is_fraud']
        y_pred = payload['model'].predict(X)
        
        report.append({
            "Engine": "Fraud Detection",
            "Type": "Classification (RandomForestClassifier)",
            "Metrics": {
                "Accuracy": round(accuracy_score(y_true, y_pred), 3),
                "Precision": round(precision_score(y_true, y_pred, zero_division=0), 3),
                "Recall": round(recall_score(y_true, y_pred, zero_division=0), 3),
                "F1 Score": round(f1_score(y_true, y_pred, zero_division=0), 3)
            }
        })
        
    # 3. DEMAND FORECASTING (Regression)
    print("Evaluating Job Demand Engine (XGBoost)...")
    payload = load_model('demand')
    if payload:
        df = pd.read_csv(CSV['demand'])
        df['season'] = df['season'].astype('category')
        df['job_type'] = df['job_type'].astype('category')
        X = df[payload['features']]
        y_true = df['num_jobs_posted']
        y_pred = payload['model'].predict(X)
        
        report.append({
            "Engine": "Job Demand Forecaster",
            "Type": "Regression (XGBoost Regressor)",
            "Metrics": {
                "R2 Score": round(r2_score(y_true, y_pred), 3),
                "MAE": round(mean_absolute_error(y_true, y_pred), 3),
                "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 3)
            }
        })

    # 4. DYNAMIC WAGE PREDICTOR (Regression)
    print("Evaluating Dynamic Wage Predictor (CatBoost)...")
    payload = load_model('wage')
    if payload:
        df = pd.read_csv(CSV['wage'])
        df['season'] = df['season'].astype('category')
        df['job_type'] = df['job_type'].astype('category')
        X = df[payload['features']]
        y_true = df['avg_wage']
        y_pred = payload['model'].predict(X)
        
        report.append({
            "Engine": "Dynamic Wage Predictor",
            "Type": "Regression (CatBoostRegressor)",
            "Metrics": {
                "R2 Score": round(r2_score(y_true, y_pred), 3),
                "MAE": round(mean_absolute_error(y_true, y_pred), 3),
                "RMSE": round(np.sqrt(mean_squared_error(y_true, y_pred)), 3)
            }
        })
        
    # Write to a JSON file for the Markdown artifact to read
    with open('evaluation_metrics.json', 'w') as f:
        json.dump(report, f, indent=4)
        
    print("Mathematical evaluation complete! Results saved to evaluation_metrics.json")

if __name__ == "__main__":
    generate_report()
