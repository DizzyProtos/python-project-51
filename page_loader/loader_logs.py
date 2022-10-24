import logging
from logging.handlers import RotatingFileHandler


def _setup_logger():
    logger = logging.getLogger('Rotating Log')
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler('loader.log', backupCount=5)
    logger.addHandler(handler)
    return logger


logger = _setup_logger()
