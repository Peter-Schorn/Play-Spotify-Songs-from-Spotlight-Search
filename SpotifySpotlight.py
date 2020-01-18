import os, shutil, re, subprocess, requests, spotipy, spotipy.util as util, time, sys
#################################################################

# This is where you specify the folder in which the songs will be stored
# TODO: **DO NOT** add a forward slash at the very end of the folder path
folder_location  = '/Users/yourUsername/Songs'

# TODO: Don't forget to enter your username below
username         = 'the username you use to login to Spotify'

# TODO: Make sure that you enter your client ID and secret into the appropriate locations
client_id        = 'client id enclosed in quotes'
client_secret    = 'client secret enclosed in quotes'

redirect_uri     = 'http://localhost/'
scope            = 'playlist-read-private'

################################################################
################################################################

custom_icon = True

# The system arguments are processed
if len(sys.argv) > 1:
    if sys.argv[1].casefold() == 'noicon':
      #       \033[95m = Red Color
        print('\n\033[95mIcons Have Been Disabled\033[0m\n')
        custom_icon = False; time.sleep(2)
    else:
        print(
        'This script only accepts one argument: \033[95mnoicon\033[0m\nOtherwise, custom icons will be added\n')
        time.sleep(5)

# The first 8 variables are assigned to a separate empty list,
# the next two are assinged to 0 as an integer,
# and the last is assigned to the current time in integer seconds
allSongs, allAlbums, allArtists, RmvdSongs, savedSongs, plylsts, \
UpdateCount, numm, TimeStamp = [], [], [], [], [], [], 0, 0, int(time.time())

pListsdir       = folder_location + '/Playlists/'
Imagedir        = folder_location + '/.Images/'
dirArtistImage  = Imagedir + 'Artists/'
dirAlbumImage   = Imagedir + 'Albums/'

# Hidden folders that contain all the artist and album images are created.
# This is so that each album and artist image is only downloaded once.
for f in (folder_location, pListsdir, Imagedir, dirArtistImage, dirAlbumImage):
    if not os.path.exists(f): os.mkdir(f)


# Download a custom Icon for the songs folder if has not previously been downloaded
SpotifyICNS = folder_location + '/.Images/Spotify.icns'
if not os.path.exists(SpotifyICNS):
    iconset = folder_location + '/.Images/Spotify.iconset/'
    os.mkdir(iconset)
    SpotifyPNG = iconset + 'icon_256x256.png'
    # SpotifyPNG = folder_location + '/.Images/Spotify.png'
    with open(SpotifyPNG, 'wb') as f:
        f.write(requests.get('https://i.ibb.co/89MbxQv/Spotify-Folder-Square.png').content)

    os.system('sips -z 256 256 ' + SpotifyPNG + ' >/dev/null')
    os.system('sips -z 128 128 ' + SpotifyPNG + ' -o ' + iconset + 'icon_128x128.png' + ' >/dev/null')
    os.system(
        'sips -z 32 32 ' + iconset + 'icon_128x128.png' + ' -o ' + iconset + 'icon_32x32.png' + ' >/dev/null')
    os.system(
        'sips -z 16 16 ' + iconset + 'icon_32x32.png' + ' -o ' + iconset + 'icon_16x16.png' + ' >/dev/null')
    os.system('iconutil -c icns ' + iconset + ' -o ' + SpotifyICNS)
    os.system('iconutil -c icns ' + iconset + ' -o ' + SpotifyICNS + ' >/dev/null')
    os.remove(SpotifyPNG); shutil.rmtree(iconset)

# Set the icon for the songs folder if it has not already been set
# An `Icon\r` file will be created when a custom icon is set.
# This line checks if this file exists and set the custom icon only if this file doesn't exist.

if not os.path.exists(folder_location + "/Icon\r"):
    try:
        subprocess.run(
            ['/usr/local/bin/fileicon', 'set', '-q', folder_location, SpotifyICNS])
    except: pass

################################################################

