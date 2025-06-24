import google.cloud.logging
from logging import LoggerAdapter

# Set up Google Cloud logging
client = google.cloud.logging.Client()
client.setup_logging()


# Create a LoggerAdapter to inject custom fields
class CloudLogger(LoggerAdapter):
    def process(self, msg, kwargs):
        print(msg)
        kwargs["extra"] = {"worker": self.extra.get("worker", "unknown")}
        return msg, kwargs
