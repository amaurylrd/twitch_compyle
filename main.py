# pylint: disable=unused-import, import-outside-toplevel

import os
from urllib.request import urlretrieve, urlcleanup

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.video.compositing.transitions import slide_in
from moviepy.video.fx.resize import resize

from compyle.preloader import launch_after_preload
from compyle.services.twitch import TwitchApi


def main():
    api = TwitchApi()

    game_name = "League of Legends"
    game_name = "VALORANT"
    game_id = api.get_game_id(game_name)
    clips = api.get_game_clips(game_id)

    # import random

    # random.shuffle(clips)

    subclips = []
    subclips_duration = 0

    video = None
    description = ""
    remote_thumbnail = urlretrieve(clips[0]["thumbnail_url"])[0]

    for clip in clips:
        # retrieve url and download remote file
        url = api.get_clip_url(clip)
        temporary_file, _ = urlretrieve(url)

        # videoclip creation and normalization
        videoclip: VideoFileClip = VideoFileClip(temporary_file)
        videoclip = videoclip.subclip(0, clip["duration"])
        videoclip = videoclip.set_fps(60)
        videoclip = videoclip.fx(resize, width=1920, height=1080)
        videoclip = audio_normalize(videoclip)

        # textclip creation and initialisation
        textclip: TextClip = TextClip(clip["broadcaster_name"], fontsize=60, color="white")
        textclip = textclip.set_duration(videoclip.duration)
        textclip = textclip.set_position(("left", "top"))
        textclip = textclip.fx(slide_in, duration=1, side="left")
        # TODO couleur

        # composite clip append to subclips
        composite = CompositeVideoClip([videoclip, textclip])
        # videoclip.crossfadein(1)
        subclips.append(composite)

        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        description += f"{timestamp} {clip['broadcaster_name']}\n"
        subclips_duration += videoclip.duration

        # when to close a clip https://zulko.github.io/moviepy/getting_started/efficient_moviepy.html
        videoclip.close()

    if subclips:
        # to be remove to when remote download is fixed
        local_file = "clips.mp4"
        if os.path.exists(local_file):
            os.remove(local_file)

        video: CompositeVideoClip = concatenate_videoclips(subclips, method="compose")

        # try:
        #     import pygame

        #     video.show(interactive=True)
        # except ImportError:
        video.write_videofile(local_file, codec="libx264", audio_codec="aac", verbose=False)
        #     pass  # set try/catch here for jupiter notebook, and then write_videofile
        # finally:
        video.close()

    urlcleanup()

    # require to have Pygame
    # is_interactive = False
    # try:
    #     from IPython import get_ipython

    #     is_interactive = get_ipython() is not None
    # except Exception:
    #     pass
    # IPython Notebook
    # video.ipython_display()

    # todo shuffle + pas deux fois le meme streamer à la suite ?


if __name__ == "__main__":
    launch_after_preload(main)
