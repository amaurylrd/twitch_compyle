from twitch_compyle.api import twitch
from twitch_compyle.preloader import launch_after_preload

def main():
    pass

if __name__ == "__main__":
    launch_after_preload(main)
    
    twitch.refresh_access_token()   
    x = twitch.get_top_games()
    y = twitch.get_games_clips(x[0][0])
    
    print(y)
