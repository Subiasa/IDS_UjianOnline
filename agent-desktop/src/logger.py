import logging
import sys
import os

def setup_logger():
    logger = logging.getLogger("HIDSAgent")
    logger.setLevel(logging.DEBUG)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    
    # File Handler
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    fh = logging.FileHandler(os.path.join(log_dir, "agent.log"))
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)

    logger.addHandler(ch)
    logger.addHandler(fh)
    
    return logger

logger = setup_logger()
