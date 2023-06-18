import logging
import os

from moviepy import config


def launch_after_preload(method_callback, *args, **kwargs):
    logging.getLogger("PIL.PngImagePlugin").setLevel(logging.WARNING)
    # logging.getLogger("moviepy.editor").setLevel(logging.WARNING)
    logging.getLogger("imageio_ffmpeg").setLevel(logging.CRITICAL)

    # print(config.get_setting("IMAGEMAGICK_BINARY"))
    # config.change_settings({"IMAGEMAGICK_BINARY": r"/bin/convert"})

    if not config.get_setting("IMAGEMAGICK_BINARY"):
        # logger.warning("IMAGEMAGICK_BINARY not found, please install imagemagick or set IMAGEMAGICK_BINARY in .env")
        # config.change_settings({"IMAGEMAGICK_BINARY": r"/bin/convert"})  # pour ubuntu
        dir = os.path.basename(os.path.dirname(__file__))
        # todo message pas bien warn
