import schedule
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import DataCollectionPipeline
from models.train_models import ModelTrainer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.data_pipeline = DataCollectionPipeline()
        self.model_trainer = ModelTrainer()
    
    def schedule_tasks(self):
        # Hourly data collection
        schedule.every(1).hours.do(self.data_pipeline.collect_data)
        
        # Daily model retraining
        schedule.every().day.at("02:00").do(self.retrain_models)
        
        logger.info("Scheduler initialized")
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def retrain_models(self):
        logger.info("Starting daily model retraining...")
        from config.settings import CITIES
        for city in CITIES:
            self.model_trainer.train_all_models(city)

if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.schedule_tasks()
