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
from moviepy.video.compositing.transitions import slide_in, crossfadein
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.resize import resize
import datetime

from compyle.utils.descriptors import serialize
from compyle.preloader import launch_after_preload
from compyle.services.twitch import TwitchApi
from compyle.utils.decorators import call_before_after


@call_before_after(urlcleanup)
def collect(*, reports_folder: str = "reports", game_name: str = "League of Legends", period: int = 2):
    twitch_api = TwitchApi()

    game_id = twitch_api.get_game_id(game_name)
    clips = twitch_api.get_game_clips(game_id, period=period)

    if not os.path.isdir(reports_folder):
        os.mkdir(reports_folder)

    output_file: str = (
        f'{reports_folder}/{game_name.replace(" ", "-")}_{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.json'
    )
    serialize(output_file, clips)

    return output_file


def main():
    # workflow= collect -> edit -> upload en json
    # https://docs.python.org/3/library/argparse.html
    report = collect()
    exit(0)

    # import random
    # random.shuffle(clips)

    subclips = []
    subclips_duration = 0

    subimages = {}

    timestamps = ""
    credits = set()

    # todo thumbnail des 4 meilleures
    # TODO couleur
    # todo shuffle, pas deux même streamers de suite
    # todo break si durée au dessus de 10 minutes + historique

    for clip in clips[2:4]:
        # 1. retrieve clip url and download clip file
        url = api.get_clip_url(clip)
        temporary_file = urlretrieve(url)[0]

        # 2. videoclip creation and normalization
        videoclip: VideoFileClip = VideoFileClip(temporary_file)
        videoclip = videoclip.subclip(0, clip["duration"])
        videoclip = videoclip.set_fps(60)
        videoclip = videoclip.fx(resize, width=1920, height=1080)
        videoclip = audio_normalize(videoclip)

        # 3. textclip creation
        textclip: TextClip = TextClip(
            clip["broadcaster_name"].ljust(5),
            # TODO pourquoi ça strip
            method="caption",
            align="center",
            fontsize=60,
            color="white",
            bg_color="rgb(145, 70, 255)",  # TODO mettre custom twitch bg-color
            # stroke_color="black",
            # stroke_width=1,
        )
        textclip = textclip.set_position(("left", "top"))
        textclip = textclip.set_duration(videoclip.duration)
        # todo set duration 3 ou 4 secondes avec un fadeout
        textclip = textclip.fx(slide_in, duration=1, side="left")

        def get_faces(image: cv2.Mat):
            image: cv2.Mat = cv2.resize(image, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
            # todo (0,0) ou None
            grayscale: cv2.Mat = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            grayscale: cv2.Mat = cv2.equalizeHist(grayscale)

            cascade: str = "./opencv/haarcascades/frontalface.xml"
            classifier: cv2.CascadeClassifier = cv2.CascadeClassifier(cascade)

            return classifier.detectMultiScale(
                grayscale,
                scaleFactor=1.3,
                minNeighbors=6,
                minSize=(30, 30),
                flags=cv2.CASCADE_SCALE_IMAGE,
            )

        # 4. face detection for thumbnail
        if len(subimages) < 4 and clip["broadcaster_name"] not in subimages:
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

                subimages[clip["broadcaster_name"]] = image
                cv2.imwrite(f"./opencv/image-{len(subimages)}.png", image)

        # 5. append composite clip to subclips
        composite: CompositeVideoClip = CompositeVideoClip([videoclip, textclip]).set_duration(videoclip.duration)
        composite = composite.fx(crossfadein, 1) if subclips else composite
        subclips.append(composite)
        videoclip.close()
        textclip.close()
        # todo test close composite, trouver 1 liner pour les 3

        # 6. updating timestamps and description
        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        timestamps += f"{timestamp} {clip['broadcaster_name']}\n"
        subclips_duration += composite.duration

        credit = f"{clip['broadcaster_name']} - https://www.twitch.tv/{clip['broadcaster_name']}"
        credits.add(credit)

    if subclips:
        thumbnail = pil.new("RGB", (1920, 1080))
        width, height = tuple(size // 2 for size in thumbnail.size)

        for i, (_, subimage) in enumerate(subimages.items()):
            border = [30] * 4

            subimage = cv2.resize(subimage, (width, height))
            subimage = cv2.copyMakeBorder(subimage, *border, cv2.BORDER_CONSTANT, value=(145, 70, 255))
            subimage = pil.fromarray(subimage)

            thumbnail.paste(subimage, (i % 2 * width, i // 2 * height))

        thumbnail.save("thumbnail.png")
        # todo fall back thumbnail remote_thumbnail = urlretrieve(clips[0]["thumbnail_url"])[0]
        # exit(0)

        # to be remove to when remote download is fixed
        local_file = "clips.mp4"
        if os.path.exists(local_file):
            os.remove(local_file)

        video: CompositeVideoClip = concatenate_videoclips(subclips, method="compose", padding=-1)
        # si debug ultrafast, si prod slow preset="ultrafast",
        video.write_videofile(local_file, codec="h264_nvenc", audio_codec="aac", verbose=False)
        video.close()
        # adjust thread and codec for gpu acceleration

        print(video.duration)
        print(subclips_duration)

        description = "🎥 Credits:\n" + "\n".join(credits) + "\n\n⌚ Timestamps:\n" + timestamps
        print(description)

    # todo shuffle + pas deux fois le meme streamer à la suite ?


if __name__ == "__main__":
    launch_after_preload(main)

# youtube upload https://github.com/ClarityCoders/AutoTube/blob/master/utils/upload_video.py
