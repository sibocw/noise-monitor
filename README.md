# Neighborhood Noise Monitor
This is a Python program, designed to run on a Raspberry Pi, that
- continuously records audio with external USB microphone,
- only records during preset hours,
- uploads recording to Google Cloud Storage, and
- deletes data after a preset retention period.

Its intended use is a noise monitor. Be careful not to leak the data, as it's literally recordings of your private home.

## User guide
> [!NOTE]
> Specific procedures here (e.g. virtual environment management) can be adopted for your needs.

To install the noise monitor software, first create a Python virtual environment and activate it:
```shell
python -m venv ~/noise_monitor_env
source ~/noise_monitor_env/bin/activate
```

Then, download the noise monitor software from [the GitHub repository](https://github.com/sibocw/noise-monitor) and install it using `pip`:
```shell
git clone git@github.com:sibocw/noise-monitor.git
cd noise_monitor
pip install -e .
```

Modify parameters in `noise_monitor/config.py` as needed. The parameters are explained in comments within this file. 

Then, sign up for [a Google Cloud account](https://cloud.google.com/) and create a project.

> [!IMPORTANT]
> **It's always a good idea to [set a budget limit](https://cloud.google.com/billing/docs/how-to/budgets) on your account!** $5 per month should be more than enough for this project.

Then, create a service account using [Identity and Access Management (IAM)](https://console.cloud.google.com/iam-admin/serviceaccounts). This service account should have `storage.objectAdmin` and `logging.logWriter` roles. Note down this service account's email address. It should follow the format `SERVICE_ACCOUNT_NAME@PROJECT_ID.iam.gserviceaccount.com`.

Next, create a storage bucket on [Google Cloud Storage](https://console.cloud.google.com/storage/overview;tab=overview). Note down the bucket name. We now need to assign the service account to be a manager of the newly create bucket. For this, you will need to [download the `gcloud` command-line interface](https://cloud.google.com/sdk/docs/install-sdk) and run
```shell
gcloud storage buckets add-iam-policy-binding \
    "gs://BUCKET_NAME" \
    --member="SERVICE_ACCOUNT_EMAIL_ADDRESS" \
    --role="roles/storage.objectAdmin"
```

Then, go to the [Service Accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts), click the service account that you have created. Select the "Keys" tab and and create a new key. Download the JSON key file. Save it to a secure place on the file system (e.g. at `~/.gcloud/SERVICE_ACCOUNT_NAME_key.json`), and add the following to the end of `~/.bashrc` (be sure to use the absolute path):
```shell
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

Next, create a `noise_monitor/google_cloud_io.py` file with the following content:
```Python
project_id = "PROJECT_ID"
bucket_name = "YOUR_STORAGE_BUCKET_NAME"
remote_path = "ANY_FOLDER_NAME"  # Path in the bucket to store data
```
**This file is not tracked by Git, and you also shouldn't include it in your version tracker** (though if you did do it, it's not catastrophic. People will just know your project ID and bucket name).

Restart a terminal. Now you are ready to run the recorder. To do so, run
```shell
# Always activate virtual env first
source ~/noise_monitor_env/bin/activate  

# Change into the recorder monitor directory
cd noise_monitor

# Inspect the output of the following command verify that the microphone is listed
python -u scripts/list_audio_devices.py  

# Run recorder program
python -u scripts/run_noise_monitor.py
```
... and let the program run in the background.

To access the recording, go to the [Cloud Storage page](https://console.cloud.google.com/storage/browser) and enter the storage bucket that you created. For diagnosis and monitoring, the logs are streamed to the Google Cloud [Logging service](https://console.cloud.google.com/logs).
