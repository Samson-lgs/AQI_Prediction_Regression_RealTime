import schedule
import time
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import DataCollectionPipeline
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskScheduler:
    def __init__(self):
        self.data_pipeline = DataCollectionPipeline()

    def schedule_tasks(self):
        # Hourly data collection using the parallel method from DataCollectionPipeline
        schedule.every(1).hours.do(self.data_pipeline.collect_data_all_cities_parallel)
        # Daily unified model retraining at 02:00
        schedule.every().day.at("02:00").do(self.retrain_models)
        logger.info("Scheduler initialized (hourly collection + daily retraining)")
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    def retrain_models(self):
        """Kick off unified tuned training script to refresh models and medians."""
        try:
            logger.info("Starting daily unified model retraining (tuned)...")
            script = Path('scripts') / 'train_models_render_last7d_tuned.py'
            if not script.exists():
                logger.error(f"Training script not found: {script}")
                return False
            # Use the same Python interpreter
            cmd = [sys.executable, str(script)]
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Retraining failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")
                return False
            logger.info(f"Retraining completed successfully. Output:\n{result.stdout}")
            return True
        except Exception as e:
            logger.exception(f"Error during retraining: {e}")
            return False

if __name__ == "__main__":
    scheduler = TaskScheduler()
    scheduler.schedule_tasks()
