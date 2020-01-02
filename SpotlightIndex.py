import os
import sys
import shutil
import re
import subprocess
import requests
import spotipy
import spotipy.util as util
import time
#################################################################
#################################################################
custom_icon         =  True
playlist            = '2z212MPinIr8HesnJ68UoF'
folder_location     = '/Users/pschorn/TempSongs'
username            = 'petervschorn'

client_id           = os.environ.get('CLIENT_ID')
client_secret       = os.environ.get('CLIENT_SECRET')
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


for f in (folder_location, folder_location + '/.Images/', dirArtistImage, dirAlbumImage):
    if not os.path.exists(f): os.mkdir(f)

# if not os.path.exists(folder_location): os.mkdir(folder_location)
# if not os.path.exists(folder_location + '/.Images/'): os.mkdir(folder_location + '/.Images/')
# if not os.path.exists(dirArtistImage): os.mkdir(dirArtistImage)
# if not os.path.exists(dirAlbumImage): os.mkdir(dirAlbumImage)



################################################################

def download_tracks(tracks):
    global UpdateCount
    for i, item in enumerate(tracks['items']):
        track           = item['track']
        SongURI         = track['uri']
      # Ignore local songs
        if "spotify:local:" in SongURI or SongURI == "": continue
        ################################################################

        myNameExact     = track['name'] + " - " + track['artists'][0]['name']
        myNamePrint     = myNameExact

        myName          = myNameExact
        TheSong         = track['name']
        TheAlbum        = track['album']['name']
        TheArtist       = track['artists'][0]['name']

        AlbumURIContext = track['album']['uri']
        AlbumURI        = re.sub('^spotify:album:', '', AlbumURIContext)
        ArtistURI       = track['artists'][0]['uri']
        ArtistURI       = re.sub('^spotify:artist:', '', ArtistURI)

        ################################################################

        for temp in [('[:]+', ''), ('/', ':'), ('^\.+', '')]:
            myName      = re.sub(temp[0], temp[1], myName)
            TheAlbum    = re.sub(temp[0], temp[1], TheAlbum)
            TheArtist   = re.sub(temp[0], temp[1], TheArtist)
            TheSong     = re.sub(temp[0], temp[1], TheSong)
            myNameExact = re.sub(temp[0], temp[1], myNameExact)

        ################################################################

        SongsInPlaylist.append(myNameExact)

        if not AlbumURI in PlaylistAlbumsList:
            PlaylistAlbumsList.append(AlbumURI)

        if not ArtistURI in PlaylistArtistsList:
            PlaylistArtistsList.append(ArtistURI)

        ################################################################

        if TheAlbum     == "":
            TheAlbum    = "Unknown Album"
            AlbumKnown  = False
        else:
            AlbumKnown  = True

        if TheSong      == "":
            TheSong     = "Song " + str(i)
            myName      = TheSong + " - " + TheArtist
            BlankName   = True
        else:
            BlankName   = False

        if TheArtist    == "":
            TheArtist   = "Unknown Artist"
            myNamePrint = track['name']
            myName      = TheSong

        ################################################################
        dirArtistName   = folder_location + "/" + TheArtist
        if not os.path.exists(dirArtistName): os.mkdir(dirArtistName)

        dirAlbumName    = folder_location + "/" + TheArtist + "/" + TheAlbum
        if not os.path.exists(dirAlbumName): os.mkdir(dirAlbumName)
        ################################################################

        dirName = folder_location + "/" + TheArtist + "/" + TheAlbum + "/" + myName + ".app"

        if os.path.exists(dirName):
            continue
        os.mkdir(dirName)
        os.mkdir(dirName + "/Contents")
        with open(dirName + "/Contents/PkgInfo", "w+") as f:
            f.write("APPL????")
        os.mkdir(dirName + "/Contents/MacOS")
        with open(dirName + "/Contents/MacOS/" + myName, "w+") as f:
            f.write("#!/bin/bash\n")
            f.write(
                "osascript -e \'tell application \"Spotify\" to play track \"{}\" in context \"{}\"\'"
                    .format(SongURI, AlbumURIContext))
        os.lchmod(dirName + "/Contents/MacOS/" + myName, 0o777)

        ################## SET ALBUM AND ARTIST IMAGE ##################

        if custom_icon == True:
            try:# to get the album image

              # Only download the album image if it has not already been downloaded
                if not os.path.exists(dirAlbumImage + AlbumURI + '.jpeg'):

                    ImageURL = track['album']['images'][1]['url']

                    with open(dirAlbumImage + AlbumURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ImageURL).content)

                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirName,
                     dirAlbumImage + AlbumURI + '.jpeg'])

                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirAlbumName,
                     dirAlbumImage + AlbumURI + '.jpeg'])

            except:
                pass

            try:# to get the artist image

              # Only download the artist image if it has not already been downloaded
                if not os.path.exists(dirArtistImage + ArtistURI + '.jpeg'):

                    Artist         = sp.artist(track['artists'][0]['uri'])

                    ArtistImageURL = Artist['images'][1]['url']

                    with open(dirArtistImage + ArtistURI + '.jpeg', 'wb') as f:
                        f.write(requests.get(ArtistImageURL).content)

                subprocess.run(
                    ['/usr/local/bin/fileicon', 'set', '-q', dirArtistName,
                     dirArtistImage + ArtistURI + '.jpeg'])

            except:
                pass

        ################ END SET ALBUM AND ARTIST IMAGE ################

        if BlankName == True: # then notify user that song has been saved as 'Song ' + str(i)
            if AlbumKnown == True:
                (BlankNamesList.append
                    ('\033[91m' + myNamePrint + " (from " + TheAlbum + ") saved as --> " + myName + '\033[0m'))
            else:
                (BlankNamesList.append
                    ('\033[91m' + myNamePrint + " saved as --> " + myName + '\033[0m'))

        else:
            print(myNamePrint)


        UpdateCount += 1
      # print("###################################################################")
        ################################################################