def download_tracks(tracks, plistURI):
    global allSongs, allArtists, allAlbums, UpdateCount

    # for each track in the playlist...
    for i, item in enumerate(tracks['items']):
        track         = item['track']

      # A URI is a unique identifier for each song, album, artist, playlist, etc...
        SongURI       = track['uri']

      # Ignore local songs; See http://bit.ly/2ssUqi5 for more info.
        if "spotify:local:" in SongURI or SongURI == "": continue

        ################################################################

        TheSong       = track['name']
        TheAlbum      = track['album']['name']
        TheArtist     = track['artists'][0]['name']

        albumURI      = track['album']['id']
        artistURI     = track['artists'][0]['id']

        # The URL for the album image is retrieved

        try:    AlbumImageURL = track['album']['images'][1]['url']
        except: AlbumImageURL = 'none'

        ################################################################

      # Finder does not allow files/folders to include a colon, so all occurences of them are removed.
      # Files/folders that start with a period will be hidden, so leading periods are removed.
      # For some bizarre reason, a shell-escaped `/` becomes a colon, so `/`s are replaced with colons.
      # For example, if you cd to your desktop and then run `mkdir Some:Folder`,
      # The name of the folder will be `Some/Folder`.
        for temp in [('[:]+', ''), ('/', ':'), ('^\.+', '')]:
            TheAlbum  = re.sub(temp[0], temp[1], TheAlbum)
            TheArtist = re.sub(temp[0], temp[1], TheArtist)
            TheSong   = re.sub(temp[0], temp[1], TheSong)

      # This will be the name of the song in finder.
      # You can pick and choose from `TheAlbum`, `TheArtist`, and `TheSong`
      # and create a different format for the name if you like.
      # Also make sure to update the lines below if you do this.
        myName        = TheSong + ' - ' + TheArtist

        ################################################################

        if TheAlbum  == "":
            TheAlbum  = "Unknown Album"

        if TheSong   == "":
            TheSong   = "Song " + str(i)
            myName    = TheSong + ' - ' + TheArtist

        if TheArtist == "":
            TheArtist = "Unknown Artist"
            myName    = TheSong

        ################################################################

        # Folders for the artists and albums are made if they don't already exist.
        dirArtistName = folder_location + "/" + TheArtist
        if not os.path.exists(dirArtistName):
            os.mkdir(dirArtistName)

        dirAlbumName = folder_location + "/" + TheArtist + "/" + TheAlbum
        if not os.path.exists(dirAlbumName):
            os.mkdir(dirAlbumName)

        ################################################################

      # Lists of all the songs, albums, and artists in all of the playlists are maintained.
      # These will later be compared with all of the downloaded songs.
        if not SongURI in allSongs:
            allSongs.append(SongURI)

        if not (dirAlbumName, albumURI, TheAlbum) in allAlbums:
            allAlbums.append((dirAlbumName, albumURI, TheAlbum))

        if not (dirArtistName, artistURI, TheArtist) in allArtists:
            allArtists.append((dirArtistName, artistURI, TheArtist))

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
                f.write("#!/bin/bash\n")
                f.write(
                    "osascript -e \'tell application \"Spotify\" to play track \"{}\" in context \"spotify:playlist:{}\"\'"
                        .format(SongURI, plistURI))

              # Store the album URI, artist URI, and a boolean
              # indicating the icon has not yet been set for the song.
                f.write('\n##' + albumURI + '\n#@' + artistURI + '\n#&false'
                        + '\n#al#' + AlbumImageURL)


          # The shell script is given permission to execute
            os.lchmod(dirName + "/Contents/MacOS/" + myName, 0o777)

            if not custom_icon: print(re.sub(':', '/', myName))

          # A count of all the songs that have been *NEWLY* downloaded is maintained
            UpdateCount += 1
          # print(UpdateCount)

        ################################################################
################################################################

token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)


