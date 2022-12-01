import logging

import dotenv


def launch_after_preload(method_callback, *args, **kwargs):
    logging.basicConfig(level=logging.DEBUG)

    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.debug("Loading variables from %s", dotenv.find_dotenv())

    dotenv.load_dotenv()

    return method_callback(*args, **kwargs)
