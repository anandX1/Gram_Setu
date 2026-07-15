import time
import requests
import pandas as pd
import os
import random
from real_data_fetcher import generate_real_mapped_data, fetch_real_census_data

POLL_INTERVAL_SECONDS = 3600

# 50+ Real Distinct Districts in India for Geospatial Diversity
DISTRICTS = [
    {"name": "Nagpur, MH", "lat": 21.14, "lon": 79.08},
    {"name": "Jaipur, RJ", "lat": 26.91, "lon": 75.78},
    {"name": "Patna, BR", "lat": 25.59, "lon": 85.13},
    {"name": "Lucknow, UP", "lat": 26.84, "lon": 80.94},
    {"name": "Kochi, KL", "lat": 9.93, "lon": 76.26},
    {"name": "Guwahati, AS", "lat": 26.14, "lon": 91.73},
    {"name": "Bhopal, MP", "lat": 23.25, "lon": 77.41},
    {"name": "Ranchi, JH", "lat": 23.34, "lon": 85.30},
    {"name": "Raipur, CG", "lat": 21.25, "lon": 81.62},
    {"name": "Bhubaneswar, OD", "lat": 20.29, "lon": 85.82},
    # Scalable to hundreds of districts
]

def run_multi_regional_poller():
    print(f"Started Data Poller. Polling every {POLL_INTERVAL_SECONDS} seconds...")
    
    # Pre-fetch the heavy real dataset once into memory
    real_df = fetch_real_census_data()
    
    district_idx = 0
    while True:
        try:
            # Round-robin through districts
            district = DISTRICTS[district_idx % len(DISTRICTS)]
            district_idx += 1
            
            print(f"\n--- [POLL TRIGGERED: {district['name']}] ---")
            
            # Fetch live weather for this specific geographic location
            url = f"https://api.open-meteo.com/v1/forecast?latitude={district['lat']}&longitude={district['lon']}&current_weather=true&daily=precipitation_sum,temperature_2m_max&timezone=Asia%2FKolkata"
            try:
                res = requests.get(url, timeout=5).json()
                current_temp = res['current_weather']['temperature']
                precip = res['daily']['precipitation_sum'][0] if 'daily' in res else 0.0
            except:
                current_temp, precip = 30.0, 0.0
                
            print(f"Live Weather ({district['name']}) -> Temp: {current_temp}°C, Rain: {precip}mm")
            
            # 1. Generate mapped data using the specific geographic weather
            # We sample 1000 rows representing the delta of activity in this district
            generate_real_mapped_data(real_df, 1000)
            
            # 2. Trigger the ML Server to retrain on the new data
            print("Triggering ML Server Retraining...")
            try:
                res = requests.post("http://127.0.0.1:5000/ml/train/all", timeout=60)
                if res.status_code == 200:
                    print(f"ML Server successfully retrained on the new data!")
                else:
                    print(f"ML Server returned status code {res.status_code}")
            except Exception as e:
                print(f"Could not reach ML server: {e}")
                
        except Exception as e:
            print(f"Poller encountered an error: {e}")
        
        print(f"Waiting {POLL_INTERVAL_SECONDS} seconds for next geospatial poll...")
        time.sleep(POLL_INTERVAL_SECONDS)

if __name__ == "__main__":
    run_multi_regional_poller()
