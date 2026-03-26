import os
import logging
import random

from dotenv import load_dotenv

from locust import FastHttpUser, task, tag, constant

ENV_FILE = os.getenv("ENV_FILE")
if ENV_FILE is not None:
    load_dotenv(dotenv_path=ENV_FILE)
else:
    load_dotenv()

APP_ADDRESS = os.getenv("APP_ADDRESS")

# MIN_WAIT = int(os.getenv("MIN_WAIT") or 0.2)
# MAX_WAIT = int(os.getenv("MAX_WAIT") or 1)

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

SMALL_PAYLOAD = random.randbytes(32768)
MEDIUM_PAYLOAD = random.randbytes(262144)
LARGE_PAYLOAD = random.randbytes(1048576)


class InspectUser(FastHttpUser):
    weight = 1 # in relation to other Users
    # wait_time = between(MIN_WAIT, MAX_WAIT)
    wait_time = constant(1)

    @tag('empty')
    @task
    def empty_inspect(self):
        LOGGER.info(f"Sending empty inspect to app {APP_ADDRESS}")
        with self.rest("POST", f"/inspect/{APP_ADDRESS}") as resp:
            if resp.js is None:
                pass # no need to do anything, already marked as failed
            elif "status" not in resp.js or "processed_input_count" not in resp.js:
                resp.failure(f"Not valid response response {resp.text}")
            else:
                LOGGER.info(f"   empty inspect reponse for {APP_ADDRESS} has processed inputs = {resp.js['processed_input_count']}")

    @tag('small')
    @task
    def small_inspect(self):
        LOGGER.info(f"Sending empty inspect to app {APP_ADDRESS}")
        with self.rest("POST", f"/inspect/{APP_ADDRESS}",data=SMALL_PAYLOAD) as resp:
            if resp.js is None:
                pass # no need to do anything, already marked as failed
            elif "status" not in resp.js or "processed_input_count" not in resp.js:
                resp.failure(f"Not valid response response {resp.text}")
            else:
                LOGGER.info(f"   empty inspect reponse for {APP_ADDRESS} has processed inputs = {resp.js['processed_input_count']}")

    @tag('medium')
    @task
    def medium_inspect(self):
        LOGGER.info(f"Sending empty inspect to app {APP_ADDRESS}")
        with self.rest("POST", f"/inspect/{APP_ADDRESS}",data=MEDIUM_PAYLOAD) as resp:
            if resp.js is None:
                pass # no need to do anything, already marked as failed
            elif "status" not in resp.js or "processed_input_count" not in resp.js:
                resp.failure(f"Not valid response response {resp.text}")
            else:
                LOGGER.info(f"   empty inspect reponse for {APP_ADDRESS} has processed inputs = {resp.js['processed_input_count']}")

    @tag('large')
    @task
    def large_inspect(self):
        LOGGER.info(f"Sending empty inspect to app {APP_ADDRESS}")
        with self.rest("POST", f"/inspect/{APP_ADDRESS}",data=LARGE_PAYLOAD) as resp:
            if resp.js is None:
                pass # no need to do anything, already marked as failed
            elif "status" not in resp.js or "processed_input_count" not in resp.js:
                resp.failure(f"Not valid response response {resp.text}")
            else:
                LOGGER.info(f"   empty inspect reponse for {APP_ADDRESS} has processed inputs = {resp.js['processed_input_count']}")
