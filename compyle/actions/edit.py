# pylint: disable=invalid-name

import logging
import os
import random
from http.client import HTTPMessage
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    MutableMapping,
    Optional,
    Set,
    Tuple,
    TypeAlias,
    Union,
)
from urllib.request import Request, urlcleanup, urlopen, urlretrieve

import cv2
import numpy as np
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.editor import (
    CompositeVideoClip,
    TextClip,
    VideoFileClip,
    concatenate_videoclips,
)
from moviepy.video.compositing.transitions import crossfadein, crossfadeout, slide_in
from moviepy.video.fx.resize import resize

from compyle.services.databases.mongo import MongoDB
from compyle.utils.decorators import call_before_after

LOGGER = logging.getLogger(__name__)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)
logging.getLogger("PIL.Image").setLevel(logging.ERROR)
logging.getLogger("imageio_ffmpeg").setLevel(logging.ERROR)

vec4: TypeAlias = List[Tuple[int, int, int, int]]


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


# pylint: disable=line-too-long
def url_retrieve(
    url: str, data: Optional[Iterable[bytes]] = None, headers: MutableMapping[str, str] = None, size: int = -1
) -> tuple[str, HTTPMessage]:
    """Retrieves the specified url and returns the content.

    Args:
        url (str): the url to be retrieved.
        data (Iterable[bytes], optional): the data to be sent. Defaults to None.
        headers (MutableMapping[str, str], optional): the headers to be sent. Defaults to None.
        size (int, optional): the number of characters to read from the url. Defaults to -1. If negative or omitted, read until EOF.

    Returns:
        bytes: the content of the page.
    """
    return urlretrieve(url)  # nosec
    # with urlopen(Request(url, data=data, headers=headers)) as response:  # nosec
    #     return response.read(size)


def get_faces(image: cv2.Mat) -> List[vec4]:
    """Returns the faces detected in the specified image.

    Args:
        image (cv2.Mat): the image to process.

    Returns:
        List[Tuple[int, int, int, int]]: the faces detected in the specified image.
    """
    image: cv2.Mat = cv2.resize(image, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)

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


def find_crop(image: cv2.Mat, face: vec4, factor: float = 1.5, ratio: float = 16 / 9) -> vec4:
    """Finds the crop coordinates for the specified image and face.

    Args:
        image (cv2.Mat): the image to process.
        face (vec4): the face coordinates.
        factor (float, optional): the scale factor to apply. Defaults to 1.5.
        ratio (float, optional): the ratio to satisfy. Defaults to 16/9.

    Returns:
        vec4: the crop coordinates.
    """
    x, y, w, h = face  # pylint: disable=invalid-name
    center: Tuple[int, int] = x + w // 2, y + h // 2

    if w > h * ratio:
        neww = int(w * factor)
        newh = int(neww / ratio)
        newx = center[0] - neww // 2
        newy = center[1] - newh // 2
    else:
        newh = int(h * factor)
        neww = int(newh * ratio)
        newy = center[1] - newh // 2
        newx = center[0] - neww // 2

    if neww >= image.shape[1]:
        neww = image.shape[1]
        newh = int(neww / ratio)
        newy = center[1] - newh // 2
        newx = 0
    elif newh >= image.shape[0]:
        newh = image.shape[0]
        neww = int(newh * ratio)
        newx = center[0] - neww // 2
        newy = 0

    if newx < 0:
        newx = 0
    elif newx + neww > image.shape[1]:
        newx = image.shape[1] - neww

    if newy < 0:
        newy = 0
    elif newy + newh > image.shape[0]:
        newy = image.shape[0] - newh

    return newx, newy, neww, newh


