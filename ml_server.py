"""
AI GramSetu — ml_server.py
--------------------------
Runs on http://localhost:5000
"""
import os, json, pickle, traceback
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np

# ML Models
from sklearn.linear_model import SGDClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostRegressor, CatBoostClassifier

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CSV = {
    'attendance'  : os.path.join(BASE_DIR, 'village_attendance_dataset.csv'),
    'availability': os.path.join(BASE_DIR, 'village_availability_dataset.csv'),
    'demand'      : os.path.join(BASE_DIR, 'village_demand_dataset.csv'),
    'skill'       : os.path.join(BASE_DIR, 'village_skill_dataset.csv'),
    'fraud'       : os.path.join(BASE_DIR, 'village_fraud_dataset.csv'),
    'wage'        : os.path.join(BASE_DIR, 'village_demand_dataset.csv'), 
}
PKL = {
    'attendance'  : os.path.join(BASE_DIR, 'model_attendance.pkl'),
    'availability': os.path.join(BASE_DIR, 'model_availability.pkl'),
    'demand'      : os.path.join(BASE_DIR, 'model_demand.pkl'),
    'skill'       : os.path.join(BASE_DIR, 'model_skill.pkl'),
    'fraud'       : os.path.join(BASE_DIR, 'model_fraud.pkl'),
    'wage'        : os.path.join(BASE_DIR, 'model_wage.pkl'),
}
HISTORY_FILE = os.path.join(BASE_DIR, 'ml_history.json')

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def save_history(entry):
    history = load_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history[:100], f, indent=2)

def save_model(name, payload):
    with open(PKL[name], 'wb') as f:
        pickle.dump(payload, f)

def load_model(name):
    if not os.path.exists(PKL[name]):
        return None
    with open(PKL[name], 'rb') as f:
        return pickle.load(f)

# ─────────────────────────────────────────────────────────────────────────────
# CONTINUAL LEARNING MODEL 1: ATTENDANCE (LightGBM)
# ─────────────────────────────────────────────────────────────────────────────
def train_attendance():
    df = pd.read_csv(CSV['attendance'])
    df['job_role'] = df['job_role'].astype('category')
    
    features = ['job_role', 'day_of_week', 'leaves_taken', 'workload', 'precipitation', 'temperature']
    X = df[features]
    y = df['present']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1, verbose=-1)
    model.fit(X_train, y_train)

    acc = round(accuracy_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('attendance', {'model': model, 'features': features, 'accuracy': acc})
    return acc, {}

def predict_attendance(job_role, day_of_week, leaves_taken, workload, precip=0, temp=30):
    payload = load_model('attendance')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[job_role, day_of_week, leaves_taken, workload, precip, temp]], columns=payload['features'])
    X['job_role'] = X['job_role'].astype('category')
    prob = payload['model'].predict_proba(X)[0][1]
    return {'will_be_present': bool(prob > 0.5), 'probability': round(prob * 100, 1)}, None

# ─────────────────────────────────────────────────────────────────────────────
# CONTINUAL LEARNING MODEL 2: AVAILABILITY (CatBoost)
# ─────────────────────────────────────────────────────────────────────────────
def train_availability():
    df = pd.read_csv(CSV['availability'])
    features = ['skill', 'experience_years', 'day_of_week', 'season', 'last_job_days_ago']
    cat_features = ['skill', 'season']
    df['skill'] = df['skill'].astype(str)
    df['season'] = df['season'].astype(str)
    
    X = df[features]
    y = df['available']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CatBoostClassifier(iterations=250, learning_rate=0.05, depth=5, cat_features=cat_features, verbose=0, random_seed=42, thread_count=-1)
    model.fit(X_train, y_train)

    acc = round(accuracy_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('availability', {'model': model, 'features': features, 'accuracy': acc})
    return acc, {}

def predict_availability(skill, experience_years, day_of_week, season, last_job_days_ago):
    payload = load_model('availability')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[str(skill), experience_years, day_of_week, str(season), last_job_days_ago]], columns=payload['features'])
    prob = payload['model'].predict_proba(X)[0][1]
    return {'will_be_available': bool(prob > 0.5), 'probability': round(prob * 100, 1)}, None

