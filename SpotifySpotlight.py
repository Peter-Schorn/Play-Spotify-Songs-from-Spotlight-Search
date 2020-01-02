import os, shutil, re, subprocess, requests, spotipy, spotipy.util as util, time
#################################################################

# Setting the album and artist image for the files and folders
# slows down the entire script by several orders of magnitude.
# if you don't care about this, you can set `custom_icon` to False.
# TODO: if you do this, then MAKE SURE THAT `FALSE` IS CAPATILIZED!!!
custom_icon         =  True

# This is where you enter the URI for the playlist you want to index
playlist            = '2z212MPinIr8HesnJ68UoF'

# This is where you specify the folder in which the songs will be stored
# TODO: **DO NOT** add a forward slash at the very end of the folder path
folder_location     = '/Users/myusername/Songs'

# This is where you enter the username you use to log in to spotify
username            = 'myusername'

client_id           = 'enter client id here'
client_secret       = 'enter client secret here'
redirect_uri        = 'http://localhost/'
scope               = 'user-library-read'

# print('client id: ' + str(client_id))
# print('client secret: ' + str(client_secret))
################################################################
################################################################
TimeStamp               = (int(time.time()))
BlankNamesList          = []
SongsInPlaylist         = []
PlaylistAlbumsList      = []
PlaylistArtistsList     = []
UpdateCount             = 0


dirArtistImage  = folder_location + '/.Images/Artists/'
dirAlbumImage   = folder_location + '/.Images/Albums/'


# Hidden folders that contain all the artist and album images are created.
# This is so that each album and artist image is only downloaded once.
for f in (folder_location, folder_location + '/.Images/', dirArtistImage, dirAlbumImage):
    if not os.path.exists(f): os.mkdir(f)
################################################################

