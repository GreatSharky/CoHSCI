import logging

logger = logging.getLogger(__name__)
console_handler = logging.StreamHandler()

logger.addHandler(console_handler)
formatter = logging.Formatter(
    "{logger.parent} - {asctime} - {levelname} - {message}",
    style="{",
    datefmt="%Y-%m-%d %H:%M:%S",
)

console_handler.setFormatter(formatter)
logger.warning("Hello World!")