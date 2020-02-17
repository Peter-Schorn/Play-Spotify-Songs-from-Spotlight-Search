# Play-Spotify-Songs-from-Spotlight-Search

### With this python script, you can play Spotify songs directly from Spotlight search:heavy_exclamation_mark:

<a href="https://ibb.co/tBQWfCt"><img src="https://i.ibb.co/b1Q8hdZ/Spotlight-Bright5.gif" alt="Spotlight-Bright5" border="100"></a>

**This script will retrieve all the songs in ALL of your Spotify playlists. For each song, it will make an application named after the song, which you can click to play the song in Spotify. It will also make an application for each of your playlists.**

Song will be played in the context of the playlist they belong to.

This script requires the Spotify desktop applicaiton.

The songs will be sorted into folders based on the artist and album they belong to. Album cover art will be downloaded and set as the icon for the corresponding songs and for the album folders, and artist images will be set for each artist folder.

# Installation and Setup

This script requires the following dependencies:
```
certifi>=2019.11.28
chardet>=3.0.4
idna>=2.8
Pillow>=7.0.0
requests>=2.22.0
six>=1.14.0
spotipy>=2.8.0
urllib3>=1.25.8
```
The above text is in the [requirements.txt](https://github.com/Peter-Schorn/Play-Spotify-Songs-from-Spotlight-Search/blob/master/requirements.txt) file of this repository.

If you have pip, you can install all of these dependencies at once by downloading the `requirements.txt` file and then running
```
pip install -r file/path/to/requirements.txt
```
You can download pip [here](https://pip.pypa.io/en/stable/installing/)

**This script also requires [fileicon](https://github.com/mklement0/fileicon), a command-line utility which applies custom icons to files and directories.**

Next, visit

https://developer.spotify.com/dashboard/

and login with your Spotify account. Then, click `create a client id`.  

<a href="https://ibb.co/0DJBt4G"><img src="https://i.ibb.co/4mNsdvV/Screen-Shot-2020-01-02-at-13-24-19.png" alt="Screen-Shot-2020-01-02-at-13-24-19" border="0"></a>

Enter any name or description and below `What are you building`, select `I don't know`. You will be provided with a **Client ID** and a **Client Secret**. Click on edit settings, 

<a href="https://ibb.co/MZ250x4"><img src="https://i.ibb.co/Xj2kRrg/Screen-Shot-2020-01-02-at-13-29-19.png" alt="Screen-Shot-2020-01-02-at-13-29-19" border="0"></a>

and set 
```
http://localhost/
```
as the Redirect URI. Make sure to save your changes at the bottom.

<a href="https://ibb.co/zFmhVjh"><img src="https://i.ibb.co/KD5jxRj/Screen-Shot-2020-01-02-at-13-28-20.png" alt="Screen-Shot-2020-01-02-at-13-28-20" border="0"></a>

Save your client id and client secret into a text file with the following format
```
client id = abcabcabcabcabcabcabcabcabcabcab
client secret = abcabcabcabcabcabcabcabcabcabcab
```

**Fill in the following parameters at the beginning of the script:**
```
###############################################################
###############################################################
###############################################################

# Enter the folder where you want the files to be stored
folder_location = "/Users/your_username/Songs/"

# Enter the username you use to login to Spotify
username = "username"

# Set this to False if you don't want custom icons
custom_icon = True

# Enter the path to the text file where your
# client id and client secret are stored
credentials = "/Users/your_username/.local/spotify_credentials.txt"

# Enter the full path to the fileicon executable.
# It's recommended to put it in /usr/local/bin
# If you donwloaded it, but don't know where it is,
# run `which fileicon` in terminal.
fileicon_path = "/usr/local/bin/fileicon"

# Enter your preferred dimensions for each of the images;
# they will always be square.
# Your options are: 1024, 512, 256, and 128
# Some sizes may not be available in certain cases.
album_image_size    = 512
artist_image_size   = 512
playlist_image_size = 512

# This is where your access token is stored.
# Only change this if you need to.
cachePath = os.path.join(str(Path.home()), 'sp/.cache_{}_{}'.format(username, scope))
# cachePath = os.path.join(str(Path.home()), '.cache_{}_{}'.format(username, scope))

###############################################################
###############################################################
###############################################################
```

Now you're ready to try out the script! When you run it the first time, you will get a dialog box like this and **a webpage should have been opened in your broswer**:

<img src="https://i.ibb.co/zxXZJHc/Screen-Shot-2020-02-17-at-1-34-24.png" alt="Screen-Shot-2020-02-17-at-1-34-24" border="0">

On the webpage, you may be asked to login with your spotify account. After you do so, you will be redirected to a page that looks something like the image below. If you're not asked to login, you will be immediately redirected to something like the page below.

<a href="https://ibb.co/GFR5JTX"><img src="https://i.ibb.co/KmWrGwY/Screen-Shot-2020-01-06-at-10-56-36.png" alt="Screen-Shot-2020-01-06-at-10-56-36" border="0"></a>

Paste the URL of this page into the dialog box and press enter. After that, the script should run. 

# How to Use

This script accepts one command line argument: `noicon`, which will disable the setting of custom icons. If you don't care about the icons, then use this because the script will run several orders of magnitude faster. If you run the script once using the `noicon` argument, you can then run it again without the `noicon` argument and all the icons will be applied to your songs! This included pre-downloaded songs and any songs you have added to any of your playlists since running the script the first time. 

After adding new songs to an existing playlist and/or creating and/or following new playlists you can re-run the script and only the new songs will be downloaded!

Furthermore, please note that if you remove songs from any of your playlists since the last time you ran you ran the script, then the next time you run it, **these songs will be removed from your downloaded songs folder**. The same thing applies if you remove entire playlists.


And that's it! If you can't get something to work, or have any questions, feel free to create an issue.