# ─────────────────────────────────────────────────────────────────────────────
# CONTINUAL LEARNING MODEL 3: DEMAND (XGBoost)
# ─────────────────────────────────────────────────────────────────────────────
def train_demand():
    df = pd.read_csv(CSV['demand'])
    df['season'] = df['season'].astype('category')
    df['job_type'] = df['job_type'].astype('category')
    
    features = ['month', 'season', 'temperature', 'precipitation', 'job_type', 'village_population']
    X = df[features]
    y = df['num_jobs_posted']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(n_estimators=250, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1, enable_categorical=True)
    model.fit(X_train, y_train)

    r2 = round(r2_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('demand', {'model': model, 'features': features, 'r2': r2})
    return r2, {}

def predict_demand(month, season, temp, precip, job_type, village_population):
    payload = load_model('demand')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[month, season, temp, precip, job_type, village_population]], columns=payload['features'])
    X['season'] = X['season'].astype('category')
    X['job_type'] = X['job_type'].astype('category')
    predicted = int(round(float(payload['model'].predict(X)[0])))
    return {'predicted_jobs': max(0, predicted)}, None

# ─────────────────────────────────────────────────────────────────────────────
# MODEL 4, 5, 6: SKILL, FRAUD, WAGE
# (Implementing similar Continual Learning structures)
# ─────────────────────────────────────────────────────────────────────────────
def train_skill():
    df = pd.read_csv(CSV['skill'])
    features = ['required_skill', 'experience_needed', 'worker_skill', 'worker_experience', 'worker_distance_km']
    df['required_skill'] = df['required_skill'].astype('category')
    df['worker_skill'] = df['worker_skill'].astype('category')
    X = df[features]
    y = df['matched']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = lgb.LGBMClassifier(n_estimators=250, learning_rate=0.05, max_depth=5, random_state=42, n_jobs=-1, verbose=-1)
    model.fit(X_train, y_train)
        
    acc = round(accuracy_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('skill', {'model': model, 'features': features, 'accuracy': acc})
    return acc, {}

def predict_skill(req_skill, exp_needed, worker_skill, worker_exp, distance):
    payload = load_model('skill')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[req_skill, exp_needed, worker_skill, worker_exp, distance]], columns=payload['features'])
    X['required_skill'] = X['required_skill'].astype('category')
    X['worker_skill'] = X['worker_skill'].astype('category')
    prob = payload['model'].predict_proba(X)[0][1]
    return {'match_probability': round(prob * 100, 1)}, None

def train_fraud():
    df = pd.read_csv(CSV['fraud'])
    features = ['jobs_posted_24h', 'wage_offered', 'reports_against']
    X = df[features]
    y = df['is_fraud']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = RandomForestClassifier(n_estimators=250, max_depth=5, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)
        
    acc = round(accuracy_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('fraud', {'model': model, 'features': features, 'accuracy': acc})
    return acc, {}

def predict_fraud(jobs, wage, reports):
    payload = load_model('fraud')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[jobs, wage, reports]], columns=payload['features'])
    prob = payload['model'].predict_proba(X)[0][1]
    return {'fraud_probability': round(prob * 100, 1)}, None

def train_wage():
    df = pd.read_csv(CSV['wage'])
    df['season'] = df['season'].astype(str)
    df['job_type'] = df['job_type'].astype(str)
    features = ['month', 'season', 'job_type', 'village_population', 'num_jobs_posted']
    X = df[features]
    y = df['avg_wage']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = CatBoostRegressor(iterations=250, learning_rate=0.05, depth=5, cat_features=['season', 'job_type'], verbose=0, random_seed=42, thread_count=-1)
    model.fit(X_train, y_train)
        
    r2 = round(r2_score(y_test, model.predict(X_test)) * 100, 1)
    save_model('wage', {'model': model, 'features': features, 'r2': r2})
    return r2, {}

def predict_wage(month, season, job_type, pop, jobs):
    payload = load_model('wage')
    if not payload: return None, 'Model not trained'
    X = pd.DataFrame([[month, season, job_type, pop, jobs]], columns=payload['features'])
    X['season'] = X['season'].astype(str)
    X['job_type'] = X['job_type'].astype(str)
    predicted = payload['model'].predict(X)[0]
    return {'recommended_wage': round(float(predicted), 2)}, None


# ── ROUTES ────────────────────────────────────────────────────────────────────
@app.route('/ml/status', methods=['GET'])
def get_status():
    models = {}
    for name in CSV.keys():
        trained = os.path.exists(PKL[name])
        csv_ready = os.path.exists(CSV[name])
        
        payload = load_model(name)
        acc = None
        if payload:
            if 'accuracy' in payload: acc = payload['accuracy']
            elif 'r2' in payload: acc = payload['r2']
            
        models[name] = {
            'trained': trained,
            'csv_ready': csv_ready,
            'accuracy': acc
        }
    return jsonify({'ok': True, 'models': models})

@app.route('/ml/history', methods=['GET'])
def get_history():
    return jsonify({'ok': True, 'history': load_history()})

