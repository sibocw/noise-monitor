import logging
from time import sleep
from datetime import datetime
from pathlib import Path
from multiprocessing import Process
from noise_monitor import recorder, cloud_sync, data_lifecycle, utils
from noise_monitor import config, google_cloud_io
from noise_monitor.logger import CloudLogger


logger = CloudLogger(logging.getLogger(), {"worker": "main"})


def run_recorder():
    # Find device
    device_id = recorder.get_device_id_by_name(config.device_name)
    if device_id == -1:
        logger.critical(f"Error: Device '{config.device_name}' not found.")
        return
    data_dir = Path(config.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    recording_state = True

    # Run recording loop
    while True:
        current_time = datetime.now()
        if current_time.hour not in config.recording_hours:
            if recording_state:
                logger.info("Recording stopped due to outside recording hours.")
                recording_state = False
            sleep(60)  # Check every minute
            continue
        else:
            if not recording_state:
                logger.info("Recording started again.")
                recording_state = True

        output_dir = data_dir / current_time.strftime("%Y-%m-%d-%H-%M-%S")
        block_end_time = utils.get_ending_time(current_time, config.clip_length)
        duration = (block_end_time - current_time).total_seconds()
        logger.info(
            f"Recording for {duration} seconds until "
            f"{block_end_time.strftime('%Y-%m-%d %H:%M:%S')}..."
        )
        output_path = recorder.record_audio_clip(
            device_id=device_id,
            length=duration,
            output_dir=output_dir,
            sample_rate=config.sample_rate,
            channels=config.channels,
            dtype=config.format,
            chunk_size=config.chunk_size,
        )
        if output_path is None:
            logger.error("Recording failed, retrying after 1 min...")
            sleep(60)  # Wait before retrying
            continue
        else:
            logger.info(f"Recording saved to {output_path}")


def run_sync_loop() -> None:
    logger.info(
        f"Starting sync loop from local path '{config.data_dir}' to remote path "
        f"'gs://{google_cloud_io.bucket_name}/{google_cloud_io.remote_path}'"
    )

    while True:
        current_time = datetime.now()
        next_sync_time = utils.get_ending_time(
            current_time=current_time,
            clip_length=config.clip_length,
            offset=config.upload_delay,
        )
        logger.info(
            f"Next sync scheduled at {next_sync_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        sleep((next_sync_time - current_time).total_seconds())
        cloud_sync.sync_files(
            local_path=Path(config.data_dir),
            remote_path=google_cloud_io.remote_path,
            bucket_name=google_cloud_io.bucket_name,
        )


def run_cleanup_loop() -> None:
    logger.info(
        f"Starting cleanup loop for directory '{config.data_dir}' "
        f"with retention period {config.retention_period} seconds"
    )

    while True:
        current_time = datetime.now()
        next_sync_time = utils.get_ending_time(
            current_time=current_time,
            clip_length=config.clip_length,
        )
        logger.info(
            f"Next clean-up scheduled at {next_sync_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        sleep((next_sync_time - current_time).total_seconds())
        data_lifecycle.delete_old_files(
            directory=Path(config.data_dir),
            retention_period=config.retention_period,
        )


if __name__ == "__main__":
    processes = [
        Process(target=run_recorder),
        Process(target=run_sync_loop),
        Process(target=run_cleanup_loop),
    ]

    for p in processes:
        p.start()

    for p in processes:
        p.join()
