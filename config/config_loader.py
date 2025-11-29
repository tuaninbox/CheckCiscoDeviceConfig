import configparser
from pathlib import Path
from core.logging_manager import setup_loggers

success_logger, fail_logger = setup_loggers(logger_name="config_loader")

CONFIG_FILE = "config/config.ini"
_config_cache = None

def _get_config():
    global _config_cache
    if _config_cache is None:
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        _config_cache = config
    return _config_cache

def load_account_config():
    try:
        config = _get_config()
        account_config_file = Path(config["account"]["account_config_file"]).expanduser()
    except KeyError as e:
        fail_logger.error(f"{CONFIG_FILE} missing required section: {e}")
        raise
    return account_config_file

def load_nagios_config():
    try:
        config = _get_config()
        nagios_config_file = Path(config["nagios"]["nagios_config_file"]).expanduser()
    except KeyError as e:
        fail_logger.error(f"{CONFIG_FILE} missing required section: {e}")
        raise
    return nagios_config_file

def load_backup_config():
    try:
        config = _get_config()
        backup_dir = Path(config["gitrepo"]["backup_dir"]).expanduser()
    except KeyError as e:
        fail_logger.error(f"{CONFIG_FILE} missing required section: {e}")
        raise
    return backup_dir

