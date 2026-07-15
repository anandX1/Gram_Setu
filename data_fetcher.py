import pandas as pd
import numpy as np
from faker import Faker
import random
import os
import uuid
import requests
from datetime import datetime, timedelta

# Official Indian Sector Skill Councils
OFFICIAL_SECTORS = [
    "Travel, Tourism and Hospitality", "Transportation, Logistics", "Healthcare",
    "IT and ITeS", "Leather and Leather Goods", "Textile and Clothing",
    "Handlooms and Handicrafts", "Food Processing", "Electronics and IT hardware",
    "Domestic Help", "Building, Construction and Real Estate", "Beauty and Wellness",
    "Banking and Financial Services", "Auto and Auto Components", "Telecommunications",
    "Private Security Services", "Pharmaceuticals", "Retail", "Media and Entertainment",
    "Agriculture", "Furniture and Furnishing"
]

def fetch_live_weather():
    """
    Polls the real Open-Meteo API for recent weather in Central India (e.g., Maharashtra).
    Returns average temperature and precipitation, which directly impacts rural work.
    """
    try:
        print("Polling Open-Meteo Live API...")
        # Coordinates roughly for Nagpur, India
        url = "https://api.open-meteo.com/v1/forecast?latitude=21.14&longitude=79.08&current_weather=true&daily=precipitation_sum,temperature_2m_max&timezone=Asia%2FKolkata"
        response = requests.get(url, timeout=5)
        data = response.json()
        current_temp = data['current_weather']['temperature']
        precip = data['daily']['precipitation_sum'][0] if 'daily' in data else 0.0
        return current_temp, precip
    except Exception as e:
        print(f"Weather API failed ({e}), using realistic fallbacks.")
        return 32.0, 5.0 # Fallback: 32C, 5mm rain

def generate_high_quality_data(num_rows=2000):
    print("Generating High-Quality Correlated Data...")
    fake = Faker('en_IN')
    np.random.seed(42)
    
    current_temp, precip = fetch_live_weather()
    print(f"Current Live Weather -> Temp: {current_temp}°C, Rain: {precip}mm")

    attendance_data = []
    availability_data = []
    demand_data = []
    skill_data = []
    fraud_data = []
    
    # Pre-calculate a weather severity index (0 to 1)
    weather_severity = 0.0
    if precip > 10.0: weather_severity += 0.5
    if current_temp > 40.0: weather_severity += 0.3
    
    # 1. Attendance Data (Impacted by Weather)
    for _ in range(num_rows):
        role = random.choice(OFFICIAL_SECTORS)
        day_of_week = random.randint(0, 6)
        leaves = np.random.poisson(2)
        workload = round(np.random.beta(2, 2), 2)
        
        base_prob = 0.9
        # Agriculture is heavily impacted by rain/heat
        if role == "Agriculture" and weather_severity > 0.4:
            base_prob -= 0.5
        elif role == "Building, Construction and Real Estate" and precip > 10.0:
            base_prob -= 0.4
            
        if leaves > 5: base_prob -= 0.3
        
        present = 1 if random.random() < base_prob else 0
        attendance_data.append([str(uuid.uuid4()), fake.name(), role, day_of_week, leaves, workload, precip, current_temp, present])

    # 2. Availability Data
    for _ in range(num_rows):
        skill = random.choice(OFFICIAL_SECTORS)
        exp = round(np.random.exponential(5) + 1, 1)
        dow = random.randint(0, 6)
        season = "Monsoon" if precip > 5 else "Summer" if current_temp > 35 else "Winter"
        last_job = random.randint(1, 30)
        
        # High experience = high demand = less available
        prob = 0.8
        if exp > 8: prob -= 0.3
        if last_job < 3: prob -= 0.4 # Just worked
        
        avail = 1 if random.random() < prob else 0
        availability_data.append([str(uuid.uuid4()), skill, exp, dow, season, last_job, avail])

    # 3. Demand & Wage Data
    for _ in range(num_rows):
        month = random.randint(1, 12)
        season = "Monsoon" if precip > 5 else "Summer" if current_temp > 35 else "Winter"
        job_type = random.choice(OFFICIAL_SECTORS)
        pop = random.randint(1000, 50000)
        
        # Demand formulas
        demand = int((pop * 0.01) + np.random.normal(0, 5))
        if job_type == "Agriculture" and season == "Monsoon":
            demand += 50
            
        wage = 300 + (exp * 20) + (demand * 2) + np.random.normal(0, 20)
        demand_data.append([month, season, job_type, pop, max(0, demand), round(wage, 2)])

    # 4. Skill Match
    for _ in range(num_rows):
        req_skill = random.choice(OFFICIAL_SECTORS)
        exp_needed = random.randint(1, 10)
        worker_skill = req_skill if random.random() < 0.6 else random.choice(OFFICIAL_SECTORS)
        worker_exp = round(np.random.exponential(5) + 1, 1)
        dist = round(random.uniform(1.0, 30.0), 1)
        
        match_prob = 0.9 if (req_skill == worker_skill and worker_exp >= exp_needed and dist < 15) else 0.1
        matched = 1 if random.random() < match_prob else 0
        skill_data.append([str(uuid.uuid4()), req_skill, exp_needed, worker_skill, worker_exp, dist, matched])
        
    # 5. Fraud Data
    for _ in range(num_rows):
        jobs_24h = np.random.poisson(1)
        wage_off = random.randint(200, 1500)
        reports = np.random.poisson(0.5)
        
        # Unrealistic wages + high volume + reports = fraud
        is_fraud = 1 if (jobs_24h > 5 or wage_off > 1000 or reports > 1) else 0
        if random.random() < 0.05: is_fraud = 1 - is_fraud # Add 5% noise
        fraud_data.append([jobs_24h, wage_off, reports, is_fraud])

    # Save to CSV
    pd.DataFrame(attendance_data, columns=['employee_id', 'name', 'job_role', 'day_of_week', 'leaves_taken', 'workload', 'precipitation', 'temperature', 'present']).to_csv("village_attendance_dataset.csv", index=False)
    pd.DataFrame(availability_data, columns=['worker_id', 'skill', 'experience_years', 'day_of_week', 'season', 'last_job_days_ago', 'available']).to_csv("village_availability_dataset.csv", index=False)
    pd.DataFrame(demand_data, columns=['month', 'season', 'job_type', 'village_population', 'num_jobs_posted', 'avg_wage']).to_csv("village_demand_dataset.csv", index=False)
    pd.DataFrame(skill_data, columns=['job_id', 'required_skill', 'experience_needed', 'worker_skill', 'worker_experience', 'worker_distance_km', 'matched']).to_csv("village_skill_dataset.csv", index=False)
    pd.DataFrame(fraud_data, columns=['jobs_posted_24h', 'wage_offered', 'reports_against', 'is_fraud']).to_csv("village_fraud_dataset.csv", index=False)
    
    print("New high-quality data chunks saved to CSVs.")

if __name__ == "__main__":
    # Increased to 5000 rows for stronger learning
    generate_high_quality_data(5000)
