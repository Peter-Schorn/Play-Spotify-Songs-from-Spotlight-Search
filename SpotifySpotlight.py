import os, shutil, re, subprocess, requests, \
    spotipy, spotipy.util as util, time, sys
#################################################################

# This is where you specify the folder in which the songs will be stored
# TODO: **DO NOT** add a forward slash at the very end of the folder path
folder_location  = '/Users/myUsername/Songs'

username         = 'the username you use to log into spotify'

client_id        = os.environ.get('CLIENT_ID')

client_secret    = os.environ.get('CLIENT_SECRET')


redirect_uri     = 'http://localhost/'
scope            = 'user-library-read'

################################################################
################################################################
custom_icon = True

# The system arguments are processed
if len(sys.argv) > 1:
    if sys.argv[1].casefold() == 'noicon'.casefold():
      #       \033[95m = Red Color
        print('\n\033[95mIcons Have Been Disabled\033[0m\n'); custom_icon = False
    else:
        print(
        'This script only accepts one argument: \033[95mnoicon\033[0m\nOtherwise, custom icons will be added\n')
        time.sleep(5)

# The first 8 variables are assigned to a separate empty list,
# the next two are assinged to 0 as an integer,
# and the last is assigned to the current time in integer seconds
blankNames, songsInPlaylists, playlistAlbums, playlistArtists, albumIcons, \
artistIcons, ListOfRemovedSongs, IndexedSongs, UpdateCount, numm, TimeStamp = \
[], [], [], [], [], [], [], [], 0, 0, int(time.time())

dirArtistImage   = folder_location + '/.Images/Artists/'
dirAlbumImage    = folder_location + '/.Images/Albums/'

# Hidden folders that contain all the artist and album images are created.
# This is so that each album and artist image is only downloaded once.
for f in (folder_location, folder_location + '/.Images/', dirArtistImage, dirAlbumImage):
    if not os.path.exists(f): os.mkdir(f)

################################################################

