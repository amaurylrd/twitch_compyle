from compyle.services.controllers.youtube import YoutubeAPI

youtube = YoutubeAPI()
cat = youtube.get_categories()
print(cat)