@app.route('/ml/train/<model_name>', methods=['POST'])
def train_route(model_name):
    funcs = {
        'attendance': train_attendance,
        'availability': train_availability,
        'demand': train_demand,
        'skill': train_skill,
        'fraud': train_fraud,
        'wage': train_wage
    }
    
    if model_name == 'all':
        results = {}
        for n, f in funcs.items():
            try:
                acc, imp = f()
                results[n] = {'ok': True, 'accuracy': acc}
            except Exception as e:
                print(f"Error training {n}: {e}")
                results[n] = {'ok': False, 'error': str(e)}
        return jsonify({'ok': True, 'message': 'All models trained', 'results': results})
        
    if model_name not in funcs:
        return jsonify({'ok': False, 'error': 'Unknown model'}), 400
        
    try:
        acc, imp = funcs[model_name]()
        entry = {
            'id': datetime.now().strftime("%Y%m%d%H%M%S"),
            'model': model_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'accuracy': acc
        }
        save_history(entry)
        print(f'[train] {model_name} -> {acc}%')
        return jsonify({'ok': True, 'accuracy': acc, 'importances': imp})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/ml/predict/weather-forecast', methods=['POST', 'OPTIONS'])
def predict_weather_forecast():
    if request.method == 'OPTIONS': return '', 200
    data = request.json or {}
    
    temp = float(data.get('temperature', 30))
    precip = float(data.get('precipitation', 10))
    month = int(data.get('month', 7))
    season = data.get('season', 'Monsoon')
    village_population = int(data.get('village_population', 3000))
    
    payload = load_model('demand')
    if not payload: return jsonify({'ok': False, 'error': 'Model not trained'}), 400
    
    OFFICIAL_SECTORS = [
        "Travel, Tourism and Hospitality", "Transportation, Logistics", "Healthcare",
        "IT and ITeS", "Leather and Leather Goods", "Textile and Clothing",
        "Handlooms and Handicrafts", "Food Processing", "Electronics and IT hardware",
        "Domestic Help", "Building, Construction and Real Estate", "Beauty and Wellness",
        "Banking and Financial Services", "Auto and Auto Components", "Telecommunications",
        "Private Security Services", "Pharmaceuticals", "Retail", "Media and Entertainment",
        "Agriculture", "Furniture and Furnishing"
    ]
    
    forecasts = []
    for job in OFFICIAL_SECTORS:
        X = pd.DataFrame([[month, season, temp, precip, job, village_population]], columns=payload['features'])
        X['season'] = X['season'].astype('category')
        X['job_type'] = X['job_type'].astype('category')
        predicted = max(0, int(round(float(payload['model'].predict(X)[0]))))
        forecasts.append({'job_type': job, 'predicted_demand': predicted})
        
    forecasts = sorted(forecasts, key=lambda x: x['predicted_demand'], reverse=True)
    return jsonify({'ok': True, 'forecast': forecasts})

@app.route('/ml/predict/<model_name>', methods=['POST', 'OPTIONS'])
def predict_route(model_name):
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json or {}
    try:
        if model_name == 'attendance':
            res, err = predict_attendance(data.get('job_role',''), int(data.get('day_of_week',0)), int(data.get('leaves_taken',0)), float(data.get('workload',0.5)))
        elif model_name == 'availability':
            res, err = predict_availability(data.get('skill',''), int(data.get('experience_years',0)), int(data.get('day_of_week',0)), data.get('season',''), int(data.get('last_job_days_ago',0)))
        elif model_name == 'demand':
            res, err = predict_demand(int(data.get('month',1)), data.get('season',''), float(data.get('temperature',30)), float(data.get('precipitation',0)), data.get('job_type',''), int(data.get('village_population',1000)))
        elif model_name == 'skill':
            res, err = predict_skill(data.get('required_skill',''), int(data.get('experience_needed',0)), data.get('worker_skill',''), int(data.get('worker_experience',0)), float(data.get('worker_distance_km',0)))
        elif model_name == 'fraud':
            res, err = predict_fraud(int(data.get('jobs_posted_24h',0)), float(data.get('wage_offered',0)), int(data.get('reports_against',0)))
        elif model_name == 'wage':
            res, err = predict_wage(int(data.get('month',1)), data.get('season',''), data.get('job_type',''), int(data.get('village_population',1000)), int(data.get('num_jobs_posted',0)))
        else:
            return jsonify({'ok': False, 'error': 'Unknown model'}), 400
            
        if err: return jsonify({'ok': False, 'error': err}), 400
        return jsonify({'ok': True, 'prediction': res})
    except Exception as e:
        traceback.print_exc()
        return jsonify({'ok': False, 'error': str(e)}), 500



if __name__ == '__main__':
    app.run(port=5000, debug=False)
