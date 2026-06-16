import logging

base_name = "cosmetics"
def setup_logging():
    # Silence root (and all libraries like PIL)
    logging.getLogger().setLevel(logging.WARNING)

    app_logger = logging.getLogger(base_name)
    app_logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s]: %(name)s - %(message)s")

    # File handler
    file_handler = logging.FileHandler("variety.log", mode="w")
    file_handler.setFormatter(formatter)

    # Console handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    app_logger.addHandler(file_handler)
    app_logger.addHandler(stream_handler)

def get_logger(moudle_name:str | None = None):
    moudle_name = moudle_name or ""
    return logging.getLogger(f"{base_name}.{moudle_name.split(".")[-1]}")