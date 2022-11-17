import logging

import uvicorn


###### Logging

LOG_FORMAT: str = "%(levelprefix)s %(asctime)s | %(message)s"

def init_debug_logger(logger_name: str = "logger"):
    """
    For use in development. Logging config should be updated before production deployment.
    """
    # create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.handlers = []
    
    # create console handler and set level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    formatter = uvicorn.logging.DefaultFormatter(LOG_FORMAT, datefmt="%Y-%m-%d %H:%M:%S")

    ch.setFormatter(formatter)

    logger.addHandler(ch)
    
