from compyle.services.controllers.routing import Method
from compyle.services.controllers.youtube import YoutubeAPI

youtube = YoutubeAPI()
cat = youtube.get_categories()
print(cat)

filename = "Rallye des Vallées 2023.mp4"
youtube.upload_video(filename, "TEST TITLE", "TEST DESCRIPTION", "22", ["test_tags"])