def compose_clip(file: str, broadcaster_name: str, **kwargs) -> CompositeVideoClip:
    """Composes a clip from the specified temporary file. Adds a textclip with the specified broadcaster name.

    Args:
        file (str): the path to the temporary file.
        broadcaster_name (str): the name of the broadcaster.
        kwargs (Dict[str, Any]): the optional arguments like the duration of the subclip, its new width and height.

    Returns:
        CompositeVideoClip: the composed clip.
    """
    # videoclip creation and normalization
    videoclip: VideoFileClip = VideoFileClip(file)
    videoclip = videoclip.subclip(0, kwargs.get("duration", videoclip.duration))
    resize(videoclip, width=kwargs.get("width", 1920), height=kwargs.get("height", 1080))
    videoclip = videoclip.fx(audio_normalize)

    # textclip creation and normalisation
    textclip = TextClip(
        txt=("  " + broadcaster_name).ljust(20),
        method="label",
        fontsize=60,
        color="white",
        bg_color="rgb(145, 70, 255)",  # TODO mettre custom twitch bg-color
        # stroke_color="black",
        # stroke_width=1,
    )
    textclip = textclip.set_duration(min(videoclip.duration, 5))
    textclip = textclip.fx(slide_in, 1, "left")
    textclip = textclip.fx(crossfadeout, 1)
    textclip = textclip.margin(top=50, bottom=videoclip.h - textclip.h - 50, right=videoclip.w - textclip.w, opacity=0)

    # merge subclip and textclip into a composite clip
    composite: CompositeVideoClip = CompositeVideoClip([videoclip, textclip]).set_duration(videoclip.duration)

    # releases the video, audio and text resources
    videoclip.close()
    textclip.close()

    return composite


def ne(data: Iterable[Union[Any, Dict[str, Any]]], key: Optional[str], i: int, j: int) -> bool:
    """Tests if the specified list elements are different.

    Args:
        data (Iterable[Union[Any, Dict[str, Any]]]): the data to be tested.
        key (Optional[str]): the key to use for the dictionaries comparison.
        i (int): the first index (must be in range of data).
        j (int): the second index (must be in range of data).

    Returns:
        bool: True if the specified data elements are different, False otherwise.
    """
    return data[i][key] != data[j][key] if key in data else data[i] != data[j]


def dfs(data: Iterable[Union[Any, Dict[str, Any]]], key: Optional[str] = None, i: int = 0) -> bool:
    """Shuffles the specified data to avoid having the same broadcaster twice in a row.

    Args:
        data (Iterable[Union[Any, Dict[str, Any]]]): either a list of elements or a list of dictionaries.
        key (Optional[str], optional): the key to use for the dictionaries comparison. Defaults to None.
        i (int, optional): the start index (0 or 1 expected). Defaults to 0.

    Returns:
        bool: True if the data has been shuffled or is already, False otherwise which means this is an impossible sort.
    """
    if len(data) < 3:
        return True

    if i >= len(data):
        return False

    if i == 0 or ne(data, key, i - 1, i):
        if i + 1 == len(data) or dfs(data, key, i + 1):
            return True

    for j in range(i + 1, len(data)):
        if i == 0 or ne(data, key, i - 1, j):
            data[i], data[j] = data[j], data[i]

            if i + 1 == len(data) or dfs(data, key, i + 1):
                return True

            data[i], data[j] = data[j], data[i]

    return False


