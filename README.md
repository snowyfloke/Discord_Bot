# Public Open-Source Discord Bot!

## How to Set Up?
Create a new bot on Discord Developer Portal, after that, copy it's token to a .env
```
DISCORD_TOKEN = <your-token>
DISCORD_ALT_TOKEN = <your-alt-token>
```
###### The alt token is used by main-alt.py, it's intended as a way to test your bot, or run multiple bots! By default, the .env file is ignored by git. Please check if that's the case for you, otherwise you will expose your tokens, and can get hacked!

Create a python venv, and using pip, install all the packages inside requirements.txt

### Cookies
YouTube nowadays requires cookies to download videos. There are two ways to do this:
If your default browser is NOT Google Chrome, you can log into a burner Google Account on Chrome, and the bot will grab that automatically for you!
If your default browser IS Google Chrome, download an extension that allows you to download cookies, and donwload them into a file named "cookie.txt" inside the main bot folder. Replace the music.py file by the vps/music.py, and change the location of the cookies.
```
'cookiefile': '/home/yasmin/Discord_Bot/cookie.txt' # change this line
```
After all that, you can run the bot by running (inside the venv) the main.py/main-alt.py file!
Add the bot to a server, and test the commands!

### Extractor
Sometimes, cookies aren't enough. I've included a docker-compose file so you can run a extractor container, beware that this is for more advanced users, and even I don't fully understand how it works. If you need to follow this line, you're on your own, good luck!
