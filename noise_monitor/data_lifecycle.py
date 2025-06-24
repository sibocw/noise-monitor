import shutil
import logging
from pathlib import Path
from datetime import datetime, timedelta
from noise_monitor.logger import CloudLogger

logger = CloudLogger(logging.getLogger(), {"worker": "janitor"})


def delete_old_files(directory: Path, retention_period: int):
    now = datetime.now()
    cutoff_time = now - timedelta(seconds=retention_period)

    for item in directory.iterdir():
        if item.is_dir():
            try:
                folder_time = datetime.strptime(item.name, "%Y-%m-%d-%H-%M-%S")
                if folder_time < cutoff_time:
                    shutil.rmtree(item)
                    logger.info(f"Deleted old folder: {item.name}")
            except ValueError:
                # Ignore folders that don't match the naming convention
                pass