if token:
    sp = spotipy.Spotify(auth=token)

  # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
  # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
  # TODO: This is where the Spotify Web API is queried using Spotipy.
  # Spotify only returns 100 songs at a time. Therefore, multiple requests are made.
  # Also note that there is a 10,000 track limit for playlists.

  # Retrieve all of a user's playlists
    playlists = sp.user_playlists(username)
  # playlists = sp.current_user_playlists()

  # For each of a user's playlists...
    for playlist in playlists['items']:
        tTracks     = playlist['tracks']['total']
        if tTracks == 0: continue
        plistName   = playlist['name']
        plistURI    = playlist['id']
        if playlist['images']:
            ImgURL  = playlist['images'][0]['url']
        else:
            ImgURL  = None

        for r in [('[:]+', ''), ('/', ':'), ('^\.+', '')]:
            plistName = re.sub(r[0], r[1], plistName)

      # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        plylsts.append([plistName, plistURI, ImgURL, tTracks])
                        # 0        # 1       # 2     # 3

    def dupCheck(PlistList):
        seen = []
        for x in PlistList:
            if x in seen: return True
            else: seen.append(x)

    while dupCheck(pNme[0] for pNme in plylsts):
        seenPlists = []
        for pList in plylsts:
            if pList[0] in seenPlists:
                if type(pList[0]) is list:
                    pList[0][1] += 1
                else:
                    pList[0] = [pList[0], 2]
            else: seenPlists.append(pList[0])

    for pList in plylsts:
        if type(pList[0]) is list: pList[0] = pList[0][0] + ' ' + str(pList[0][1])
  # TODO: plylsts = list of all the Spotify playlists $$$$$$$$$$$$$$$$$$$$$$$$$$$
  # TODO: [0:plistName, 1:plistURI, 2:ImgURL, 3:tTracks] $$$$$$$$$$$$$$$$$$$$$$$$


  # TODO: List of all the downloaded playlists
    svdPlylsts = []
    for dirApp in os.listdir(pListsdir):
        if dirApp.endswith('.app'):
            svdpListNme  = os.path.splitext(dirApp)[0]
            svdpListApth = pListsdir + dirApp
            svdpListEpth = svdpListApth + '/Contents/MacOS/' + svdpListNme
            svdpListURI  = (re.search('spotify:playlist:(.*)"', open(svdpListEpth, "r").read()).group(1))
          # TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
            svdPlylsts.append([svdpListNme, svdpListURI])
                               # 0          # 1


  # If a playlist has been renamed, then delete the saved version
    for svdApp in svdPlylsts:
        if not svdApp in [[plyst[0], plyst[1]] for plyst in plylsts]:
            if os.path.exists(pListsdir + svdApp[0] + '.app'):
                if not svdApp[0] in RmvdSongs: RmvdSongs.append(svdApp[0])
                result = re.match('^(.+?)\s\d+$', svdApp[0])
                if result: bgnName = result.group(1)
                else: bgnName = svdApp[0]
                for dupApp in os.listdir(pListsdir):
                    if dupApp.startswith(bgnName) and dupApp.endswith('.app'):
                        shutil.rmtree(pListsdir + dupApp)


    for pList in plylsts:
        pListApp = pListsdir + pList[0] + '.app'
        if not os.path.exists(pListApp):

            os.mkdir(pListApp)
            os.mkdir(pListApp + "/Contents")
            with open(pListApp + "/Contents/PkgInfo", "w+") as f:
                # This identifies the directory as an application
                f.write("APPL????")
            os.mkdir(pListApp + "/Contents/MacOS")
            with open(pListApp + "/Contents/MacOS/" + pList[0], "w+") as f:
                f.write("#!/bin/bash\n")
                f.write(
            "osascript -e \'tell application \"Spotify\" to set shuffling to true\' "
            "-e \'tell application \"Spotify\" to play track \"spotify:playlist:" + pList[1] + "\"\'")
            # The shell script is given permission to execute
            os.lchmod(pListApp + "/Contents/MacOS/" + pList[0], 0o777)

      # download the playlist image and convert it from jpeg to icns
        if not (os.path.exists(pListApp + "/Icon\r") or pList[2] is None) and custom_icon == True:
            iconset   = Imagedir + pList[1] + '.iconset/'
            os.mkdir(iconset)
            pListJPG  = Imagedir + pList[1] + '.jpeg'
            pListPNG  = iconset + 'icon_256x256.png'
            pListICNS = Imagedir + pList[1] + '.icns'

            with open(pListJPG, 'wb') as f:
                f.write(requests.get(pList[2]).content)

            os.system('sips -s format png ' + pListJPG + ' -o ' + pListPNG + ' >/dev/null')
            os.system('sips -z 256 256 ' + pListPNG + ' >/dev/null')
            os.system('sips -z 128 128 ' + pListPNG + ' -o ' + iconset + 'icon_128x128.png' + ' >/dev/null')
            os.system(
                'sips -z 32 32 ' + iconset + 'icon_128x128.png' + ' -o ' + iconset + 'icon_32x32.png' + ' >/dev/null')
            os.system(
                'sips -z 16 16 ' + iconset + 'icon_32x32.png' + ' -o ' + iconset + 'icon_16x16.png' + ' >/dev/null')
            os.system('iconutil -c icns ' + iconset + ' -o ' + pListICNS)
            os.remove(pListJPG); shutil.rmtree(iconset)

            try:
                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q',
                     pListApp, pListICNS])
            except: pass
            if os.path.exists(pListICNS): os.remove(pListICNS)

        ################################################################

        # continue

        tGrmmr = '' if pList[3] == 1 else 's'
        print('\033[95mIndexing ' + pList[0] + ' - ' + str(pList[3]) + ' Track' + tGrmmr + '\n\033[0m')

        for offset in range(0, 10000, 100):
            tracks = sp.user_playlist_tracks(username, pList[1], limit=100, offset=offset)
            if len(tracks['items']) == 0: print(''); break
            if pList[3] > 100:
                Lnum = offset + 1; Rnum = (Lnum + len(tracks['items']) -1)

                print('\n       \033[95mIndexing Tracks ' + '{:>3}'.format(Lnum) \
                      + ' - ' + '{:<3}'.format(Rnum) + '\033[0m\n')

            download_tracks(tracks, pList[1])

