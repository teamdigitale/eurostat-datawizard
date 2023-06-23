import os

LOGGING_FORMAT = "%(asctime)s - %(message)s"
ROOT_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), ".."))
CACHE_PATH = os.path.join(ROOT_PATH, "cache")
