# pylint: disable=invalid-name

import logging
import os
from math import ceil
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, TypeAlias, Union
from urllib.request import urlcleanup

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

from compyle.databases.mongo import MongoDB
from compyle.services.common import get_url_content
from compyle.settings import DEBUG
from compyle.utils.decorators import call_before_after

LOGGER = logging.getLogger(__name__)
logging.getLogger("PIL.PngImagePlugin").setLevel(logging.ERROR)
logging.getLogger("PIL.Image").setLevel(logging.ERROR)
logging.getLogger("imageio_ffmpeg").setLevel(logging.ERROR)

vec3: TypeAlias = Tuple[int, int, int]
vec4: TypeAlias = Tuple[int, int, int, int]


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


cascade: str = "./opencv/haarcascades/frontalface.xml"
classifier: cv2.CascadeClassifier = cv2.CascadeClassifier(cascade)


def get_faces(image: cv2.Mat, *, scale: float = 0.5) -> List[vec4]:
    """Returns the faces detected in the specified image using the Haar cascade classifier.

    Args:
        image (cv2.Mat): the image to process.
        scale (float, optional): the scale factor to apply. Defaults to 0.5 (half the size of the image).

    Returns:
        List[Tuple[int, int, int, int]]: the faces detected in the specified image.
    """
    # reduces the image size by 2 to improve the detection
    image: cv2.Mat = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

    # converts the image to grayscale and equalizes its histogram
    grayscale: cv2.Mat = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    grayscale: cv2.Mat = cv2.equalizeHist(grayscale)

    # TODO timer pour le temps de détection
    # TODO mettre une minsize en forme de visage et plus grande que 30
    faces = classifier.detectMultiScale(
        grayscale,
        scaleFactor=1.3,
        minNeighbors=6,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE,
    )

    return [[int(coord / scale) for coord in face] for face in faces]


def find_crop(image: cv2.Mat, face: vec4, *, scale: float = 1, ratio: float = 16 / 9) -> vec4:
    """Finds the crop coordinates for the specified image and face.

    Args:
        image (cv2.Mat): the image to process.
        face (vec4): the face coordinates.
        scale (float, optional): the scale factor to apply. Defaults to 1.
        ratio (float, optional): the ratio to satisfy. Defaults to 16/9.

    Returns:
        vec4: the crop coordinates.
    """
    x, y, w, h = face  # pylint: disable=invalid-name
    center: Tuple[int, int] = x + w // 2, y + h // 2

    if w > h * ratio:
        neww = int(w * scale)
        newh = int(neww / ratio)
        newx = center[0] - neww // 2
        newy = center[1] - newh // 2
    else:
        newh = int(h * scale)
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


def sharpen_image(image: cv2.Mat) -> cv2.Mat:
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(image, -1, kernel)