def download_tracks(tracks):
    global blankNames, songsInPlaylists, playlistAlbums, \
           playlistArtists, UpdateCount, artistIcons, albumIcons
    # for each track in the playlist...
    for i, item in enumerate(tracks['items']):
        track           = item['track']

      # A URI is a unique identifier for each song, album, artist, playlist, etc...
        SongURI         = track['uri']

      # Ignore local songs; See http://bit.ly/2ssUqi5 for more info.
        if "spotify:local:" in SongURI or SongURI == "": continue

        ################################################################

        TheSong         = track['name']
        TheAlbum        = track['album']['name']
        TheArtist       = track['artists'][0]['name']

        albumURI        = track['album']['id']
        artistURI       = track['artists'][0]['id']

        ################################################################

      # Finder does not allow files/folders to include a colon, so all occurences of them are removed.
      # Files/folders that start with a period will be hidden, so leading periods are removed.
      # For some bizarre reason, a shell-escaped `/` becomes a colon, so `/`s are replaced with colons.
      # For example, if you cd to your desktop and then run `mkdir Some:Folder`,
      # The name of the folder will be `Some/Folder`.
        for temp in [('[:]+', ''), ('/', ':'), ('^\.+', '')]:
            TheAlbum    = re.sub(temp[0], temp[1], TheAlbum)
            TheArtist   = re.sub(temp[0], temp[1], TheArtist)
            TheSong     = re.sub(temp[0], temp[1], TheSong)

      # This will be the name of the song in finder.
      # You can pick and choose from `TheAlbum`, `TheArtist`, and `TheSong`
      # and create a different format for the name if you like.
      # Also make sure to update lines 66 and 95 if you do this.
        myName = TheSong + ' - ' + TheArtist

        ################################################################

        if TheAlbum    == "":
            TheAlbum    = "Unknown Album"

        if TheSong     == "":
            TheSong     = "Song " + str(i)
            myName      = TheSong + ' - ' + TheArtist

        if TheArtist   == "":
            TheArtist   = "Unknown Artist"
            myName      = TheSong

        ################################################################

      # Creates a list of all the songs in the playlist.
      # This will later be compared with all of the downloaded songs
        if not SongURI in songsInPlaylists:
            songsInPlaylists.append(SongURI)

        if not albumURI in playlistAlbums:
            playlistAlbums.append(albumURI)

        if not artistURI in playlistArtists:
            playlistArtists.append(artistURI)

        ################################################################
      # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
      # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

      # Folders for the artists and albums are made if they don't already exist.
        dirArtistName   = folder_location + "/" + TheArtist
        if not os.path.exists(dirArtistName):
            os.mkdir(dirArtistName)

        dirAlbumName = folder_location + "/" + TheArtist + "/" + TheAlbum
        if not os.path.exists(dirAlbumName):
            os.mkdir(dirAlbumName)

        ################################################################

      # This is where the song will be saved
        dirName = folder_location + "/" + TheArtist + "/" + TheAlbum + "/" + myName + ".app"

      # Only create the song if it has not already been saved.
        if not os.path.exists(dirName):

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
                    "osascript -e \'tell application \"Spotify\" to play track \"{}\" in context \"spotify:album:{}\"\'"
                        .format(SongURI, albumURI))
                f.write("\n##" + artistURI + "\n###false")

          # The shell script is given permission to execute
            os.lchmod(dirName + "/Contents/MacOS/" + myName, 0o777)

            if custom_icon == False: print(myName)

          # A list of all the songs that have been downloaded is maintained
            UpdateCount += 1

        ################################################################

        if custom_icon == True:

            # A list of all the artists in the playlists is maintained
            if not (dirArtistName, artistURI, TheArtist) in artistIcons:
                artistIcons.append((dirArtistName, artistURI, TheArtist))

            # A list of all the albums in the playlist
            if not (dirAlbumName, albumURI, TheAlbum) in albumIcons:
                albumIcons.append((dirAlbumName, albumURI, TheAlbum))


            try:# to get the album image

              # Only download the album image if it has not already been downloaded
                if not os.path.exists(dirAlbumImage + albumURI + '.jpeg'):

                  # You can change the number in the line below to change
                  # the size of the image that is downloaded.
                  # 0 = 640 x 640 pixels
                  # 1 = 300 x 300 pixels
                  # 2 = 64  x 64  pixels
                    ImageURL = track['album']['images'][1]['url']

                  # Download the album image from the internet
                    with open(dirAlbumImage + albumURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ImageURL).content)

            except: pass

            try:# to get the artist image

              # Only download the artist image if it has not already been downloaded
                if not os.path.exists(dirArtistImage + artistURI + '.jpeg'):

                    Artist         = sp.artist(track['artists'][0]['uri'])

                    # You can change the number in the line below to change
                    # the size of the image that is downloaded.
                    # 0 = 640 x 640 pixels
                    # 1 = 320 x 320 pixels
                    # 2 = 160 x 160 pixels
                    ArtistImageURL = Artist['images'][1]['url']

                  # Download the artist image from the internet
                    with open(dirArtistImage + artistURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ArtistImageURL).content)

            except: pass

        ################################################################
################################################################

token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)