@call_before_after(urlcleanup)
def edit(*, _input: Optional[str] = None, output: Optional[str] = None):
    if _input is None:
        # loads data from the database
        with MongoDB() as mongo_db:
            clips = mongo_db.get_documents("clips")  # todo filter ceux non utilisé pour des clips
    else:
        # stores the clips data in the filesystem
        # if output.endswith("/") or os.path.isdir(output):
        #     output = get_latest_file(output)

        # soit c'est un fichier soit un dossier
        clips = []
        pass

    clips = clips[-10:]
    subclips = []
    subclips_duration = 0
    timestamps = ""
    _credits: Set[str] = set()
    subimages: Dict[str, cv2.Mat] = {}

    # shuffles the clips to avoid having the same broadcaster twice in a row
    def rearrange(clips: List[Dict[str, str]], key=str) -> List[Dict[str, str]]:
        # rule never 2 clips from the same broadcaster in a row

        if dfs(clips, key, 1):
            return clips

        for i in range(len(clips) - 1):
            broadcaster_name = clips[i][key]

            if broadcaster_name == clips[i + 1][key]:
                for j in range(1, len(clips)):
                    if (
                        j != i
                        and j != i + 1
                        and broadcaster_name not in (clips[k][key] for k in range(j - 1, min(j + 2, len(clips))))
                        and (i + 2 >= len(clips) or clips[j][key] != clips[i + 2][key])
                    ):
                        clips[i + 1], clips[j] = clips[j], clips[i + 1]
                        break

        return clips

    def is_valid(clips) -> bool:
        for i in range(len(clips) - 1):
            if clips[i]["broadcaster_name"] == clips[i + 1]["broadcaster_name"]:
                return False
        return True

    test1 = [1, 2, 3, 3, 5, 5, 7, 8, 9, 9]
    test = [1, 1, 1, 1, 1, 6, 6, 6, 6, 6, 6]  # expected false
    test2 = [6, 6, 6, 6, 1, 1, 1, 1, 1, 6, 6]
    test3 = [1, 1, 1, 3, 5, 5, 9, 9, 9, 9]
    test4 = [1, 2, 3, 4, 4]
    test5 = [1, 2, 3, 4, 4, 4]

    tests = [test1, test, test2, test3, test4, test5]
    for t in tests:
        inp = [{"broadcaster_name": f"toto{i}"} for i in t]
        t2 = rearrange(inp, "broadcaster_name")
        print(is_valid(t2), t, [clip["broadcaster_name"][-1] for clip in t2])

    exit()

    clips = shuffle(clips)

    for clip in clips:
        # retrieve clip url and download clip file
        temporary_file: str = url_retrieve(clip["clip_url"])[0]
        broadcaster_name: str = clip["broadcaster_name"]

        print(broadcaster_name, clip["_id"])  # todo transformer en log

        composite = compose_clip(temporary_file, broadcaster_name, duration=clip["duration"], width=1920, height=1080)

        # add crossfadein transition between subclips
        if subclips:
            composite = composite.fx(crossfadein, 1)

        # append composite clip to subclips
        subclips.append(composite)

        # updating timestamps and description
        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        timestamps += f"{timestamp} {broadcaster_name}\n"
        subclips_duration += composite.duration
        credit = f"{broadcaster_name} - https://www.twitch.tv/{broadcaster_name}"
        _credits.add(credit)

        if len(subimages) < 4 and broadcaster_name not in subimages:
            image = cv2.imread(url_retrieve(clip["thumbnail_url"])[0])
            faces = get_faces(image)

            i = 0
            step = composite.duration // 10
            while len(faces) < 1 and i < composite.duration:
                image = composite.get_frame(i)
                faces = get_faces(image)
                i += step

            if len(faces) > 0:
                subimages[broadcaster_name] = (
                    [coord * 2 for coord in faces[0]],
                    cv2.cvtColor(image, cv2.COLOR_BGR2RGB),
                )

    if subclips:
        fst, rst = subclips[0], subclips[1:]

        title = clips[0]["title"]

        if not subimages:
            thumbnail = cv2.imread(url_retrieve(clips[0]["thumbnail_url"])[0])
        elif len(subimages) == 4:
            thumbnail = np.zeros((1080, 1920, 3), np.uint8)
            height, width = tuple(size // 2 for size in thumbnail.shape[:2])

            for i, (face, subimage) in enumerate(subimages.values()):
                x, y, w, h = find_crop(image, face)
                subimage = subimage[y : y + h, x : x + w]

                border = 20
                subimage = cv2.resize(subimage, (width - int(border * 1.5), height - int(border * 1.5)))
                subimage = cv2.copyMakeBorder(subimage, *([border] * 4), cv2.BORDER_CONSTANT, value=0)
                x, y = (width - border // 2) * (i % 2), (height - border // 2) * (i // 2)
                thumbnail[y : y + subimage.shape[0], x : x + subimage.shape[1]] = subimage
        else:
            thumbnail = np.zeros((1080, 1920, 3), np.uint8)
            height, width = thumbnail.shape[0], thumbnail.shape[1] // len(subimages)
            for i, (face, subimage) in enumerate(subimages.values()):
                x, y, w, h = find_crop(image, face, factor=1.5, ratio=(16 / 9) / len(subimages))
                print(x, y, w, h)
                subimage = subimage[y : y + h, x : x + w]

                border = 20
                subimage = cv2.resize(
                    subimage, (width - int(border + border / len(subimages)), height - int(border * 2))
                )
                subimage = cv2.copyMakeBorder(subimage, *([border] * 4), cv2.BORDER_CONSTANT, value=(100, 35, 200))
                x1 = (width - int(border / len(subimages))) * i
                if i == len(subimages) - 1:
                    x1 = thumbnail.shape[1] - subimage.shape[1]
                print(x1, subimage.shape[1])
                print(i, subimage.shape, (width - border * 1.5, height - border * 1.5))
                thumbnail[: subimage.shape[0], x1 : x1 + subimage.shape[1]] = subimage

        font = cv2.FONT_HERSHEY_SIMPLEX
        # get boundary of this text
        fontScale = 5
        textsize = [i * fontScale for i in cv2.getTextSize(title, font, 1, 2)[0]]
        bottomLeftCornerOfText = ((1920 - textsize[0]) // 2, (1080 + textsize[1]) // 2)
        fontColor = (255, 255, 255)
        thickness = 20

        # cv2.putText(
        #     thumbnail,
        #     title.upper(),
        #     (int(1920 - textsize[0] * 1.1) // 2, bottomLeftCornerOfText[1]),
        #     font,
        #     fontScale * 1.05,
        #     (0, 0, 255),
        #     thickness,
        #     lineType,
        # )
        thumbnail[
            (1080 - textsize[1]) // 2 - 50 : (1080 + textsize[1]) // 2 + 50,
            (1920 - textsize[0]) // 2 - 50 : (1920 + textsize[0]) // 2 + 50,
        ] = (0, 0, 0)
        cv2.putText(thumbnail, title.upper(), bottomLeftCornerOfText, font, fontScale, fontColor, thickness)

        filename = r"thumbnail.png"
        if os.path.exists(filename):
            os.remove(filename)
        cv2.imwrite(filename, thumbnail)

        description = "🎥 Credits:\n" + "\n".join(list(_credits)[::-1]) + "\n\n⌚ Timestamps:\n" + timestamps
        local_file = r"clips.mp4"

        print(local_file)
        print(description)
        if os.path.exists(local_file):
            os.remove(local_file)

        # codec="h264_nvenc",

        video: CompositeVideoClip = concatenate_videoclips(my_array, method="compose", padding=-1)
        video.write_videofile(local_file, audio_codec="aac", verbose=False, fps=15, preset="placebo")
        video.close()

    print("edit", _input, output)
    # TODO laoder

    # for clip in clips[2:4]:
    #     # 1. retrieve clip url and download clip file
    #     url = api.get_clip_url(clip)
    #     temporary_file = url_retrieve(url)[0]

    #     # 2. videoclip creation and normalization
    #     videoclip: VideoFileClip = VideoFileClip(temporary_file)
    #     videoclip = videoclip.subclip(0, clip["duration"])
    #     videoclip = videoclip.set_fps(60)
    #     videoclip = videoclip.fx(resize, width=1920, height=1080)
    #     videoclip = audio_normalize(videoclip)