def get_thumbnail(
    subimages: Dict[str, Tuple[vec4, cv2.Mat]],
    default: Dict[str, str],
    border_color: Tuple[int, int, int] = (114, 181, 209),
    border_size: int = 30,
    scale: float = 1.5,
):
    if not subimages:
        return cv2.imread(get_url_content(default["thumbnail_url"]))
        # TODO resize 480x272 to 1920x1080

    # TODO get_gradiant

    # fills the thumbnail with black pixels in column-major order
    # thumbnail = np.full((1080, 1920, len(border_color)), border_color, np.uint8)
    thumbnail = np.zeros((1080, 1920, 3), np.uint8)

    def paint_gradient(thumbnail: cv2.Mat, primary: vec3, secondary: vec3, tertiary: vec3 = None):
        y = np.linspace(0, 1, thumbnail.shape[0])
        x = np.linspace(0, 1, thumbnail.shape[1])
        xv, yv = np.meshgrid(x, y)

        zz = np.sqrt(xv**2 + yv**2)

        # if (zz > 1).any():
        #     zz = zz / zz.max()

        # thumbnail[:, :, 0] = (zz * 255).astype(np.uint8)
        # 2
        d = np.minimum(0.01, np.minimum(np.minimum(xv, yv), np.minimum(1 - xv, 1 - yv)))
        d = d / d.max()

        thumbnail[:, :] = primary * d[:, :, None] + secondary * (1 - d[:, :, None])
        # thumbnail[:, :, 0] = (np.sin(xv * 2 * np.pi) * 127 + 128).astype(np.uint8)
        # thumbnail[:, :, 1] = (np.sin(yv * 2 * np.pi) * 127 + 128).astype(np.uint8)
        # thumbnail[:, :, 2] = (np.sin((xv + yv) * 2 * np.pi) * 127 + 128).astype(np.uint8)

        return None

    paint_gradient(thumbnail, border_color, (7, 46, 74))

    if len(subimages) == 4:
        # gets the quarter of the size of the thumbnail
        height, width = tuple(size // 2 for size in thumbnail.shape[:2])

        # resizes and crops the subimages onto the thumbnail in cross shape
        for i, (face, subimage) in enumerate(subimages.values()):
            # finds the largest crop around the face respecting the specified ratio
            dsize = (width - int(border_size * 1.5), height - int(border_size * 1.5))
            x, y, w, h = find_crop(subimage, face, scale=scale, ratio=dsize[0] / dsize[1])

            # crops the subimage to fit the crop
            subimage = subimage[y : y + h, x : x + w]

            # resizes the subimage the thumbnail quarter less the borders size
            subimage = cv2.resize(subimage, dsize)

            # TODO Suppr subimage = cv2.copyMakeBorder(subimage, *([border_size] * 4), cv2.BORDER_CONSTANT, value=border_color)

            # retrieves the coordinates of the subimage in the thumbnail
            x, y = (width - border_size // 2) * (i % 2) + border_size, (height - border_size // 2) * (
                i // 2
            ) + border_size

            # adds the subimage to the thumbnail
            thumbnail[y : y + subimage.shape[0], x : x + subimage.shape[1]] = subimage  # (subimage)
    else:
        height, width = thumbnail.shape[0], thumbnail.shape[1] // len(subimages)

        # resizes and crops vertically the subimages onto the thumbnail
        for i, (face, subimage) in enumerate(subimages.values()):
            # crops the largest subimage around the face respecting the specified ratio
            x, y, w, h = find_crop(subimage, face, scale=scale, ratio=16 / 9 / len(subimages))
            subimage = subimage[y : y + h, x : x + w]
            subimage = cv2.resize(
                subimage, (width - int(border_size + border_size / len(subimages)), height - border_size * 2)
            )
            subimage = cv2.copyMakeBorder(subimage, *([border_size] * 4), cv2.BORDER_CONSTANT, value=border_color)

            x = (width - int(border_size / len(subimages))) * i
            if i == len(subimages) - 1:
                x = thumbnail.shape[1] - subimage.shape[1]

            print(x, subimage.shape[1])
            print(i, subimage.shape, (width - border_size * scale, height - border_size * scale))

            thumbnail[: subimage.shape[0], x : x + subimage.shape[1]] = subimage

    return thumbnail


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
    from math import exp

    textclip = textclip.set_duration(min(videoclip.duration, 6)).set_start(1.42)

    def slide_in_and_out(t):
        if t < 1:
            return (-exp(-t * 5) * 500, 0)
        if t > 4:
            return (-exp((t - 5) * 5) * 500, 0)
        return (0, 0)

    # TODO
    # faire un jeu mobile: escalier parfait avec un barre de chargement (cf, touche du bas qd ca charge avec edit)
    # True du cul
    # False
    textclip = textclip.set_position(slide_in_and_out)
    # textclip = textclip.fx(slide_in, 1, "left")
    # textclip = textclip.fx(crossfadeout, 1)

    textclip = textclip.margin(top=50, bottom=videoclip.h - textclip.h - 50, right=videoclip.w - textclip.w, opacity=0)

    # merges subclip and textclip into a composite clip
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
    return data[i][key] != data[j][key]


def dfs(data: Iterable[Union[Any, Dict[str, Any]]], key: Optional[str] = None, i: int = 0) -> bool:
    """Shuffles the specified data to avoid having the same broadcaster twice in a row.

    Args:
        data (Iterable[Union[Any, Dict[str, Any]]]): either a list of elements or a list of dictionaries.
        key (Optional[str], optional): the key to use for the dictionaries comparison. Defaults to None.
        i (int, optional): the start index (0 or 1 expected). Defaults to 0.

    Returns:
        bool: True if the data has been shuffled or is already, False otherwise which means this is an impossible sort.
    """
    if len(data) < 3 or i == len(data):
        return True

    if i == 0 or ne(data, key, i, i):
        if dfs(data, key, i + 1):
            return True

    for j in range(i + 1, len(data)):
        if i == 0 or ne(data, key, i - 1, j):
            data[i], data[j] = data[j], data[i]

            if dfs(data, key, i + 1):
                return True

            data[i], data[j] = data[j], data[i]

    return False


def rearrange(clips: List[Dict[str, str]], key: str, max_length: int = 15) -> List[Dict[str, str]]:
    # TODO docstring
    # rule never 2 clips from the same broadcaster in a row
    # shuffles the clips to avoid having the same broadcaster twice in a row

    if len(clips) < max_length and dfs(clips, key, 1):
        return clips

    # TODO faire une fonction de fall_back
    # for i in range(len(clips) - 1):
    #     broadcaster_name = clips[i][key]

    #     if broadcaster_name == clips[i + 1][key]:
    #         for j in range(1, len(clips)):
    #             if (
    #                 j != i
    #                 and j != i + 1
    #                 and broadcaster_name not in (clips[k][key] for k in range(j - 1, min(j + 2, len(clips))))
    #                 and (i + 2 >= len(clips) or clips[j][key] != clips[i + 2][key])
    #             ):
    #                 clips[i + 1], clips[j] = clips[j], clips[i + 1]
    #                 break

    return clips


@call_before_after(urlcleanup)
def edit(*, _input: Optional[str] = None, output: Optional[str] = None):
    if _input is None:
        # loads data from the database
        with MongoDB() as mongo_db:
            # todo filter ceux non utilisé pour des clips
            # limit=20, sum(duration) == 10

            # clips = mongo_db.get_documents("clips", limit=20)

            query = {}
            sort = {"view_count": -1, "created_at": -1}
            project = {"data": {"$arrayElemAt": ["$data", 0]}}
            group = {"data": {"$push": "$$ROOT"}, "_id": "$id"}
            replaceRoot = {"$replaceRoot": {"newRoot": "$data"}}
            pipeline = mongo_db.build_pipeline(query, replaceRoot, sort=sort, project=project, group=group)
            clips = mongo_db.get_documents("clips", pipeline)

            # clips_id = [
            #     ObjectId("650c8e0251beaf12754f1a90"),
            #     ObjectId("650c8e0251beaf12754f1a92"),
            #     ObjectId("650c8e0251beaf12754f1a93"),
            #     ObjectId("650c8e0251beaf12754f1a97"),
            # ]
            # pipeline = mongo_db.build_pipeline(match={"_id": {"$in": clips_id}})
            # clips = mongo_db.get_documents("clips", pipeline)

            # top 20
            # most viewed
            # most recent

    else:
        # stores the clips data in the filesystem
        # if output.endswith("/") or os.path.isdir(output):
        #     output = get_latest_file(output)

        # soit c'est un fichier soit un dossier
        clips = []
        pass

    subclips = []
    subclips_duration = 0
    timestamps = ""
    _credits: Set[str] = set()
    subimages: Dict[str, cv2.Mat] = {}

    # test1 = [1, 2, 3, 3, 5, 5, 7, 8, 9, 9]
    # test = [1, 1, 1, 1, 1, 6, 6, 6, 6, 6, 6]  # expected false
    # test2 = [6, 6, 6, 6, 1, 1, 1, 1, 1, 6, 6]
    # test3 = [1, 1, 1, 3, 5, 5, 9, 9, 9, 9]
    # test4 = [1, 2, 3, 4, 4]
    # test5 = [1, 2, 3, 4, 4, 4]

    # tests = [test1, test, test2, test3, test4, test5]
    # for t in tests:
    #     inp = [{"broadcaster_name": f"toto{i}"} for i in t]
    #     t2 = rearrange(inp, "broadcaster_name")
    #     print(is_valid(t2), t, [clip["broadcaster_name"][-1] for clip in t2])

    rearrange(clips, key="broadcaster_name")

    for clip in clips:
        # retrieves clip url and downloads clip file
        temporary_file: str = get_url_content(clip["clip_url"])
        broadcaster_name: str = clip["broadcaster_name"]
        LOGGER.debug("edit clip %s from %s", clip["_id"], broadcaster_name)

        # TODO timer pour le file download
        composite = compose_clip(temporary_file, broadcaster_name, duration=clip["duration"], width=1920, height=1080)

        # adds crossfadein transition between subclips
        if subclips:
            composite = composite.fx(crossfadein, 1)

        # appends composite clip to subclips
        subclips.append(composite)

        # updating timestamps and description
        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        timestamps += f"{timestamp} {broadcaster_name}\n"
        subclips_duration += composite.duration
        credit = f"{broadcaster_name} - {clip['broadcaster_url']}"
        _credits.add(credit)

        # checks if the broadcaster has already been added to the subimages
        if len(subimages) < 4 and broadcaster_name not in subimages:
            # if no face has been detected, tries to find one in every 10% of the clip
            faces = []
            i = 0
            step = int(ceil(composite.duration / 10))
            while len(faces) < 1 and i < composite.duration:
                image = composite.get_frame(i)
                faces = get_faces(image)
                i += step

            # checks if a face has been detected
            if len(faces) > 0:
                subimages[broadcaster_name] = (faces[0], cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
                LOGGER.debug("face found in the %dth frame of the clip", i)
            else:
                LOGGER.debug("no face found in the clip")
        else:
            LOGGER.debug("face detection skipped to avoid repeating the same broadcaster face")

    if subclips:
        print(subimages.keys())
        # prompt video title
        title = clips[0]["title"]
        # from transformers import AutoModelForSequenceClassification

        # # Charger le modèle BERT
        # model = AutoModelForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=8)

        # # Définir les sentences à classer
        # prompt = f"If needed rephrase this title of twitch clip {title} to be a good video title on youtube in french showcasing or emphasing the epicness of the performance"

        # # Encoder les sentences
        # encoded_data = model.encode([prompt], return_tensors="pt")

        # # Effectuer la prédiction
        # predicted_labels = model(encoded_data["input_ids"])

        # # Décoder les labels prédits
        # decoded_labels = model.decode(predicted_labels)

        # https://www.kdnuggets.com/2023/05/huggingchat-python-api-alternative.html
        title = title.upper()

        # print(decoded_labels)

        thumbnail = get_thumbnail(subimages, clips[0])
        # TODO prompt thumbnail text

        font = cv2.FONT_HERSHEY_DUPLEX
        scale = 5
        color = (255, 255, 255)
        thickness = 20

        # gets the boundary of this text
        (text_width, text_height), baseline = cv2.getTextSize(title, font, scale, thickness)
        bottomLeftCornerOfText = ((1920 - text_width) // 2, (1080 + text_height) // 2)

        # bottomLeftCornerOfText = ((1920 - text_width) // 2, 1080 // 2 + baseline)
        # thickness // 2

        merge = 0
        thumbnail[
            (1080 - text_height) // 2 - merge : (1080 + text_height) // 2 + merge,
            (1920 - text_width) // 2 - merge : (1920 + text_width) // 2 + merge,
        ] = (0, 0, 0)
        cv2.putText(thumbnail, title, bottomLeftCornerOfText, font, scale, color, thickness)
        thumbnail[bottomLeftCornerOfText[1] - baseline, :] = (0, 0, 255)

        filename = r"thumbnail.png"
        if os.path.exists(filename):
            os.remove(filename)
        cv2.imwrite(filename, thumbnail)

        description = "🎥 Credits:\n" + "\n".join(list(_credits)[::-1]) + "\n\n⌚ Timestamps:\n" + timestamps
        local_file = r"clips.mp4"

        write_video(subclips, local_file)

    print("edit", _input, output)
    # TODO laoder


def write_video(subclips: List[CompositeVideoClip], filename: str = r"clips.mp4"):
    # if the file already exists, deletes it
    if os.path.exists(filename):
        os.remove(filename)

    # returns the total number of CPU or None if undetermined
    threads: Optional[int] = os.cpu_count()

    # sets the FPS and codec preset according to the debug mode
    fps, preset = (15, "ultrafast") if DEBUG else (None, "placebo")

    # merges the subclips into a single videofile
    video: CompositeVideoClip = concatenate_videoclips(subclips, method="compose", padding=-1)
    video.write_videofile(filename, codec="libx264", audio_codec="aac", fps=fps, preset=preset, threads=threads)
    video.close()
