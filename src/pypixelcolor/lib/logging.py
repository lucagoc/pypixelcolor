import logging


def setup_logging(level: str = "INFO") -> None:
    log_format = '%(levelname)s [%(asctime)s] [%(name)s] %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    formatter = logging.Formatter(log_format, datefmt=date_format)
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    logging.basicConfig(level=level, handlers=[handler], force=True)