import pathlib
import logging
from typing import Set
from google.cloud import storage
from noise_monitor.logger import CloudLogger


logger = CloudLogger(logging.getLogger(), {"worker": "synchronizer"})


def sync_files(local_path: pathlib.Path, remote_path: str, bucket_name: str) -> None:
    """
    Sync local folder to Google Cloud Storage bucket unidirectionally.

    Args:
        local_path: Local folder path to sync
        remote_path: Remote path prefix in the bucket
            (e.g., 'folder1/subfolder')
        bucket_name: GCS bucket name
    """
    # Initialize the GCS client
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    # Ensure remote_path ends with '/' if not empty
    if remote_path and not remote_path.endswith("/"):
        remote_path += "/"

    # Get all local files relative to local_path
    local_files: Set[str] = set()
    if local_path.exists():
        for file_path in local_path.rglob("*"):
            if file_path.is_file() and file_path.name[0] != ".":  # Skip hidden files
                relative_path = file_path.relative_to(local_path).as_posix()
                local_files.add(relative_path)

    # Get all remote files with the given prefix
    remote_files: Set[str] = set()
    blobs = bucket.list_blobs(prefix=remote_path)
    for blob in blobs:
        # Remove the remote_path prefix to get relative path
        if blob.name.startswith(remote_path):
            relative_path = blob.name[len(remote_path) :]
            if relative_path:  # Skip empty strings (folder markers)
                remote_files.add(relative_path)

    # Files to upload (exist locally but not remotely)
    files_to_upload = local_files - remote_files

    # Files to delete (exist remotely but not locally)
    files_to_delete = remote_files - local_files

    # Upload new/missing files
    for relative_path in files_to_upload:
        local_file = local_path / relative_path
        blob_name = remote_path + relative_path
        blob = bucket.blob(blob_name)

        logger.info(f"Uploading: {relative_path}")
        blob.upload_from_filename(str(local_file))

    # Delete removed files
    for relative_path in files_to_delete:
        blob_name = remote_path + relative_path
        blob = bucket.blob(blob_name)

        logger.info(f"Deleting: {relative_path}")
        blob.delete()

    if files_to_upload or files_to_delete:
        logger.info(
            f"Sync complete. Uploaded: {len(files_to_upload)}, "
            f"deleted: {len(files_to_delete)}"
        )
    else:
        logger.info("No changes detected.")
