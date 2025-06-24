from noise_monitor.recorder import list_audio_input_devices


if __name__ == "__main__":
    # List available audio input devices
    print("Available audio input devices:")
    devices = list_audio_input_devices()
    for device_id, name, channels in devices:
        print(f"Device {device_id}: {name} (max {channels} channels)")

    if not devices:
        print("No audio input devices found.")
