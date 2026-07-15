import os
import requests
import json
import logging
from datetime import datetime

# Setup MLOps logging
logging.basicConfig(
    filename='mlops_pipeline.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

ML_SERVER_URL = "http://localhost:5000"

def trigger_retraining():
    """
    Triggers the /ml/train/all endpoint to retrain all models.
    """
    logging.info("Starting automated ML retraining pipeline...")
    print("Initiating Retraining Pipeline...")
    
    try:
        response = requests.post(f"{ML_SERVER_URL}/ml/train/all")
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                logging.info("Retraining successful.")
                print("Success! Models retrained.")
                for model, result in data.get('results', {}).items():
                    if result.get('ok'):
                        logging.info(f"{model.upper()} upgraded. New metric: {result.get('accuracy', 'N/A')}")
                        print(f" - {model.upper()} upgraded. New metric: {result.get('accuracy', 'N/A')}")
                    else:
                        logging.warning(f"{model.upper()} failed: {result.get('error')}")
            else:
                logging.error(f"Retraining failed: {data.get('error')}")
        else:
            logging.error(f"Server returned status {response.status_code}")
            
    except requests.exceptions.ConnectionError:
        logging.error("Failed to connect to ML Server. Is it running?")
        print("Error: Could not reach ML server at localhost:5000")

if __name__ == "__main__":
    trigger_retraining()
