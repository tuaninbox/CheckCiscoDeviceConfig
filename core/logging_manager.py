from config.logging_config import LOGGING_CONFIG
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler
import logging

def setup_loggers(logger_name: str = "default", mode: str = "both"):
    """
    Create success and fail loggers with support for module-specific, master-only, or both.
    
    Args:
        logger_name (str): Name of the logger (e.g. 'getconfig', 'gitrepo').
        mode (str): 'module', 'master', or 'both' to control log destinations.
    
    Returns:
        (success_logger, fail_logger)
    """
    log_dir = Path(LOGGING_CONFIG["logdir"])
    log_dir.mkdir(parents=True, exist_ok=True)

    # --- Success logger ---
    success_logger = logging.getLogger(f"{logger_name}_success")
    success_logger.setLevel(logging.INFO)
    success_logger.handlers.clear()

    formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')

    if mode in ("module", "both"):
        success_handler = TimedRotatingFileHandler(
            log_dir / f"{logger_name}_{LOGGING_CONFIG['success_logfile']}",
            when=LOGGING_CONFIG["rotation"]["when"],
            interval=LOGGING_CONFIG["rotation"]["interval"],
            backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
        )
        success_handler.setFormatter(formatter)
        success_logger.addHandler(success_handler)

    if mode in ("master", "both"):
        master_success_handler = TimedRotatingFileHandler(
            log_dir / f"master_{LOGGING_CONFIG['success_logfile']}",
            when=LOGGING_CONFIG["rotation"]["when"],
            interval=LOGGING_CONFIG["rotation"]["interval"],
            backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
        )
        master_success_handler.setFormatter(formatter)
        success_logger.addHandler(master_success_handler)

    if LOGGING_CONFIG["console"]:
        success_logger.addHandler(logging.StreamHandler())

    # --- Fail logger ---
    fail_logger = logging.getLogger(f"{logger_name}_fail")
    fail_logger.setLevel(logging.ERROR)
    fail_logger.handlers.clear()

    if mode in ("module", "both"):
        fail_handler = TimedRotatingFileHandler(
            log_dir / f"{logger_name}_{LOGGING_CONFIG['fail_logfile']}",
            when=LOGGING_CONFIG["rotation"]["when"],
            interval=LOGGING_CONFIG["rotation"]["interval"],
            backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
        )
        fail_handler.setFormatter(formatter)
        fail_logger.addHandler(fail_handler)

    if mode in ("master", "both"):
        master_fail_handler = TimedRotatingFileHandler(
            log_dir / f"master_{LOGGING_CONFIG['fail_logfile']}",
            when=LOGGING_CONFIG["rotation"]["when"],
            interval=LOGGING_CONFIG["rotation"]["interval"],
            backupCount=LOGGING_CONFIG["rotation"]["backupCount"]
        )
        master_fail_handler.setFormatter(formatter)
        fail_logger.addHandler(master_fail_handler)

    if LOGGING_CONFIG["console"]:
        fail_logger.addHandler(logging.StreamHandler())

    return success_logger, fail_logger
