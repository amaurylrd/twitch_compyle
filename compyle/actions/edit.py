import os
from typing import Optional

from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.editor import (
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.compositing.transitions import crossfadein, slide_in
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.resize import resize

from compyle.services.databases.mongo import MongoDB


def get_latest_file(path: os.PathLike) -> Optional[str]:
    """Returns the most recent file that has been created in the specified folder path.

    Args:
        path (os.PathLike): the path to the directory.

    Returns:
        Optional[str]: the path to the most recent file if any, otherwise `None`.
    """
    # checks if the specified path is an existing directory
    if path and os.path.isdir(path):
        # gets the file in the specified path with the latest creation time
        return max((os.path.join(path, basename) for basename in os.listdir(path)), key=os.path.getctime, default=None)
    return None


def edit(*, _input: Optional[str] = None, output: Optional[str] = None):
    if _input is None:
        # loads data from the database
        with MongoDB() as mongo_db:
            clips = mongo_db.get_documents("clips")  # todo filter ceux non utilisé pour des clips

        pass
    else:
        # stores the clips data in the filesystem
        if output.endswith("/") or os.path.isdir(output):
            output = get_latest_file(output)

        # soit c'est un fichier soit un dossier
        pass

    print("edit", input, output)
    # TODO laoder

    # for clip in clips[2:4]:
    #     # 1. retrieve clip url and download clip file
    #     url = api.get_clip_url(clip)
    #     temporary_file = urlretrieve(url)[0]

    #     # 2. videoclip creation and normalization
    #     videoclip: VideoFileClip = VideoFileClip(temporary_file)
    #     videoclip = videoclip.subclip(0, clip["duration"])
    #     videoclip = videoclip.set_fps(60)
    #     videoclip = videoclip.fx(resize, width=1920, height=1080)
    #     videoclip = audio_normalize(videoclip)
