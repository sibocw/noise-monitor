from setuptools import setup

setup(
    name="noise_monitor",
    version="0.1",
    packages=["noise_monitor"],
    install_requires=[
        "sounddevice==0.5.2",
        "soundfile==0.13.1",
        "pyyaml==6.0.2",
        "google-cloud-storage==3.1.1",
        "google-cloud-logging==3.12.1",
    ],
)