else:
    print("Can't get token for", username); sys.exit()

# TODO: DEBUG $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# sys.exit()

################################################################

# The URIs for the song and the associated artist and album are read straight out of the application.
# A boolean value—which is True if the Icon has already been set for the appliation, and False if it hasn't—
# is also read
for root, dirs, files in os.walk(folder_location):
    for dirApp in dirs:
        if dirApp.endswith('.app') and root != folder_location + '/Playlists':

            FileToRead   = os.path.join(root, dirApp) + '/Contents/MacOS/' + os.path.splitext(dirApp)[0]

          # These regular expressions retrieve the song URI, album URI, artist URI,
          # and URL for the album image.
          # TODO: savedSongs $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$ - savedSong[x]
                                                                           # full path to the song # 0
                                                                                # name of the song # 1
            savedSongURI   = (re.search('track "(.*)" in', open(FileToRead, "r").read()).group(1)) # 2
            savedAlbumURI  = (re.search("##(.*)", open(FileToRead, "r").read()).group(1))          # 3
            savedArtistURI = (re.search("#@(.*)", open(FileToRead, "r").read()).group(1))          # 4
            isIcon         = (re.search("#&(.*)", open(FileToRead, "r").read()).group(1))          # 5
                                                                                      # FileToRead # 6
            savedAlbURL    = (re.search("#al#(.*)", open(FileToRead, "r").read()).group(1))        # 7

          # The full file path, name, and URIs of the song
          # are appended as a sub-tuple to a tuple containing all of the downloaded songs.
          # This tuple is later compared to the list of songs in the playlist (see the next section).
            savedSongs.append((
                os.path.join(root, dirApp), os.path.splitext(dirApp)[0], savedSongURI,
                savedAlbumURI, savedArtistURI, isIcon, FileToRead, savedAlbURL))

# This is where the songs in the playlists are cross-referenced with the songs that have been downloaded.
# If a previously-downloaded song is no longer in a playlist, it will be deleted.