def download_tracks(tracks):
    global UpdateCount
    # for each track in the playlist...
    for i, item in enumerate(tracks['items']):
        track           = item['track']

      # A URI is a unique identifier for each song, album, artist, playlist, etc...
        SongURI         = track['uri']

      # Ignore local songs. See http://bit.ly/2ssUqi5 if you don't know what those are.
        if "spotify:local:" in SongURI or SongURI == "": continue

        ################################################################

        TheSong         = track['name']
        TheAlbum        = track['album']['name']
        TheArtist       = track['artists'][0]['name']
        ExactName       = TheSong + ' - ' + TheArtist

        AlbumURIContext = track['album']['uri']
        AlbumURI        = re.sub('^spotify:album:', '', AlbumURIContext)

        ArtistURI       = track['artists'][0]['id']

        ################################################################

      # Finder does not allow files/folders to include a colon, so all occurences of them are removed.
      # Files/folders that start with a period will be hidden, so leading periods are removed.
      # For some bizarre reason, a shell-escaped `/` becomes a colon, so `/`s are replaced with colons.
      # For example, if you cd to your desktop and then run `mkdir Some:Folder`,
      # The name of the folder will be `Some/Folder`. Don't ask me why that is.
        for temp in [('[:]+', ''), ('/', ':'), ('^\.+', '')]:
            TheAlbum    = re.sub(temp[0], temp[1], TheAlbum)
            TheArtist   = re.sub(temp[0], temp[1], TheArtist)
            TheSong     = re.sub(temp[0], temp[1], TheSong)

      # This will be the name of the song in finder.
      # You can pick and choose from `TheAlbum`, `TheArtist`, and `TheSong`
      # and create a different format for the name if you like.
      # Also make sure to update line 93 if you do this.
        myName = TheSong + ' - ' + TheArtist

        ################################################################

      # A list of all the albums and artists in the playlist
      # is maintained for future reference (see lines 266-303).
        if not AlbumURI in PlaylistAlbumsList:
            PlaylistAlbumsList.append(AlbumURI)

        if not ArtistURI in PlaylistArtistsList:
            PlaylistArtistsList.append(ArtistURI)

        ################################################################

        if TheAlbum    == "":
            TheAlbum    = "Unknown Album"
            AlbumKnown  = False
        else:
            AlbumKnown  = True

        if TheSong     == "":
            TheSong     = "Song " + str(i)
            myName      = TheSong + " - " + TheArtist
            BlankName   = True
        else:
            BlankName   = False

        if TheArtist   == "":
            TheArtist   = "Unknown Artist"
            myName      = TheSong

      # Creates a list of all the songs in the playlist.
      # This will later be compared with all of the downloaded songs (see lines 266-303).
        SongsInPlaylist.append(myName)

        ################################################################
      # Folders for the artists and albums are made if they don't already exist.
        dirArtistName   = folder_location + "/" + TheArtist
        if not os.path.exists(dirArtistName): os.mkdir(dirArtistName)

        dirAlbumName    = folder_location + "/" + TheArtist + "/" + TheAlbum
        if not os.path.exists(dirAlbumName): os.mkdir(dirAlbumName)
        ################################################################

      # This is where the song will be saved
        dirName = folder_location + "/" + TheArtist + "/" + TheAlbum + "/" + myName + ".app"
      # If the song has already been saved, then skip to the next song.
        if os.path.exists(dirName): continue

      # An application is made for the song
        os.mkdir(dirName)
        os.mkdir(dirName + "/Contents")
        with open(dirName + "/Contents/PkgInfo", "w+") as f:
          # This identifies the directory as an application
            f.write("APPL????")
        os.mkdir(dirName + "/Contents/MacOS")
        with open(dirName + "/Contents/MacOS/" + myName, "w+") as f:
          # This is the code that will be executed when the application is opened.
          # If, instead, you want the song to play in the context of the artist or a given playlist,
          # let me know, and I'll show you how to change this code.
            f.write("#!/bin/bash\n")
            f.write(
                "osascript -e \'tell application \"Spotify\" to play track \"{}\" in context \"{}\"\'"
                    .format(SongURI, AlbumURIContext))
      # The shell script is given permission to execute
        os.lchmod(dirName + "/Contents/MacOS/" + myName, 0o777)

        ################################################################

        if custom_icon == True:
            try:# to get the album image

              # Only download the album image if it has not already been downloaded
                if not os.path.exists(dirAlbumImage + AlbumURI + '.jpeg'):

                  # You can change the number in the line below to change
                  # the size of the image that is downloaded.
                  # 0 = 640x640 pixels
                  # 1 = 300x300 pixels
                  # 2 = 64x64   pixels
                    ImageURL = track['album']['images'][1]['url']

                    with open(dirAlbumImage + AlbumURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ImageURL).content)

              # This is where the third-party command line utility is invoked.
              # The icon is set for the song
                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirName,
                     dirAlbumImage + AlbumURI + '.jpeg'])

              # The icon is set for the album folder
                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirAlbumName,
                     dirAlbumImage + AlbumURI + '.jpeg'])

            except:
                pass

            try:# to get the artist image

              # Only download the artist image if it has not already been downloaded
                if not os.path.exists(dirArtistImage + ArtistURI + '.jpeg'):

                    Artist         = sp.artist(track['artists'][0]['uri'])

                    # You can change the number in the line below to change
                    # the size of the image that is downloaded.
                    # 0 = 640x640 pixels
                    # 1 = 320x320 pixels
                    # 2 = 160x160 pixels
                    ArtistImageURL = Artist['images'][1]['url']

                    with open(dirArtistImage + ArtistURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ArtistImageURL).content)
              # The third-party command line utility is again invoked to set the icon for the artist folder
                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirArtistName,
                     dirArtistImage + ArtistURI + '.jpeg'])

            except:
                pass

        ################################################################

        if BlankName == True: # then notify user that song has been saved as 'Song ' + str(i)
            if AlbumKnown == True:
                (BlankNamesList.append
                    ('\033[91m' + ExactName + " (from " + TheAlbum + ") saved as --> " + myName + '\033[0m'))
            else:
                (BlankNamesList.append
                    ('\033[91m' + ExactName + " saved as --> " + myName + '\033[0m'))

        else:
            print(myName)

      # A list of all the songs that have been downloaded is maintained
        UpdateCount += 1
      # print("###################################################################")
        ################################################################
