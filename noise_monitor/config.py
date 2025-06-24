# IO
device_name = "Yeti Stereo Microphone"  # Name of audio input device (substring is OK)
data_dir = "/home/pi/noise_monitor/data"
retention_period = 48 * 3600  # seconds, data older than this will be deleted
upload_delay = 3  # seconds, sync data to could this many secs after each clip is saved

# Recording
sample_rate = 48000  # Hz
clip_length = 300  # seconds, must be a factor of 3600 (1h)
channels = 2  # stereo
chunk_size = 4096  # number of frames per
format = "int32"  # bits per sample
recording_hours = [17, 23, 0, 1, 2, 3, 4, 5, 6, 7]  # hours of the day to record