icnmsg = True
# for each of the downloaded songs
for savedSong in savedSongs:

    # This is where the Album image for the song is stored
    albumICNS = dirAlbumImage + savedSong[3] + '.icns'
                              # Album URI

    # This is where the Artist image for the song is stored
    artistICNS = dirArtistImage + savedSong[4] + '.icns'
                                # Artist URI

  # If the downloaded song is still in at least one of the playlists
    if savedSong[2] in allSongs:

      # If the icon has not already been set...
        if savedSong[5] == 'false' and custom_icon == True:
            if icnmsg: print('\033[95mApplying Song Icons\n\033[0m'); icnmsg = False

            if not os.path.exists(albumICNS) and savedSong[7] != 'none':

                iconset  = dirAlbumImage + savedSong[3] + '.iconset/'
                albumJPG = dirAlbumImage + savedSong[3] + '.jpeg'
                albumPNG = iconset + 'icon_256x256.png'
                os.mkdir(iconset)

              # Downlaod the album image
                with open(albumJPG, 'wb') as f:
                    f.write(requests.get(savedSong[7]).content)

              # This block converts the image from jpeg to apple's proprietary icns format.
              # This allow the icons to render faster in finder.
                os.system('sips -s format png ' + albumJPG + ' -o ' + albumPNG + ' >/dev/null')
                os.system('sips -z 256 256 ' + albumPNG + ' >/dev/null')
                os.system('sips -z 128 128 ' + albumPNG + ' -o ' + iconset + 'icon_128x128.png' + ' >/dev/null')
                os.system(
                    'sips -z 32 32 ' + iconset + 'icon_128x128.png' + ' -o ' + iconset + 'icon_32x32.png' + ' >/dev/null')
                os.system(
                    'sips -z 16 16 ' + iconset + 'icon_32x32.png' + ' -o ' + iconset + 'icon_16x16.png' + ' >/dev/null')
                os.system('iconutil -c icns ' + iconset + ' -o ' + albumICNS)
                os.remove(albumJPG); shutil.rmtree(iconset)


          # set the icon for the song
            if os.path.exists(albumICNS):
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         savedSong[0], albumICNS])
                    print(re.sub(':', '/', savedSong[1]))
                    numm += 1
                except: pass

          # Change a boolean to true, which indicates a custom icon has been set
          # (or an attempt has been made to set it). This way, the icon is only set once.
            readf = open(savedSong[6], 'r')
            fData = readf.read()
            readf.close()

            rData = fData.replace("#&false", "#&true")

            readf = open(savedSong[6], 'w')
            readf.write(rData)
            readf.close()


  # If the downloaded song is no longer in any playlists
    else:
        RmvdSongs.append(savedSong[1])

      # if there are no longer any songs belonging to the album of the removed song,
      # then delete the album image.
        if not savedSong[3] in [albI[1] for albI in allAlbums]:
            if os.path.exists(albumICNS): os.remove(albumICNS)

      # If there are no longer any songs belonging to the artist of the removed song,
      # then delete the artist image.
        if not savedSong[4] in [arI[1] for arI in allArtists]:
            if os.path.exists(artistICNS): os.remove(artistICNS)

      # Delete the song itself
        shutil.rmtree(savedSong[0])

########################################################################

