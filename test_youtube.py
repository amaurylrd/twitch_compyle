from compyle.preloader import launch_after_preload
from compyle.services.youtube import YoutubeApi


def test():
    youtube_api = YoutubeApi()
    print(youtube_api.router.get_registered())


if __name__ == "__main__":
    launch_after_preload(test)
