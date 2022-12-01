from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from moviepy.audio.fx.audio_normalize import audio_normalize
from moviepy.video.compositing import transitions as transfx

from compyle.preloader import launch_after_preload
from compyle.services.twitch import TwitchApi
from urllib.request import urlretrieve


def main():
    api = TwitchApi()

    game_name = "League of Legends"
    game_name = "VALORANT"
    game_id = api.get_game_id(game_name)
    clips = api.get_game_clips(game_id)

    # import random

    # random.shuffle(clips)

    video = None
    description = ""
    subclips = []
    subclips_duration = 0

    for clip in clips[:10]:
        url = api.get_clip_url(clip)
        remote_path, _ = urlretrieve(url)

        videoclip: VideoFileClip = VideoFileClip(remote_path)
        videoclip = audio_normalize(videoclip)
        videoclip = videoclip.resize((1920, 1080))
        videoclip = videoclip.set_fps(60)

        textclip: TextClip = TextClip(clip["broadcaster_name"], fontsize=60, color="white")
        textclip = textclip.set_duration(videoclip.duration)
        textclip = textclip.set_position(("left", "top"))
        textclip = textclip.fx(transfx.slide_in, duration=1, side="left")
        # TODO couleur

        composite = CompositeVideoClip([videoclip, textclip])
        subclips.append(composite)

        minutes = int(subclips_duration / 60)
        seconds = int(subclips_duration % 60)
        timestamp = f"{minutes:02d}:{seconds:02d}"
        description += f"{timestamp} {clip['broadcaster_name']}\n"
        subclips_duration += videoclip.duration

        videoclip.reader.close()

    if subclips:
        video: CompositeVideoClip = concatenate_videoclips(subclips)
        video.write_videofile("clips.mp4", codec="libx264", verbose=False)
        video.close()

    # pas deux fois le meme streamer à la suite ?


if __name__ == "__main__":
    launch_after_preload(main)
