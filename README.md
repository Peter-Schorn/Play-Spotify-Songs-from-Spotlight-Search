# macOS-Play-Spotify-Songs-from-Spotlight-Search

**With this script, you can search for a song from your playlist in spotlight search and then press enter to play the song!**

This python script will retrieve all the songs in one of your spotify playlists. For each song, it will make an application named after the song which you can click to play the song in spotify. 
<a href="https://ibb.co/tBQWfCt"><img src="https://i.ibb.co/b1Q8hdZ/Spotlight-Bright5.gif" alt="Spotlight-Bright5" border="0"></a>

This script requires the spotify desktop applicaiton. If you'd like to play songs in the webplayer instead, then let me know.

The song will be played in the context of the album that it belongs too. If, instead, you want the song to play in the context of a playlist or the artist it belongs to, let me know and I'll show you how to change the code. 

The songs will be sorted into folders based on the artist and album they belong to. Album cover art will be downloaded and set as the icon for the corresponding songs and for the album folders. An image for the artist will also be downloaded and set for each artist folder.

To use this script, you must have the spotipy (yes, that's with a "p", not an "f") library installed, which can be found [here](https://github.com/plamere/spotipy).
Also, download the request module from [here](https://github.com/andrewp-as-is/request.py). This module is used to download artist and album images from spotify. You must also download fileicon, a command-line utility which sets a custom icon for files and directories. It can be found [here](https://github.com/mklement0/fileicon).

Then, visit

https://developer.spotify.com/dashboard/

and login with your spotify account. Next, click `create client id`.  Enter any name or description and below `What are you building`, select `I don't know`. You will be provided with a Client ID and a Client Secret. Click on edit settings, and set 
```
http://localhost/
```
as the Redirect URI. Make sure to save your changes at the bottom.


Next, navigate to one of your playlists on the spotify desktop client and click on the circle with the three dots inside it, then click on share > Copy Spotify URI, as shown below. This option is only available in the desktop client, not the web player or the mobile application.

![Playlist URI](https://i.ibb.co/TmK8mW0/PLAYLIST.png)

￼


The URI will look something like this:
```
spotify:playlist:2z212MPinIr8HesnJ68UoF
```
Remove `spotify:playlist:` from the beginning so that you have something like
```
2z212MPinIr8HesnJ68UoF
```

Now, open the script and paste the URI into the appropriate location in line 11 of the code, as shown below. Ensure that the URI is enclosed in quotation marks!
```
# This is where you enter the URI for the playlist you want to index
playlist            = '2z212MPinIr8HesnJ68UoF'
```

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

And that's it! If you can't get something to work, or have any questions, feel free to create an issue.