########################################################################


token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)


if token:
    sp = spotipy.Spotify(auth=token)

  # The name of the playlist is retrieved so it can be displayed
    PlaylistName = sp.user_playlist(username, playlist, fields="name")
    print('\033[95m' + "Indexing " + PlaylistName['name'] + "...")
    print('\033[0m')

  # TODO: This is where the Spotify Web API is queried using Spotipy.
  # Spotify only returns 100 songs at a time. Therefore, multiple requests are made.
  # Also note that there is a 10,000 track limit for playlists.
    for offset in range(0, 10000, 100):
        tracks = sp.user_playlist_tracks(username, playlist, limit=100, offset=offset)
        if len(tracks['items']) == 0: break
        download_tracks(tracks)

  # The URI for the song is read straight out of the application;
  # It looks something like this: spotify:track:1SDiiE3v2z89VxC3aVRKHQ
    IndexedSongs = []
    for root, dirs, files in os.walk(folder_location):
        for dir in dirs:
            if dir.endswith('.app'):
                FileToRead   = os.path.join(root, dir) + '/Contents/MacOS/' + os.path.splitext(dir)[0]

              # This regular expression search retrieves the song URI
                SavedSongURI = (re.search('track "(.*)" in', open(FileToRead, "r").read()).group(1))

              # The full file path, name, and URI of the downloaded song (in that order)
              # are appended as a sub-list to a list containing all of the downloaded songs.
              # This list is later compared to the list of songs in the playlist (see the next section).
                IndexedSongs.append(
                    (os.path.join(root, dir), (os.path.splitext(dir)[0]), SavedSongURI))
  
  # This is where the songs in the playlist are cross-referenced with the songs that have been downloaded.
  # If a previously-downloaded song is no longer in the playlist, it will be deleted.
    ListOfRemovedSongs = []
  # for each of the indexed songs...
    for SavedSong in IndexedSongs:
      # if the downloaded song is not in the playlist, then...
        if not SavedSong[1] in SongsInPlaylist:
          # Append it's name to a list that will later be printed
            ListOfRemovedSongs.append(SavedSong[1])

          # The Spotify Web API is queried in order to
          # retrieve the album and artist URI for the song
            TrackInfo       = sp.track(SavedSong[2])

            SavedAlbumURI   = TrackInfo['album']['id']

          # This is where the Album image for the song is stored
            AlbumImagePath  = dirAlbumImage + SavedAlbumURI + '.jpeg'

            SavedArtistURI  = TrackInfo['artists'][0]['id']

          # This is where the Artist image for the song is stored
            ArtistImagePath = dirArtistImage + SavedArtistURI + '.jpeg'

          # if there are no longer any songs belonging to the album of the removed song,
          # then delete the album image.
            if not SavedAlbumURI in PlaylistAlbumsList:
                try: os.remove(AlbumImagePath)
                except: pass

          # If there are no longer any songs belonging to the artist of the removed song,
          # then delete the artist image
            if not SavedArtistURI in PlaylistArtistsList:
                try: os.remove(ArtistImagePath)
                except: pass

          # The song itself is deleted
            shutil.rmtree(SavedSong[0])

else:
    print("Can't get token for", username)

########################################################################

# A list of renamed songs is printed.
# Empty lists evaluate to true;
# non-empty lists evaluate to false.
if BlankNamesList:# if the list is not empty, then...
    GrammrRe = ' Song Was ' if len(BlankNamesList) == 1 else ' Songs Were '

    print("\n\033[91m################### " + str(len(BlankNamesList)) + GrammrRe + "Renamed ###################\033[0m\n")
    for i in BlankNamesList: print(i)

########################################################################

