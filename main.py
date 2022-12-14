# pylint: disable=unused-import, import-outside-toplevel

import os
from urllib.request import urlretrieve, urlcleanup

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.video.compositing.transitions import slide_in
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.resize import resize

from compyle.preloader import launch_after_preload
from compyle.services.twitch import TwitchApi


def main():
    api = TwitchApi()

    game_name = "League of Legends"
    # game_name = "VALORANT"
    game_id = api.get_game_id(game_name)
    clips = api.get_game_clips(game_id)

    # import random

    # random.shuffle(clips)

    subclips = []
    subclips_duration = 0

    video = None
    timestamps = ""
    credits = set()

    remote_thumbnail = urlretrieve(clips[0]["thumbnail_url"])[0]
    # todo thumbnail des 4 meilleures

    # todo shuffle
    # todo break si durée au dessus de 10 minutes + historique

    for clip in clips[:2]:
        # retrieve url and download remote file
        url = api.get_clip_url(clip)
        temporary_file, _ = urlretrieve(url)

        # videoclip creation and normalization
        videoclip: VideoFileClip = VideoFileClip(temporary_file)
        videoclip = videoclip.subclip(0, clip["duration"])
        videoclip = videoclip.set_fps(60)
        videoclip = videoclip.fx(resize, width=1920, height=1080)
        videoclip = audio_normalize(videoclip)

        if subclips:
            videoclip = videoclip.fx(fadein, 1)

        # textclip creation and initialisation
        textclip: TextClip = TextClip(clip["broadcaster_name"], fontsize=60, color="white")
        textclip = textclip.set_duration(videoclip.duration)
        textclip = textclip.set_position(("left", "top"))
        textclip = textclip.fx(slide_in, duration=1, side="left")
        # TODO couleur

        # composite clip append to subclips
        composite = CompositeVideoClip([videoclip, textclip])
        subclips.append(composite)

        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        timestamps += f"{timestamp} {clip['broadcaster_name']}\n"
        subclips_duration += videoclip.duration

        x = "https://www.twitch.tv/" + clip["broadcaster_name"]
        credit = f"{clip['broadcaster_name']} - {x}"
        credits.add(credit)

        # close the clip https://zulko.github.io/moviepy/getting_started/efficient_moviepy.html
        videoclip.close()

    if subclips:
        # to be remove to when remote download is fixed
        local_file = "clips.mp4"
        if os.path.exists(local_file):
            os.remove(local_file)

        video: CompositeVideoClip = concatenate_videoclips(subclips, method="compose", padding=-1)
        video.write_videofile(local_file, codec="libx264", audio_codec="aac", verbose=False)

        # try:
        #     import pygame

        #     pygame.init()
        #     pygame.display.set_caption("Show Video on screen")

        #     video.audio.fps = 44_100
        #     video = video.resize((620, 480))
        #     video.preview(fps=60, audio=True, audio_fps=44_100)

        #     pygame.quit()
        # except ImportError:

        # #     pass  # set try/catch here for jupiter notebook, and then write_videofile
        # # finally:
        # # video.close()
        description = "🎥 Credits:\n" + "\n".join(credits) + "\n\n⌚ Timestamps:\n" + timestamps
        print(description)
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

# youtube upload https://github.com/ClarityCoders/AutoTube/blob/master/utils/upload_video.py