if custom_icon:
    artMsg = True; alMsg = True

  # Apply artist images to artist folders
    for artistI in allArtists:

      # if the icon has not already been set for the artist folder
        if not os.path.exists(artistI[0] + "/Icon\r"):
            if artMsg: print('\n\033[95mApplying Artist Icons\n\033[0m'); artMsg = False

          # if the icon does not already exist, then...
            artistICNS = dirArtistImage + artistI[1] + '.icns'
            if not os.path.exists(artistICNS):

                iconset   = dirArtistImage + artistI[1] + '.iconset/'
                artistJPG = dirArtistImage + artistI[1] + '.jpeg'
                artistPNG = iconset + 'icon_256x256.png'

                try:
                    ArtInfo   = sp.artist(artistI[1])
                    ArtImgURL = ArtInfo['images'][1]['url']

                  # Download the artist image
                    with open(artistJPG, 'wb') as f:
                        f.write(requests.get(ArtImgURL).content)
                except: pass
                else:
                    os.mkdir(iconset)

                  # Convert from jpeg to png
                    os.system('sips -s format png ' + artistJPG + ' -o ' + artistPNG + ' >/dev/null')
                  # Convert from png to icns
                    os.system('sips -z 256 256 ' + artistPNG + ' >/dev/null')
                    os.system('sips -z 128 128 ' + artistPNG + ' -o ' + iconset + 'icon_128x128.png' + ' >/dev/null')
                    os.system(
                        'sips -z 32 32 ' + iconset + 'icon_128x128.png' + ' -o ' + iconset + 'icon_32x32.png' + ' >/dev/null')
                    os.system(
                        'sips -z 16 16 ' + iconset + 'icon_32x32.png' + ' -o ' + iconset + 'icon_16x16.png' + ' >/dev/null')
                    os.system('iconutil -c icns ' + iconset + ' -o ' + artistICNS)
                    os.remove(artistJPG); shutil.rmtree(iconset)

          # Set the icon for the artist folder
            if os.path.exists(artistICNS):
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         artistI[0], artistICNS])
                    print(re.sub(':', '/', artistI[2])); numm += 1
                except: pass

  # Apply album images to album folders
    for albumI in allAlbums:
        if not os.path.exists(albumI[0] + "/Icon\r"):
            if os.path.exists(dirAlbumImage + albumI[1] + '.icns'):
                if alMsg: print('\n\033[95mApplying Album Icons\n\033[0m'); alMsg = False
                try:
                    subprocess.run(
                        ['/usr/local/bin/fileicon', 'set', '-q',
                         albumI[0], dirAlbumImage + albumI[1] + '.icns'])
                    print(re.sub(':', '/', albumI[2])); numm += 1
                except: pass

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

      # if the list of normal files in the folder is empty, then delete the folder
        if not nFs: shutil.rmtree(os.path.join(root, dir))


# Displays a list of removed songs
if RmvdSongs:# if list is not empty, then...
    GrammrRemovedSongs = ' Item Was ' if len(RmvdSongs) == 1 else ' Items Were '
    print(
        "\n\033[91m################### " + str(len(RmvdSongs)) + GrammrRemovedSongs + "Removed ###################\033[0m\n")
    for i in RmvdSongs: print(re.sub(':', '/', i))

########################################################################
# This function takes an integer number of seconds as input and
# outputs a length of time in human-readable format with correct grammar.
# For example: 3 hours, 1 minute, and 2 seconds.
def formatTime(s):
    if s == 0: return '0 Seconds'
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
    if   len(tList) == 1: return tList[0]
    elif len(tList) == 2:
        return tList[0] + ' and ' + tList[1]
    else:
        return tList[0] + ', ' + tList[1] + ', and ' + tList[2]

########################################################################

if UpdateCount + numm != 0:
    if UpdateCount == 0:
        print("\n\033[91mNo New Songs\n\033[0m")
        prCnt    = numm
        iCnOrInx = ' to Apply an Icon to ' if prCnt == 1 else ' to Apply Icons to '
        sngOrItm = ' Item'
    else:
        iCnOrInx = ' to Update '
        prCnt    = UpdateCount
        sngOrItm = ' Song'

    elapsedInt   = (int(time.time())) - TimeStamp
    elapsed      = formatTime(elapsedInt)

    try:
      # The number of seconds per item to index/apply icons to the items
        perItemInt = round(elapsedInt / prCnt, 2)
    except ZeroDivisionError: perItemInt = 0

    perItem    = formatTime(perItemInt)

  # print how long it took to index the songs
    GrammrUp = '' if prCnt == 1 else 's'
    FinalMsg = 'It Took ' + elapsed + iCnOrInx + str(prCnt) + sngOrItm + GrammrUp
    print('\033[95m\n#----------------------------------------------------#')
    print(FinalMsg)
    if prCnt > 1: print(perItem + ' per' + sngOrItm + '\033[0m')
    print('')

  # see https://apple.co/2N9hedH for more info about applescript notifications
    os.system(
r'osascript -e "display notification \"' + FinalMsg + r'\" with title \"Indexing Finished\" sound name \"Glass\""')

else:
    print("\n\033[91mNo New Songs or Icons to Apply\n\033[0m")
    os.system(
r'osascript -e "display notification \"No New Songs or Icons to Apply\" sound name \"Glass\""')