# If all the songs/albums for an album/artist, respectively, are removed,
# then the album/artist folder is deleted.
def rmEmptyFolder(dir):
    for item in os.listdir(dir):

      # All directories contain a hidden `.DS_Store` file.
      # see http://bit.ly/2Fdh8NR to read all about it
      # Also, When a custom icon is set for a finder item, a hidden `icon?` file is created.
      # This file is extra-special in that it it hidden, yet does not begin with a period,
      # Unlike all other hidden files!
      # This function deletes all folders that only contain `.DS_Store` and `icon?` files.
        if not (item == "Icon\r" or item.startswith('.')):
            return
    shutil.rmtree(dir)

# This calls the above function once for each folder
# that exists in the `folder_location`, as defined by the user.
for root, dirs, files in os.walk(folder_location, topdown=False):
    for dir in dirs:
        rmEmptyFolder(os.path.join(root, dir))

# Displays a list of removed songs
if ListOfRemovedSongs:# if list is not empty, then...
    GrammrRemovedSongs = ' Song Was ' if len(ListOfRemovedSongs) == 1 else ' Songs Were '
    print(
        "\n\033[91m################### " + str(len(ListOfRemovedSongs)) + GrammrRemovedSongs + "Removed ###################\033[0m\n")
    for i in ListOfRemovedSongs: print(re.sub(':', '/', i))

########################################################################
# This function takes an integer number of seconds as input and
# outputs a length of time in human-readable format.
# For example: 3 hours, 1 minute, and 2 seconds.
def formatTime(s):
    if s == 0: return('0 Seconds')
    tList = []
    hours = s // 3600
    strhours = '1 Hour' if hours == 1 else str(hours) + ' Hours'
    if hours != 0: tList.append(strhours)
  # print('Hour: ' + strhours)

    s = s - hours * 3600
    minutes = s // 60
    strminutes = '1 Minute' if minutes == 1 else str(minutes) + ' Minutes'
    if minutes != 0: tList.append(strminutes)
  # print('Minute: ' + strminutes)

    s = s - minutes * 60
    strseconds = '1 Second' if s == 1 else str('{0:g}'.format(s)) + ' Seconds'
    # strseconds = '1 Second' if s == 1 else str(s) + ' Seconds'
    if s != 0: tList.append(strseconds)
  # print('Second: ' + s)

  # print(tList)
    if len(tList) == 1: return(tList[0])
    if len(tList) == 2:
        return(tList[0] + ' and ' + tList[1])
    else:
        return(tList[0] + ', ' + tList[1] + ', and ' + tList[2])
########################################################################
if UpdateCount != 0:
    elapsedInt = (int(time.time())) - TimeStamp
    elapsed    = formatTime(elapsedInt)

    try: # You can't divide by zero!
      # The number of seconds per song to index the songs
        perSongInt = round(elapsedInt / UpdateCount, 2)
      # Use the line below instead of the above one if you don't want the number rounded
      # perSongInt = elapsedInt/UpdateCount
    except: perSongInt = 0


    perSong    = formatTime(perSongInt)

  # print how long it took to index the songs
    GrammrUp = '' if UpdateCount == 1 else 's'
    print('\033[95m\n#----------------------------------------------------#')
    print('It Took ' + elapsed + ' to Index ' + str(UpdateCount) + ' Song' + GrammrUp)
    if UpdateCount > 1: print(perSong + ' per Song\033[0m')

else:
    if len(SongsInPlaylist) == 0:
        print("\n\033[95mThere are no songs in " + PlaylistName['name'] + "!\033[0m")
    else:
        print("\n\033[91mNo New Songs\n\033[0m")

# print the number of songs in the playlist
if len(SongsInPlaylist) == 1:
    print("\033[95mThere's Only One Song in " + PlaylistName['name'] + "!")
    print('#----------------------------------------------------#\033[0m')
if len(SongsInPlaylist) > 1:
    print('\033[95mThere are ' + str(len(SongsInPlaylist)) + ' Songs in ' + PlaylistName['name'])
    print('#----------------------------------------------------#\033[0m')
