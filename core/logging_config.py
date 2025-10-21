# logging_config.py
import logging
import sys

def setup_logging(level: str = "INFO"):
    fmt = (
        '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
        '"module": "%(name)s", "message": "%(message)s"}'
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt))
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]