if token:
    sp = spotipy.Spotify(auth=token)

  # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
  # TODO: This is where the Spotify Web API is queried using Spotipy.
  # Spotify only returns 100 songs at a time. Therefore, multiple requests are made.
  # Also note that there is a 10,000 track limit for playlists.

  # Retrieve all of a user's playlists
    playlists = sp.user_playlists(username)
  # For each of a user's playlists...
    for playlist in playlists['items']:
        plistName = playlist['name']
        plistURI  = playlist['uri']
        tTracks   = playlist['tracks']['total']
        if tTracks == 0: continue
        tGrmmr = '' if tTracks == 1 else 's'

        print('\033[95mIndexing ' + plistName + ' - ' + str(tTracks) + ' Track' + tGrmmr + '\n\033[0m')

        for offset in range(0, 10000, 100):
            tracks = sp.user_playlist_tracks(username, plistURI, limit=100, offset=offset)
            if len(tracks['items']) == 0: print(''); break
            if tTracks > 100:
                Lnum = offset + 1; Rnum = Lnum + len(tracks['items'])

                print('\n       \033[95mIndexing Tracks ' + '{:>3}'.format(Lnum) \
                      + ' - ' + '{:<3}'.format(Rnum) + '\033[0m\n')

            download_tracks(tracks)
        # break


  # The URIs for the song and the associated artist and album are read straight out of the application.
  # A boolean value—which is True if the Icon has already been set for the appliation, and False if it hasn't—
  # is also read
    for root, dirs, files in os.walk(folder_location):
        for dirApp in dirs:
            if dirApp.endswith('.app'):
                FileToRead   = os.path.join(root, dirApp) + '/Contents/MacOS/' + os.path.splitext(dirApp)[0]       # 6

              # These regular expressions retrieve the song URI, album URI, and artist URI
              #TODO IndexedSongs:
                savedSongURI   = (re.search('track "(.*)" in', open(FileToRead, "r").read()).group(1))       # 2
                savedAlbumURI  = (re.search("spotify:album:(.*)\"'", open(FileToRead, "r").read()).group(1)) # 3
                savedArtistURI = (re.search("##(.*)", open(FileToRead, "r").read()).group(1))                # 4
                isIcon         = (re.search("###(.*)", open(FileToRead, "r").read()).group(1))               # 5

              # The full file path, name, and URIs of the song
              # are appended as a sub-tuple to a tuple containing all of the downloaded songs.
              # This tuple is later compared to the list of songs in the playlist (see the next section).
                IndexedSongs.append((
                    os.path.join(root, dirApp), os.path.splitext(dirApp)[0],
                    savedSongURI, savedAlbumURI, savedArtistURI, isIcon, FileToRead))

  # This is where the songs in the playlists are cross-referenced with the songs that have been downloaded.
  # If a previously-downloaded song is no longer in a playlist, it will be deleted.

    # for each of the downloaded songs...
    icnmsg = True
    for indexSong in IndexedSongs:

        # This is where the Album image for the song is stored
        albumImagePath = dirAlbumImage + indexSong[3] + '.jpeg'

        # This is where the Artist image for the song is stored
        artistImagePath = dirArtistImage + indexSong[4] + '.jpeg'

      # If the downloaded song is still in the playlist
        if  indexSong[2] in songsInPlaylists:

          # If the icon has not already been set...
            if indexSong[5] == 'false' and custom_icon == True:
                if icnmsg: print('\033[95mApplying Song Icons\n\033[0m'); icnmsg = False
              # set the icon for the song
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         indexSong[0], albumImagePath])
                    print(indexSong[1])
                    numm += 1
                except: pass

              # Change a boolean to True, which indicates a custom icon has been set.
              # This way, the icon is only set once.
                readf = open(indexSong[6], 'r')
                fData = readf.read()
                readf.close()

                rData = fData.replace("###false", "###true")

                readf = open(indexSong[6], 'w')
                readf.write(rData)
                readf.close()

      # If the song is not in the playlist..
        else:
            ListOfRemovedSongs.append(
                (indexSong[5], indexSong[1], 'Album URI: [' + indexSong[3] + ']',
                 'Artist URI: [' + indexSong[4] + ']'))

          # if there are no longer any songs belonging to the album of the removed song,
          # then delete the album image.
            if not indexSong[3] in playlistAlbums:
                try: os.remove(albumImagePath)
                except: pass

          # If there are no longer any songs belonging to the artist of the removed song,
          # then delete the artist image
            if not indexSong[4] in playlistArtists:
                try: os.remove(artistImagePath)
                except: pass


            # Delete the song itself
            shutil.rmtree(indexSong[0])

    ########################################################################
  #TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
  #TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
  #TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

    if len(artistIcons) + len(albumIcons) != 0 and custom_icon == True:
        artMsg = True; alMsg = True

      # Apply artist images to artist folders
        for artistI in artistIcons:
            if not os.path.exists(artistI[0] + "/Icon\r"):
                if artMsg: print('\n\033[95mApplying Artist Icons\n\033[0m'); artMsg = False
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         artistI[0], dirArtistImage + artistI[1] + '.jpeg'])
                    print(artistI[2])
                    numm += 1
                except: pass # print('Error Setting Icon for Artist: ' + artistI[2])
            # else: print('Icon already set for Artist: ' + artistI[2])

      # Apply album images to album folders
        for albumI in albumIcons:
            if not os.path.exists(albumI[0] + "/Icon\r"):
                if alMsg: print('\n\033[95mApplying Album Icons\n\033[0m'); alMsg = False
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         albumI[0], dirAlbumImage + albumI[1] + '.jpeg'])
                    print(albumI[2])
                    numm += 1
                except: pass # print('Error Setting Icon for Album: ' + albumI[2])
            # else: print('Icon already set for Album: ' + albumI[2])


    ########################################################################

    # A list of renamed songs is printed.
    # Empty lists evaluate to true;
    # non-empty lists evaluate to false.
    if blankNames:# if the list is not empty, then...
        GrammrRe = ' Song Was ' if len(blankNames) == 1 else ' Songs Were '

        print("\n\033[91m################### " + str(len(blankNames)) + GrammrRe + "Renamed ###################\033[0m\n")
        for i in blankNames: print(i)

    ########################################################################

    # If all the songs/albums for an album/artist, respectively, are removed,
    # then the album/artist folder is deleted.
    # All directories contain a hidden `.DS_Store` file.
    # see http://bit.ly/2Fdh8NR to read all about it
    # Also, When a custom icon is set for a finder item, a hidden `icon?` file is created.
    # This file is extra-special in that it it hidden, yet does not begin with a period,
    # Unlike all other hidden files!
    # This block deletes all folders that only contain `icon?` files and files beginning with a period.
    for root, dirs, files in os.walk(folder_location, topdown=False):
        for dir in dirs:
            nFs = [] # list of normal files
            for item in os.listdir(os.path.join(root, dir)):
                if not (item == "Icon\r" or item.startswith('.')): nFs.append(item)
            if not nFs: shutil.rmtree(os.path.join(root, dir))


    # Displays a list of removed songs
    if ListOfRemovedSongs:# if list is not empty, then...
        GrammrRemovedSongs = ' Song Was ' if len(ListOfRemovedSongs) == 1 else ' Songs Were '
        print(
            "\n\033[91m################### " + str(len(ListOfRemovedSongs)) + GrammrRemovedSongs + "Removed ###################\033[0m\n")
        # for i in ListOfRemovedSongs: print(re.sub(':', '/', i))
        for i in ListOfRemovedSongs: print(str(i[1]))

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
    if UpdateCount + numm != 0:
        if UpdateCount == 0:
            print("\n\033[91mNo New Songs\n\033[0m")
            prCnt     = numm
            iCnOrInx  = ' to Apply an Icon to ' if prCnt == 1 else ' to Apply Icons to '
            sngOrItm  = ' Item'
        else:
            iCnOrInx  = ' to Update '
            prCnt     = UpdateCount
            sngOrItm  = ' Song'

        elapsedInt    = (int(time.time())) - TimeStamp
        elapsed       = formatTime(elapsedInt)

        try: # You can't divide by zero!
          # The number of seconds per song to index the songs
            perSongInt = round(elapsedInt / UpdateCount, 2)
          # Use the line below instead of the above one if you don't want the number rounded
          #   perSongInt = elapsedInt/prCnt
        except: perSongInt = 0


        perSong    = formatTime(perSongInt)

      # print how long it took to index the songs
        GrammrUp = '' if prCnt == 1 else 's'
        print('\033[95m\n#----------------------------------------------------#')
        print('It Took ' + elapsed + iCnOrInx + str(prCnt) + sngOrItm + GrammrUp)
        if prCnt > 1: print(perSong + ' per Song\033[0m')
        
        os.system("osascript -e \"display notification with title \\\"Indexing Finished\\\"\"")  
        
    else:
        print("\n\033[91mNo New Songs or Icons to Apply\n\033[0m")

else:
    print("Can't get token for", username)
