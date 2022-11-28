from compyle.api.twitch import TwitchAPI
from compyle.preloader import launch_after_preload

import os
import os.path
import random
import shutil
from moviepy.editor import *
import requests
import urllib.request


def main():
    twitch_api = TwitchAPI()
    games = twitch_api.get_top_games()

    dir_path = "./tmp/"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)

    streamers = []
    for game in games:
        if game["name"] != "League of Legends":
            continue

        clips = twitch_api.get_games_clips(game["id"])

        # clips.sort(key=lambda clip: clip["created_at"], reverse=True)

        i = 0
        for clip in clips:
            if clip["language"] == "fr":
                streamers.append(clip["broadcaster_name"])
            continue
            # print(clip["title"], clip["created_at"], clip["view_count"])

            # if i >= 1:
            #     break

            if clip["language"] not in ["fr"] or clip["duration"] > 25:
                continue

            url = clip["url"]
            i += 1
            thumbnail_url = clip["thumbnail_url"]
            thumbnail = thumbnail_url.index("-preview-")
            url = thumbnail_url[:thumbnail] + ".mp4"

            print(url)

            # reporthook=get_progress
            #         def get_progress(count, block_size, total_size) -> None:
            # percent = int(count * block_size * 100 / total_size)
            # print(f"Downloading clip... {percent}%", end="\r", flush=True)
            # regex = re.compile("[^a-zA-Z0-9_]")
            file_path = dir_path + clip["title"] + ".mp4"
            urllib.request.urlretrieve(url, file_path)

    videoclips = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)

        if os.path.isfile(file_path) and file.endswith(".mp4"):
            videoclip = VideoFileClip(file_path).fx(afx.audio_normalize)

            textclip: TextClip = TextClip(txt=file, color="white", fontsize=30)
            textclip: TextClip = textclip.set_duration(videoclip.duration)
            textclip: TextClip = textclip.set_position(("left", "top"))
            textclip = textclip.on_color(color=(145, 70, 255))
            # .set_start(0.5)
            compositeclip = CompositeVideoClip([videoclip, textclip])
            print(compositeclip, compositeclip.duration)
            videoclips.append(compositeclip)

    print(len(clips), streamers)

    if videoclips:
        # random.shuffle(audioclips)

        videoclip = concatenate_videoclips(videoclips)
        videoclip.write_videofile(
            "all_clips.mp4",
            fps=24,
            codec="libx264",
        )
        print("done")
    print("pas done")


if __name__ == "__main__":
    launch_after_preload(main)
