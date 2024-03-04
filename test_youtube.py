from compyle.services.youtube import YoutubeAPI

youtube = YoutubeAPI()
# cat = youtube.get_categories()
# print(cat)

filename = "Rallye des Vallées 2023.mp4"
youtube.test(filename, "TEST TITLE", "TEST DESCRIPTION", "22", ["test_tags"])
