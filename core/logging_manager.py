from config.logging_config import LOGGING_CONFIG
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import logging

# Configure logging once, ideally at app startup
def setup_loggers():
    log_dir = Path(LOGGING_CONFIG["logdir"])
    log_dir.mkdir(parents=True, exist_ok=True)

    # Success logger
    success_logger = logging.getLogger("success_logger")
    success_logger.setLevel(logging.INFO)
    success_logger.handlers.clear()   # clear old handlers

    success_handler = TimedRotatingFileHandler(
        log_dir / LOGGING_CONFIG["success_logfile"],
        when=LOGGING_CONFIG["rotation"]["when"],
        interval=LOGGING_CONFIG["rotation"]["interval"],
        backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
    )
    success_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    success_logger.addHandler(success_handler)

    if LOGGING_CONFIG["console"]:
        success_logger.addHandler(logging.StreamHandler())

    # Error logger
    fail_logger = logging.getLogger("fail_logger")
    fail_logger.setLevel(logging.ERROR)
    fail_logger.handlers.clear()   # clear old handlers

    fail_handler = TimedRotatingFileHandler(
        log_dir / LOGGING_CONFIG["fail_logfile"],
        when=LOGGING_CONFIG["rotation"]["when"],
        interval=LOGGING_CONFIG["rotation"]["interval"],
        backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
    )
    fail_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
    fail_logger.addHandler(fail_handler)

    if LOGGING_CONFIG["console"]:
        fail_logger.addHandler(logging.StreamHandler())

    return success_logger, fail_logger