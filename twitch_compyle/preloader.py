import logging

import dotenv

    
def launch_after_preload(method_callback, *args, **kwargs):
    logging.basicConfig(level=logging.DEBUG)
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Loading variables from {dotenv.find_dotenv()}")

    dotenv.load_dotenv()
    
    return method_callback(*args, **kwargs)
