import os
import pandas as pd
import numpy as np
from faker import Faker
import random

OFFICIAL_SECTORS = [
    "Travel, Tourism and Hospitality", "Transportation, Logistics", "Healthcare",
    "IT and ITeS", "Leather and Leather Goods", "Textile and Clothing",
    "Handlooms and Handicrafts", "Food Processing", "Electronics and IT hardware",
    "Domestic Help", "Building, Construction and Real Estate", "Beauty and Wellness",
    "Banking and Financial Services", "Auto and Auto Components", "Telecommunications",
    "Private Security Services", "Pharmaceuticals", "Retail", "Media and Entertainment",
    "Agriculture", "Furniture and Furnishing"
]

fake = Faker('en_IN')

def generate_synthetic_data(num_samples=5000):
    print("Generating highly realistic synthetic datasets...")
    
    # 1. Attendance Data (Impacted by weather and workload)
    attendance_data = []
    job_roles = OFFICIAL_SECTORS
    
    for _ in range(num_samples):
        role = random.choice(job_roles)
        temp = random.uniform(20, 45) # 45 is extreme heat
        rain = random.uniform(0, 50)  # Heavy rain
        workload = random.uniform(0.1, 1.0)
        leaves_taken = random.randint(0, 10)
        
        # Logic for attendance probability
        prob = 0.9 - (0.05 * leaves_taken) - (0.1 if temp > 40 else 0) - (0.2 if rain > 20 else 0)
        prob = max(0.1, min(0.99, prob))
        present = 1 if random.random() < prob else 0
        
        attendance_data.append([
            fake.uuid4(), fake.name(), role, random.randint(0, 6),
            leaves_taken, workload, temp, rain, present
        ])
    
    df_att = pd.DataFrame(attendance_data, columns=['employee_id', 'name', 'job_role', 'day_of_week', 'leaves_taken', 'workload', 'temperature', 'precipitation', 'present'])
    df_att.to_csv('village_attendance_dataset.csv', index=False)
    
    # 2. Wage & Demand Data (For Dynamic Pricing & Prophet)
    demand_data = []
    months = list(range(1, 13))
    
    base_wages = {
        "Travel, Tourism and Hospitality": 500, "Transportation, Logistics": 450, "Healthcare": 600,
        "IT and ITeS": 800, "Leather and Leather Goods": 400, "Textile and Clothing": 350,
        "Handlooms and Handicrafts": 380, "Food Processing": 400, "Electronics and IT hardware": 650,
        "Domestic Help": 300, "Building, Construction and Real Estate": 450, "Beauty and Wellness": 400,
        "Banking and Financial Services": 700, "Auto and Auto Components": 500, "Telecommunications": 600,
        "Private Security Services": 400, "Pharmaceuticals": 550, "Retail": 400, "Media and Entertainment": 500,
        "Agriculture": 350, "Furniture and Furnishing": 400
    }

    # For more realistic dataset, we should have multiple samples per month/role combination
    for _ in range(num_samples):
        month = random.randint(1, 12)
        role = random.choice(job_roles)
        pop = random.randint(1000, 5000)
        base_wage = base_wages.get(role, 400)
        
        # Seasonality logic
        season = "Monsoon" if 6 <= month <= 9 else "Summer" if 3 <= month <= 5 else "Winter"
        
        # Adding Weather Features
        temp = random.uniform(20, 45)
        precip = random.uniform(0, 50)
        
        if season == "Monsoon":
            precip = random.uniform(20, 100)
        elif season == "Summer":
            temp = random.uniform(35, 48)
            precip = random.uniform(0, 10)
            
        demand_multiplier = 1.0
        # Agriculture spikes when it rains a lot (Monsoon/Sowing)
        if role == "Agriculture" and precip > 40:
            demand_multiplier += 1.2
        # Construction drops heavily in extreme rain
        if role == "Building, Construction and Real Estate" and precip > 50:
            demand_multiplier -= 0.6
        # Healthcare spikes in extreme weather (heatwaves or monsoon diseases)
        if role == "Healthcare" and (temp > 42 or precip > 60):
            demand_multiplier += 0.8
            
        jobs_posted = int((pop * 0.005 + random.uniform(-2, 5)) * demand_multiplier)
        jobs_posted = max(1, jobs_posted)
        suggested_wage = int(base_wage * (1 + (jobs_posted / pop) * 2) * demand_multiplier + random.uniform(-20, 20))
        
        demand_data.append([month, season, temp, precip, role, pop, jobs_posted, suggested_wage])
        
    df_dem = pd.DataFrame(demand_data, columns=['month', 'season', 'temperature', 'precipitation', 'job_type', 'village_population', 'num_jobs_posted', 'avg_wage'])
    df_dem.to_csv('village_demand_dataset.csv', index=False)

    # 3. Fraud Detection Data (Isolation Forest)
    fraud_data = []
    for _ in range(num_samples):
        employer_id = fake.uuid4()
        jobs_posted_24h = random.randint(1, 3)
        wage_offered = random.randint(200, 600)
        reports_against = random.randint(0, 1)
        
        is_fraud = 0
        # Inject anomalies with a bit more noise so it's not 100% trivially linearly separable
        if random.random() < 0.05: # 5% fraud rate
            jobs_posted_24h = random.randint(3, 10) # Less obvious spamming
            wage_offered = random.randint(800, 1200) # Semi-unrealistic wage
            reports_against = random.randint(1, 4)
            is_fraud = 1
            
        fraud_data.append([employer_id, jobs_posted_24h, wage_offered, reports_against, is_fraud])
        
    df_fraud = pd.DataFrame(fraud_data, columns=['employer_id', 'jobs_posted_24h', 'wage_offered', 'reports_against', 'is_fraud'])
    df_fraud.to_csv('village_fraud_dataset.csv', index=False)
    
    print("CSV generation complete. Files updated:")
    print("- village_attendance_dataset.csv")
    print("- village_demand_dataset.csv")
    print("- village_fraud_dataset.csv")

if __name__ == "__main__":
    generate_synthetic_data()
