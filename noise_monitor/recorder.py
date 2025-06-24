import sounddevice as sd
import soundfile as sf
import pathlib
import datetime
import yaml
import logging
from typing import Optional

from noise_monitor.logger import CloudLogger


logger = CloudLogger(logging.getLogger(), {"worker": "recorder"})


def list_audio_input_devices() -> list[tuple[int, str, int]]:
    """
    List all available audio input devices.

    Returns:
        List of tuples containing (device_name, max_input_channels)
    """
    input_devices = []
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        # Only include devices that can record (have input channels)
        if device["max_input_channels"] > 0:
            device_name = device["name"]
            max_input_channels = device["max_input_channels"]
            input_devices.append((i, device_name, max_input_channels))

    return input_devices


def record_audio_clip(
    device_id: int,
    length: int,
    output_dir: pathlib.Path,
    sample_rate: int,
    channels: int,
    dtype: str,
    chunk_size: int,
) -> Optional[pathlib.Path]:
    """
    Record an audio clip from the specified device.

    Args:
        device_id: Index of the audio input device
        length: Recording length in seconds
        output_dir: Directory where the audio file should be saved
        sample_rate: Sample rate in Hz (eg: 48000 for high quality)
        channels: Number of audio channels (eg: 2 for stereo)
        dtype: Audio data type ('int16', 'int32', or 'float32')
        blocksize: Size of audio blocks (eg. 4096)

    Returns:
        Path to the saved audio file if successful, None otherwise
    """
    # Validate device exists and supports input
    try:
        devices = sd.query_devices()
        if device_id >= len(devices):
            logger.critical(f"Error: Device ID {device_id} does not exist")
            return None

        device_info = devices[device_id]
        if device_info["max_input_channels"] == 0:
            logger.critical(f"Error: Device {device_id} does not support audio input")
            return None
    except Exception as e:
        logger.critical(f"Error querying device {device_id}: {e}")
        return None

    # Validate channels don't exceed device capability
    if channels > device_info["max_input_channels"]:
        logger.critical(
            f"Error: Requested {channels} channels, "
            f"but device only supports {device_info['max_input_channels']}"
        )
        return None

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Record start time for metadata
    start_time = datetime.datetime.now()

    # Try recording with preferred dtype, fallback if needed
    actual_dtype = dtype
    audio_data = None

    logger.info(f"Recording for {length} seconds...")
    audio_data = sd.rec(
        frames=int(length * sample_rate),
        samplerate=sample_rate,
        channels=channels,
        dtype=dtype,
        device=device_id,
        blocking=True,
    )

    if audio_data is None:
        logger.critical("Error: Recording failed, no audio data captured")
        return None

    # Save to audio file using soundfile
    try:
        bit_depth, pcm_type = get_bit_depth_and_pcm_type(actual_dtype)

        # Save audio file
        sf.write(
            str(output_dir / (output_dir.name + ".wav")),
            audio_data,
            sample_rate,
            subtype=pcm_type,
        )

        # Add metadata as YAML file
        metadata_path = output_dir / (output_dir.name + ".yaml")
        metadata = {
            "audio_recording_metadata": {
                "recording_started": start_time.isoformat(),
                "duration_seconds": length,
                "device": {
                    "id": device_id,
                    "name": device_info["name"],
                    "max_input_channels": device_info["max_input_channels"],
                    "default_samplerate": device_info["default_samplerate"],
                },
                "audio_settings": {
                    "sample_rate_hz": sample_rate,
                    "channels": channels,
                    "dtype": actual_dtype,
                    "bit_depth": bit_depth,
                    "blocksize": chunk_size,
                    "subtype": pcm_type,
                },
                "output_file": {
                    "filename": output_dir.name,
                    "full_path": str(output_dir.absolute()),
                },
                "library_info": {
                    "backend": "sounddevice",
                    "soundfile_version": sf.__version__,
                    "sounddevice_version": sd.__version__,
                },
            }
        }

        with open(metadata_path, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False, indent=2)

        logger.info(f"Recording saved to: {output_dir}")
        logger.info(f"Metadata saved to: {metadata_path} (YAML format)")
        return output_dir

    except Exception as e:
        logger.critical(f"Error saving audio file: {e}")
        return None


def get_device_id_by_name(name: str) -> int:
    """
    Find the audio input device ID by name (substring match).

    Args:
        name: Substring to match against device names

    Returns:
        Device ID if found, -1 otherwise
    """
    devices = list_audio_input_devices()
    for device_id, device_name, _ in devices:
        if name.lower() in device_name.lower():
            return device_id
    return -1


def get_bit_depth_and_pcm_type(dtype: str) -> tuple[int, str]:
    if dtype == "int16":
        bit_depth = 16
        subtype = "PCM_16"
    elif dtype == "int24":
        bit_depth = 24
        subtype = "PCM_24"
    elif dtype == "int32":
        bit_depth = 32
        subtype = "PCM_32"
    elif dtype == "float32":
        bit_depth = 32
        subtype = "FLOAT"
    else:
        raise ValueError(f"Unsupported dtype: {dtype}")
    return bit_depth, subtype
