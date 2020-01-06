# Play-Spotify-Songs-from-Spotlight-Search

### With this python script, you can play Spotify songs directly from Spotlight search:heavy_exclamation_mark:

<a href="https://ibb.co/tBQWfCt"><img src="https://i.ibb.co/b1Q8hdZ/Spotlight-Bright5.gif" alt="Spotlight-Bright5" border="100"></a>

**This script will retrieve all the songs in ALL of your Spotify playlists. For each song, it will make an application named after the song which you can click to play the song in Spotify.**

#

This script requires the Spotify desktop applicaiton. If you'd like to play songs in the webplayer instead, then let me know.

The song will be played in the context of the album that it belongs too. If, instead, you want the song to play in the context of a playlist or the artist it belongs to, let me know and I'll show you how to change the code. 

The songs will be sorted into folders based on the artist and album they belong to. Album cover art will be downloaded and set as the icon for the corresponding songs and for the album folders. An image for the artist will also be downloaded and set for each artist folder.

To use this script, you must have the spotipy (yes, that's with a "p", not an "f") library installed, which can be found [here](https://github.com/plamere/spotipy).
Also, download the request module from [here](https://github.com/andrewp-as-is/request.py). This module is used to download artist and album images from Spotify. You must also download fileicon, a command-line utility which sets a custom icon for files and directories. It can be found [here](https://github.com/mklement0/fileicon).

Then, visit

https://developer.spotify.com/dashboard/

and login with your Spotify account. Next, click `create client id`.  

<a href="https://ibb.co/0DJBt4G"><img src="https://i.ibb.co/4mNsdvV/Screen-Shot-2020-01-02-at-13-24-19.png" alt="Screen-Shot-2020-01-02-at-13-24-19" border="0"></a>

Enter any name or description and below `What are you building`, select `I don't know`. You will be provided with a Client ID and a Client Secret. Click on edit settings, 

<a href="https://ibb.co/MZ250x4"><img src="https://i.ibb.co/Xj2kRrg/Screen-Shot-2020-01-02-at-13-29-19.png" alt="Screen-Shot-2020-01-02-at-13-29-19" border="0"></a>

and set 
```
http://localhost/
```
as the Redirect URI. Make sure to save your changes at the bottom.

<a href="https://ibb.co/zFmhVjh"><img src="https://i.ibb.co/KD5jxRj/Screen-Shot-2020-01-02-at-13-28-20.png" alt="Screen-Shot-2020-01-02-at-13-28-20" border="0"></a>

Enter your client id, client secret, and Spotify username into the appropriate locations at the beginning of the script.


On line 15, specify the folder in which the songs will be downloaded to.
**DO NOT ADD A FORWARD SLASH TO THE END OF THE FOLDER PATH**
```
folder_location     = '/Users/myusername/Songs'
```


Now you're ready to try out the script! You must run it from terminal the first time.  When you run it the first time, you will get a message like this:
```

            User authentication requires interaction with your
            web browser. Once you enter your credentials and
            give authorization, you will be redirected to
            a url.  Paste that url you were directed to to
            complete the authorization.

        
Opened https://accounts.spotify.com/authorize?client_id=ce3e747efc764258963ec7a4bb6f80fc&response_type=code&redirect_uri=http%3A%2F%2Flocalhost%2F&scope=user-library-read in your browser


Enter the URL you were redirected to: 
```
Paste the URL that was opened in your browser into your terminal and press enter. After that, the script should run. 

This script accepts one command line argument: `noicon`, which will disable the setting of custom icons. If you don't care about the icons, then use this because the script will run several orders of magnitude faster.


And that's it! If you can't get something to work, or have any questions, feel free to create an issue.
