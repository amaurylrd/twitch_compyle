# pylint: disable=unused-import, import-outside-toplevel, invalid-name

import os
from urllib.request import urlcleanup, urlretrieve

import cv2
import PIL.Image as pil
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.editor import (
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
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

    subimages = []
    subimages_broadcasters = []

    video = None
    timestamps = ""
    credits = set()

    # todo thumbnail des 4 meilleures
    # TODO couleur
    # todo shuffle, pas deux même streamers de suite
    # todo break si durée au dessus de 10 minutes + historique

    urlcleanup()  # clear cache

    for clip in clips[:10]:
        # 1. retrieve clip url and download clip file
        url = api.get_clip_url(clip)
        temporary_file, _ = urlretrieve(url)

        # 2. videoclip creation and normalization
        videoclip: VideoFileClip = VideoFileClip(temporary_file)
        videoclip = videoclip.subclip(0, clip["duration"])
        videoclip = videoclip.set_fps(60)
        videoclip = videoclip.fx(resize, width=1920, height=1080)
        videoclip = audio_normalize(videoclip)

        # 3. textclip creation
        textclip: TextClip = TextClip(clip["broadcaster_name"], fontsize=60, color="white")
        textclip = textclip.set_duration(videoclip.duration)
        textclip = textclip.set_position(("left", "top"))
        textclip = textclip.fx(slide_in, duration=1, side="left")

        # 4. append composite clip to subclips
        composite: CompositeVideoClip = CompositeVideoClip([videoclip, textclip])
        subclips.append(composite.fx(fadein, 1) if subclips else composite)

        def get_faces(image: cv2.Mat):
            image: cv2.Mat = cv2.resize(image, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

            grayscale: cv2.Mat = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            grayscale: cv2.Mat = cv2.equalizeHist(grayscale)

            cascade: str = "./opencv/haarcascades/frontalface.xml"
            classifier: cv2.CascadeClassifier = cv2.CascadeClassifier(cascade)

            return classifier.detectMultiScale(
                grayscale,
                scaleFactor=1.3,
                minNeighbors=4,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        # 5. face detection for thumbnail
        if len(subimages) < 4 and clip["broadcaster_name"] not in subimages_broadcasters:
            image = cv2.imread(urlretrieve(clip["thumbnail_url"])[0])
            faces = get_faces(image)

            i = 0
            while len(faces) < 1 and i < videoclip.duration:
                image = videoclip.get_frame(i)
                faces = get_faces(image)
                i += 1

            if len(faces) > 0:
                x, y, w, h = tuple(int(coord * 2) for coord in faces[0])
                center = x + w // 2, y + h // 2

                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                matrix = cv2.getRotationMatrix2D(center, 0, 2.0)
                image = cv2.warpAffine(image, matrix, image.shape[1::-1], flags=cv2.INTER_LINEAR)

                subimages.append(image)
                subimages_broadcasters.append(clip["broadcaster_name"])

                cv2.imwrite(f"./opencv/image-{len(subimages)}.png", image)

        # description
        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        timestamps += f"{timestamp} {clip['broadcaster_name']}\n"
        subclips_duration += videoclip.duration

        credit = f"{clip['broadcaster_name']} - https://www.twitch.tv/{clip['broadcaster_name']}"
        credits.add(credit)

        videoclip.close()

    if subclips:
        thumbnail = pil.new("RGB", (1920, 1080))
        width, height = tuple(size // 2 for size in thumbnail.size)

        for i, subimage in enumerate(subimages):
            border = [30] * 4
            color = (145, 70, 255)
            subimage = cv2.resize(subimage, (width, height))
            subimage = cv2.copyMakeBorder(subimage, *border, cv2.BORDER_CONSTANT, value=color)
            subimage = pil.fromarray(subimage)

            thumbnail.paste(subimage, (i % 2 * width, i // 2 * height))

        thumbnail.save("thumbnail.png")
        # todo fall back thumbnail remote_thumbnail = urlretrieve(clips[0]["thumbnail_url"])[0]
        exit(0)

        # to be remove to when remote download is fixed
        local_file = "clips.mp4"
        if os.path.exists(local_file):
            os.remove(local_file)

        video: CompositeVideoClip = concatenate_videoclips(subclips, method="compose", padding=-1)
        video.write_videofile(local_file, codec="libx264", audio_codec="aac", verbose=False)
        video.close()

        description = "🎥 Credits:\n" + "\n".join(credits) + "\n\n⌚ Timestamps:\n" + timestamps
        print(description)
    urlcleanup()

    # todo shuffle + pas deux fois le meme streamer à la suite ?


if __name__ == "__main__":
    launch_after_preload(main)

# youtube upload https://github.com/ClarityCoders/AutoTube/blob/master/utils/upload_video.py