########################################################################


token = util.prompt_for_user_token(username, scope, client_id, client_secret, redirect_uri)

#TODO $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
#TODO $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
if token:
    sp = spotipy.Spotify(auth=token)
    PlaylistName = sp.user_playlist(username, playlist, fields="name")
    print('\033[95m' + "Indexing " + PlaylistName['name'] + "...")
    print('\033[0m')
    for offset in range(0, 10000, 100):
        tracks = sp.user_playlist_tracks(username, playlist, limit=100, offset=offset)
        if len(tracks['items']) == 0: break
        download_tracks(tracks)

    IndexedSongs = []
    for root, dirs, files in os.walk(folder_location):
        for dir in dirs:
            if dir.endswith('.app'):
                FileToRead   = os.path.join(root, dir) + '/Contents/MacOS/' + os.path.splitext(dir)[0]
                SavedSongURI = (re.search('track "(.*)" in', open(FileToRead, "r").read()).group(1))

                IndexedSongs.append(
                    (os.path.join(root, dir), (os.path.splitext(dir)[0]), SavedSongURI))

    ListOfRemovedSongs = []
    for SavedSong in IndexedSongs:
        if not SavedSong[1] in SongsInPlaylist:
            ListOfRemovedSongs.append(SavedSong[1])

            TrackInfo       = sp.track(SavedSong[2])

            SavedAlbumURI   = TrackInfo['album']['id']
            AlbumImagePath  = dirAlbumImage + SavedAlbumURI + '.jpeg'

            SavedArtistURI  = TrackInfo['artists'][0]['id']
            ArtistImagePath = dirArtistImage + SavedArtistURI + '.jpeg'

            if not SavedAlbumURI in PlaylistAlbumsList:
                try:
                    os.remove(AlbumImagePath)
                except:
                    pass

            if not SavedArtistURI in PlaylistArtistsList:
                try:
                    os.remove(ArtistImagePath)
                except:
                    pass

            shutil.rmtree(SavedSong[0])

else:
    print("Can't get token for", username)

########################################################################
if BlankNamesList:# if list is not empty, then...
    GrammrRe = ' Song Was ' if len(BlankNamesList) == 1 else ' Songs Were '

    print("\n\033[91m################### " + str(len(BlankNamesList)) + GrammrRe + "Renamed ###################\033[0m\n")
    for i in BlankNamesList: print(i)

########################################################################

if ListOfRemovedSongs:# if list is not empty, then...
    GrammrRemovedSongs = ' Song Was ' if len(ListOfRemovedSongs) == 1 else ' Songs Were '
    print(
        "\n\033[91m################### " + str(len(ListOfRemovedSongs)) + GrammrRemovedSongs + "Removed ###################\033[0m\n")
    for i in ListOfRemovedSongs: print(re.sub(':', '/', i))

def rmEmptyFolder(dir):
    for item in os.listdir(dir):
        if not (item == "Icon\r" or item.startswith('.')):
            return
    shutil.rmtree(dir)

for root, dirs, files in os.walk(folder_location, topdown=False):
    for dir in dirs:
        rmEmptyFolder(os.path.join(root, dir))

########################################################################
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
  # print(s)

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

    try:
      # perSongInt = round(elapsedInt / UpdateCount, 2)
        perSongInt = elapsedInt/UpdateCount
    except: perSongInt = 0

    perSong     = formatTime(perSongInt)

    GrammrUp = '' if UpdateCount == 1 else 's'
    print('\033[95m\n#----------------------------------------------------#')
    print('It Took ' + elapsed + ' to Index ' + str(UpdateCount) + ' Song' + GrammrUp)
    if UpdateCount > 1: print(perSong + ' per Song\033[0m')

else:
    if len(SongsInPlaylist) == 0:
        print("\033[95mThere are no songs in " + PlaylistName['name'] + "!\033[0m")
    else:
        print("\n\033[91mNo New Songs\n\033[0m")

if len(SongsInPlaylist) == 1:
    print("\033[95mThere's Only One Song in " + PlaylistName['name'] + "!")
    print('#----------------------------------------------------#\033[0m')
if len(SongsInPlaylist) > 1:
    print('\033[95mThere are ' + str(len(SongsInPlaylist)) + ' Songs in ' + PlaylistName['name'])
    print('#----------------------------------------------------#\033[0m')