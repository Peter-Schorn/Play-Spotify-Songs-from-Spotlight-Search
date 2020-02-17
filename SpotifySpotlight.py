# -*- coding: utf-8 -*-
import os, shutil, re, subprocess, requests, pickle, \
       spotipy, time, sys, bisect
from pathlib import Path; from PIL import Image
from pkg_resources import get_distribution
scope = 'playlist-read-private'

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
cachePath = os.path.join(str(Path.home()), '.cache_{}_{}'.format(username, scope))

###############################################################
###############################################################
###############################################################

# TODO: $$$$$$$$$$$$$$$$$$$ -- CONSTANTS -- $$$$$$$$$$$$$$$$$$$

print()

# TODO: Check that the Spotipy version is >= 2.8.0
spotipyVers = get_distribution('spotipy').version
intSpotipyVers = spotipyVers.split('.')
expectedVersion = [2, 8, 0]
for ic, ie in zip(intSpotipyVers, expectedVersion):
    if int(ic) < ie:
        print('The version of the Spotipy module you have is {}\n'
              'You need {} or greater for this script to work.\n'
              'If you have pip, you can upgrade spotipy by running\n\n'
              '\033[95mpip install spotipy --upgrade\033[0m'
              .format(str(spotipyVers),
              '.'.join(str(jie) for jie in expectedVersion)),
              end='\n\n')
        sys.exit()
    elif int(ic) == ie: continue
    break

if len(sys.argv) > 1 and sys.argv[1] in \
('___chngPlist___', '___chngAlb___', '___rnPlist___'):
    isMain = False
else:
    isMain = True

# TODO: Retrieve client id and client secret
if os.path.exists(credentials):
    with open(credentials) as crdnts:
        rdcrednts = crdnts.read()
        client_id = re.search(r'client[\W_]*id[\W]*([a-zA-Z0-9]+)', rdcrednts)
        if client_id: client_id = client_id.group(1).strip()
        else: print("Couldn't find client id")
        client_secret = re.search(r'client[\W_]*secret[\W]*([a-zA-Z0-9]+)', rdcrednts)
        if client_secret: client_secret = client_secret.group(1).strip()
        else: print("Couldn't find client secret")
    if not client_id or not client_secret: print(); sys.exit()
else:
    print('The file where your client id and client secrets are stored could not be found:'
          '\n' + credentials + '\n')
    sys.exit()

spAlbums       = {}
spArtists      = {}
spSongs        = {}
spPlists       = {}
rmvdItems      = ([], [])  # ([removed songs], [removed playlists])
updCnt         = 0
TimeStamp      = int(time.time())
fullScriptPath = sys.executable + ' ' + sys.argv[0]
redirect_uri   = 'http://localhost/'

# Hidden folders that contain all the artist and album images are created.
# This is so that each album and artist image is only downloaded once.
plistsDir = os.path.join(folder_location, 'Playlists/')
dataDir   = os.path.join(folder_location, '.Data/')
artImgDir = os.path.join(dataDir, 'Artists/')
albImgDir = os.path.join(dataDir, 'Albums/')
pickleDir = dataDir + 'Pickle'

# TODO: Check if fileicon is installed
if os.path.exists(fileicon_path):
    if custom_icon:
        dimd = {'alb': 256, 'art': 256, 'pls': 256}
        for dx in (('alb', album_image_size), ('art', artist_image_size), ('pls', playlist_image_size)):
            if dx[1] in (1024, 512, 256, 128):
                dimd[dx[0]] = dx[1]
else:
    custom_icon = False
    print('Icons have been disabled because '
          + str(fileicon_path) + ' was not found\n')
    if isMain: time.sleep(3)

###############################################################
# TODO: $$$$$$$$$$$$$$$$$$$ -- FUNCTIONS -- $$$$$$$$$$$$$$$$$$$

def printRe(prntItem, prnt=True):
    '''
    When saving an item to Finder, a `/` must be
    shell-escaped as a ':', so this function
    un-shell-escapes an item so it can be printed
    as it originally appeared.
    See http://bit.ly/38FsMhK for more info.
    '''

    prntItem = re.sub(':', '/', prntItem)
    if prnt: print(prntItem)
    else: return prntItem

def osaMsg(msg, knd='n', titl='Spotify', snd='Glass'):
    '''
    Displays notifications or modal dialogs

    :param msg: the content to display
    :param knd: n: notification; d: modal dialog
    :param titl: The title
    :param snd: The sound to play if the knd is a notification
    '''

    # See https://apple.co/2N9hedH for more info about applescript notifications
    if not sys.platform.startswith('darwin'): return
    if knd == 'n':
        os.system('osascript -e \'display notification "{}" with title "{}" sound name "{}"\''
                  .format(msg, titl, snd))
    elif knd == 'd':
        os.system('osascript -e \'display dialog "{}" with title "{}"\''
                  .format(msg, titl))

def mkrmDir(mkrm, fItem):
    '''
    Makes, removes, or overwrites a directory or file

    :param mkrm:
        m: make directory
        r: remove directory
        rf: remove file
        o: make directory and delete previous directory if it exists
    :param fItem: a path to a file or folder
    '''
    if mkrm == 'm':
        if not os.path.exists(fItem):
            os.makedirs(fItem); return True
    elif mkrm == 'r':
        if os.path.exists(fItem):
            shutil.rmtree(fItem); return True
    elif mkrm == 'rf':
        if os.path.exists(fItem):
            os.remove(fItem); return True
    elif mkrm == 'o':
        if os.path.exists(fItem):
            shutil.rmtree(fItem)
        os.mkdir(fItem)

def mkApp(appDir, appName, code):
    '''
    Makes an application

    :param appDir: the parent directory of the app
    :param appName: the name of the app
    :param code: either a string consisting of a playlist uri
    or a tuple consisting of a song uri and a playlist uri
    :returns: True if the app was made and None if the app already exists
    '''
    global fullScriptPath
    appPth = os.path.join(appDir, appName) + '.app'
    if mkrmDir('m', appPth):
        os.mkdir(appPth + '/Contents')
        with open(appPth + '/Contents/PkgInfo', 'w') as fa:
            fa.write('APPL????')
        os.mkdir(appPth + '/Contents/MacOS')
        with open(appPth + '/Contents/MacOS/' + appName, 'w') as fa:
            fa.write('#!/bin/bash\n')

            if type(code) is str:
                fa.write(
'osascript -e \'tell application "Spotify" to set shuffling to true\''
' -e \'tell application "Spotify" to play track "spotify:playlist:{0}"\''
'\n\n{1} ___rnPlist___ {0}'.format(code, fullScriptPath))

            else:
                fa.write(
'osascript -e \'tell application "Spotify" to play track "spotify:track:{0}" in context "spotify:playlist:{1}"\''
'\n\n{2} ___chngPlist___ {0}'.format(code[0], code[1], fullScriptPath))

        # The shell script is given permission to execute
        os.lchmod(appPth + '/Contents/MacOS/' + appName, 0o777)
        return True

def chunkPrint(itemN, length):
    '''
    If length > 100:
        When the next set of 100 items is reached or itemN == 0,
        a range from itemN to min(itemN + 100, length of items) is printed
    :param itemN: current item
    :param length: total number of items
    '''

    if itemN % 100 == 0 and length > 100:
        itemNr = length if itemN + 100 > length else itemN + 100
        print('\n\033[95m{:>4} - {:<4}\033[0m\n'.format(itemN + 1, itemNr))

def allUserPlaylists(spUser):
    '''
    Spotify only returns 50 playlists per request,
    so multiple requests are made to the API.
    :param spUser: a Spotify username
    :returns A list of all of a user's playlists
    '''
    global sp
    spPlistResults = sp.user_playlists(spUser)
    extendedPlists = spPlistResults['items']
    while spPlistResults['next']:
        spPlistResults = sp.next(spPlistResults)
        extendedPlists.extend(spPlistResults['items'])
    return extendedPlists

def indexPlaylist(plistDict, playlist):
    '''
    Extracts information from a user's playlists

    :param plistDict: a dictionary to store info for each playlist
    :param playlist: a nested dictionary for a given playlist provided by spotipy
    :returns: the playlist uri
    '''
    tTracks = playlist['tracks']['total']
    if not tTracks: return
    plistName = playlist['name']
    plistURI = playlist['id']
    if 'images' in playlist and playlist['images']:
        plistImgDict = playlist['images']
    else: plistImgDict = None

    if plistName:
        for sysrp in ((':', ''), ('/', ':'), ('^\.+', '')):
            plistName = re.sub(sysrp[0], sysrp[1], plistName)
    if not plistName: plistName = 'Playlist'
    exactPlistName = plistName

    dPnm = 2
    while plistName in (dwp['name'] for dwp in plistDict.values()):
        plistName = exactPlistName + ' ' + str(dPnm)
        dPnm += 1

    plistDict[plistURI] = \
    {'name': plistName, 'imgs': plistImgDict,'num': tTracks}

    return plistURI

def renamePlaylistApp(oldName=None, newName=None):
    '''
    Renames a playlist app

    :param oldName: previous name
    :param newName: new name
    '''

    global plistsDir
    if not newName: newName = oldName + ' '

    os.rename(plistsDir + oldName + '.app',
              plistsDir + newName + '.app')

    os.rename(plistsDir + newName + '.app/Contents/MacOS/' + oldName,
              plistsDir + newName + '.app/Contents/MacOS/' + newName)

def updatePlaylists(savedPs, spotifyPs, isUpdate=None):
    '''
    Compares playlists from Spotify with downloaded playlists
    and renames, makes, and sets icons for them as needed

    :param savedPs: info about downloaded playlists
    :param spotifyPs: info about current playlists on Spotify
    :param isUpdate: increment an update counter
    '''

    global rmvdItems, custom_icon

    for svdpK, svdpV in savedPs.items():
        if svdpK in spotifyPs and os.path.exists(plistsDir + svdpV['name'] + '.app'):
            # Add a blank space to the end of the playlist app
            renamePlaylistApp(oldName=svdpV['name'])
        elif svdpK not in spotifyPs:
            # Remove the playlist if it is no longer in Spotify
            mkrmDir('r', plistsDir + svdpV['name'] + '.app')
            rmvdItems[1].append(svdpV['name'])

    for spPK, spPV in spotifyPs.items():
        # TODO: Rename the playlist to the new name if it exists
        if spPK in savedPs and os.path.exists(plistsDir + savedPs[spPK]['name'] + ' .app'):
            renamePlaylistApp(oldName=savedPs[spPK]['name'] + ' ', newName=spPV['name'])

        # TODO: MAKE THE APP FOR THE PLAYLIST
        else:
            # def mkApp(appDir, appName, code)
            mkApp(plistsDir, spPV['name'], spPK)

        # TODO: SET THE ICON FOR THE PLAYLIST
        # def setIcon(setf, imgDict, path, typ, isPNG=False, rmICNS=False)

        if custom_icon:
            setIcon(plistsDir + spPV['name'] + '.app',
                    spPV['imgs'], dataDir + spPK, 'pls', rmICNS=True)

            if isUpdate: isUpdate += 1
            printRe(spPV['name'])

def sysPlaylist(rePlstURI):
    '''
    Every time a playlist app is launched,
    the Spotify web API is called to check if
    it has been renamed or unfollwed by the user,
    and it is renamed or deleted as necessary.

    :param rePlstURI: the URI of the playlist
    '''

    global pickleDir, username, plistsDir, sp
    if not os.path.exists(pickleDir): return

    rPlayists = allUserPlaylists(username)

    # TODO: Index Playlists From Spotify
    rspPlists = {}
    for rPlist in rPlayists:
        # DEBUG: Stop At a given playlist
        # if rPlist['id'] == '01KRdno32jt1vmG7s5pVFg': break
        indexPlaylist(rspPlists, rPlist)

    # TODO: Retrive Pickle With Saved Playlists
    with open(pickleDir, 'rb') as rePdir:
           rsvdpickle = pickle.load(rePdir)
    rsvdPlists = rsvdpickle[3]

    # TODO: If the Playlist Name Has Changed or was Removed from SPotify
    if not rePlstURI in rspPlists or \
    rsvdPlists[rePlstURI]['name'] != rspPlists[rePlstURI]['name']:

        updatePlaylists(rsvdPlists, rspPlists)

        if rePlstURI in rspPlists:
            osaMsg('{} was renamed to {}'.format(
                printRe(rsvdPlists[rePlstURI]['name'], prnt=False),
                printRe(rspPlists[rePlstURI]['name'], prnt=False)))

        else:
            osaMsg(printRe(rsvdPlists[rePlstURI]['name'], prnt=False) +
            ' was removed because it was removed from Spotify')

        rsvdpickle[3] = rspPlists

       # TODO: Write Updated Pickle Back to Finder
        with open(pickleDir, 'wb') as rpd:
            pickle.dump(rsvdpickle, rpd, protocol=-1)

        # DEBUG: CHECK TO SEE IF PICKLE HAS BEEN UPDATED
        # with open(pickleDir, 'rb') as debug_rp:
        #     debug_rsvdPickle = pickle.load(debug_rp)
        #
        # debug_rsvdPlists = debug_rsvdPickle[3]
        #
        # for fdsa in debug_rsvdPlists:
        #     del debug_rsvdPlists[fdsa]['imgs']
        #
        # pprint.pprint(debug_rsvdPlists)

def sysSong(csongID, iscgPlst):
    '''
    If a song has been moved to a different playlist,
    then this function attempts to find the playlist
    it was moved to. If the song is no longer in any playlist,
    then it is played in the context of the album it belongs to.

    :param csongID: the URI of the song
    :param iscgPlst: TODO: ADD LATER
    '''

    global pickleDir, username, sp
    if iscgPlst:
        osaMsg('The song was moved to a different playlist.\nRetrieving new playlist...')

    if not os.path.exists(pickleDir):
        if iscgPlst:
            osaMsg('Missing Data. Run the script again to automatically update the playlist.')
        return

    with open(pickleDir, 'rb') as cprr:
           csvdpickle = pickle.load(cprr)
    csvdSongs = csvdpickle[0]
    csvdPlist = csvdSongs[csongID]['plst']
    csongApp  = os.path.join(csvdSongs[csongID]['sngDir'],
                            csvdSongs[csongID]['fndrNme']) \
               + '.app/Contents/MacOS/' + csvdSongs[csongID]['fndrNme']

    # cPlists = sp.user_playlists(username)
    # cPlistsResults = sp.user_playlists(username)
    # cPlists = cPlistsResults['items']

    cPlists = allUserPlaylists(username)

    context = None

    for cPlist in cPlists:
        print(cPlist['name'])
        if cPlist['id'] == csvdPlist: continue
        cresults = sp.playlist_tracks(cPlist['uri'])
        ctracks = cresults['items']
        while cresults['next']:
            cresults = sp.next(cresults)
        ctracks.extend(cresults['items'])
        for ctrack in ctracks:
            if ctrack['track']['id'] == csongID:
                # TODO: NEW PLAYLIST FOUND
                osaMsg('This song was moved to ' + cPlist['name'])
                context = cPlist['uri']
                break
        else: continue
        break

    csvdSongs[csongID]['plst'] = context
    plsAlb = ['___chngAlb___', '___chngPlist___']
    if not context:
        plsAlb.reverse()
        context = 'spotify:album:' + csvdSongs[csongID]['albURI']
        if iscgPlst:
            osaMsg('Song not found in any playlists.\nPlaying in context of album')

    if iscgPlst:
        os.system(
'osascript -e \'tell application "Spotify" to play track "spotify:track:{}" in context "{}"\''
                .format(csongID, context))

    with open(csongApp) as sa:
        creSongApp = re.sub('context "(.*)"', 'context "' + context + '"', sa.read())
        creSongApp = re.sub(plsAlb[0], plsAlb[1], creSongApp)

    with open (csongApp, 'w') as owa:
        owa.write(creSongApp)

    # csvdpickle[0] = csvdSongs
    with open(pickleDir, 'wb') as wp:
        pickle.dump(csvdpickle, wp, protocol=-1)

    # # DEBUG $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    # print('finished def sysSong')

def setIcon(setf, imgDict, path, typ, isPNG=False, rmICNS=False):
    '''
    Sets an icon for a directory (but also works for files)

    :param setf: the directory/file to set the icon for
    :param imgDict:
        a dictonary containing links to imgaes and their heights and widths,
        or a tuple with a link to an image and the height of the image
    :param path: The location to save the image that will be used as the icon
    :param typ:
        'alb': album image
        'art': artist image
        'pls': playlist image
        the user can set different preferred sizes for images in each category
    :param isPNG: Is the image a PNG? If not, it is assumed to be JPEG and converted to PNG
    :param rmICNS: if True: remove the ICNS file that was used to set the icon
    :returns: True if the icon was successfully applied. Else returns None
    '''

    global dimd
    # print('\n\033[91m#################### -- BEGIN def setICON() -- ####################\033[0m')
    # print('Dir to set: ' + setf)

    # If the icon has already been set,
    # then a `Icon\r` file will be inside the folder.
    if os.path.exists(setf + '/Icon\r'): return

    ICNS = path + '.icns'
    if not os.path.exists(ICNS):
        if not imgDict: return

        # DEBUG: PRINT ICON INFORMATION
        # print('Type: ' + str(typ))
        # if typ: print('Preferred Size: ' + str(dimd[typ]))
        # else: print('Preferred Size: ' + str(imgDict[1]))

        icnset = path + '.iconset/'
        mkrmDir('o', icnset)


        if type(imgDict) is tuple:
            # print('Is tuple')
            selectedImg = preferred = imgDict[1]
            PNG = icnset + 'icon_{0}x{0}.png'.format(selectedImg)
            with open(PNG, 'wb') as fi:
                fi.write(requests.get(imgDict[0]).content)
        else:
            # DEBUG: NO IMAGE SIZES
            # for dbgiD in imgDict:
            #     dbgiD['height'] = None

            preferred = dimd[typ]
            for gtn, gtsz in enumerate(imgDict):
                if not gtsz['height']:
                    # print('gtsz: ' + str(gtsz))
                    # print('^ No height ^')
                    with open(path + str(gtn) + '.jpeg', 'wb') as fi:
                        fi.write(requests.get(gtsz['url']).content)
                    gtsz['file']   = path + str(gtn) + '.jpeg'
                    gtsz['height'] = Image.open(path + str(gtn) + '.jpeg').size[0]
                    # print("gtsz['height'] = " + str(gtsz['height']))
                    # print("gtsz['file'] = " + str(gtsz['file']))


            imgDict.sort(key=lambda x: (x['height']))

            # List of sizes returned from Spotify
            bsctht = list(avsz['height'] for avsz in imgDict)
            # print('Available sizes: ' + str(bsctht))

            bsct = bisect.bisect_left(bsctht, preferred)
            if bsct == len(imgDict): bsct = -1

            selectedImg = imgDict[bsct]['height']
            if 'file' in imgDict[bsct]:
                JPG = imgDict[bsct]['file']
            else:
                with open(path + '.jpeg', 'wb') as fi:
                    fi.write(requests.get(imgDict[bsct]['url']).content)
                JPG = path + '.jpeg'

        # print('Downloaded  size: ' + str(selectedImg))

        dims = [16, 32, 128, 256, 512, 1024]

        if selectedImg < preferred:
            if selectedImg < 128:
                # print('less than 128')
                dims = [16, 32, 128]
            else:
                dims = dims[:bisect.bisect(dims, selectedImg)]
        else:
            dims = dims[:dims.index(preferred)+1]

        dims.reverse()
        dims.insert(0, dims[0])
        startICNS = True if selectedImg == dims[0] else False

        PNG = icnset + 'icon_{0}x{0}.png'.format(dims[0])

        # print('ICNS sizes: ' + str(dims))

        if not isPNG:
            os.system('sips -s format png {} -o {} >/dev/null'.format(JPG, PNG))

        for a, c in enumerate(dims[1:]):
            if a == 0 and startICNS: continue
            os.system(
                'sips -z {1} {1} {0}icon_{2}x{2}.png -o {0}icon_{1}x{1}.png >/dev/null'
                    .format(icnset, c, dims[a]))

        os.system('iconutil -c icns ' + icnset + ' -o ' + ICNS)

        shutil.rmtree(icnset)
        if not isPNG:
            mkrmDir('rf', JPG)
            for rmfi in imgDict:
                if 'file' in rmfi:
                    mkrmDir('rf', rmfi['file'])

    subprocess.run([fileicon_path, 'set', '-q', setf, ICNS])

    if rmICNS: mkrmDir('rf', ICNS)
    # print('\033[91m#################### -- END SET ICON -- ####################\033[0m\n')
    return True

def modded_auth_response(self):
    '''
    Overrides Spotipy's get_auth_response because
    of the following bug in PyCharm: When a script run from the Pycharm
    console asks for user input, if a URL is pasted, then after the user
    presses enter, the URL is re-opened in the browser intead of being
    passed back into the script. This function uses AppleScript to display
    a modal dialog in which to paste the URL.
    :param self: inherits from the SpotifyOAuth class
    '''

    print('\033[95mAuthenticating\n\033[0m')

    auth_url = self.get_authorize_url()
    try:
        import webbrowser
        webbrowser.open(auth_url)
    except: pass

    auth_prompt = """User authentication requires interaction with your
web browser. Once you enter your credentials and
give authorization, you will be redirected to
a url.  Paste the url you were directed to to
complete the authorization.

Opened the following URL in your browser:

{}""".format(auth_url)

    # TODO: Modded Code
    response = subprocess.run(
        ['osascript',
         '-e set x to display dialog "{}" default answer""'.format(auth_prompt),
         '-e set x to text returned of x'],
        capture_output=True).stdout.decode('utf-8').strip()

    if not response:
        print('Cancelled')
        sys.exit()

    return response

spotipy.SpotifyOAuth.get_auth_response = modded_auth_response

###############################################################

# TODO: Instantiate Spotify Authentication Manager
sp = spotipy.Spotify(
        auth_manager=spotipy.SpotifyOAuth
	        (client_id, client_secret, redirect_uri,
		     scope=scope, cache_path=cachePath))

###############################################################
# TODO: $$$$$$$$$$$$$$$ -- SYSTEM ARGUMENTS -- $$$$$$$$$$$$$$$$

if len(sys.argv) > 1:
    if sys.argv[1].casefold() == 'noicon' or \
    (sys.argv[1].casefold() == 'no' and sys.argv[2].casefold() == 'icon'):
        print('\n\033[95mIcons Have Been Disabled\033[0m\n')
        custom_icon = False
        if isMain: time.sleep(2)

    elif sys.argv[1] in ('___chngPlist___', '___chngAlb___'):
        if sys.argv[1] == '___chngPlist___' and \
        os.system('osascript -e \'tell application "Spotify" to get id of current track\'') != 0:
            sysSong(sys.argv[2], True)

        elif sys.argv[1] == '___chngAlb___':
            sysSong(sys.argv[2], False)

        sys.exit()

    elif sys.argv[1] == '___rnPlist___':
        sysPlaylist(sys.argv[2])
        sys.exit()

    else:
        print('\nThis script only accepts one argument: \033[95mnoicon\033[0m'
        '\nOtherwise, icons will be added\n')
        if isMain: time.sleep(3)

# TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO$$$$$$$$$$$$$$$$ -- BEGIN MAIN SCRIPT  -- $$$$$$$$$$$$$$$$$$$$$$
# TODO$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# TODO: Retrieve Saved Pickle Data
if os.path.exists(pickleDir):
    # Retrieve the Pickle containing data about tracks and playlists
    # that were previously donwloaded.
    with open(pickleDir, 'rb') as rpk:
        svdpickle = pickle.load(rpk)
    # svd = saved; sp = from Spotify
    svdSongs  = svdpickle[0]
    svdAlbums = svdpickle[1]
    svdArtsts = svdpickle[2]
    svdPlists = svdpickle[3]
else:
    svdSongs, svdPlists, svdAlbums, svdArtsts  = {}, {}, {}, {}


for f in (folder_location, plistsDir, dataDir, artImgDir, albImgDir):
    mkrmDir('m', f)

if custom_icon:
    setIcon(folder_location,
            ('https://i.ibb.co/89MbxQv/Spotify-Folder-Square.png', 1024),
            dataDir + 'folderIcon', None, isPNG=True)

spPlaylists = allUserPlaylists(username)

print('\033[95m################### -- Retrieving Playlist Tracks -- ###################\n\033[0m')


# TODO: $$$$$$$$ -- INDEX PLAYLISTS -- $$$$$$$$
for spPlaylist in spPlaylists:

    # DEBUG: Stop at a given playlist
    # if spPlaylist['id'] == '01KRdno32jt1vmG7s5pVFg': break

    plistID = indexPlaylist(spPlists, spPlaylist)
    if not plistID: continue

    ###############################################################
    # TODO: $$$$$$$$$$$$$$$$ -- RETRIEVE TRACKS -- $$$$$$$$$$$$$$$$

    results = sp.playlist_tracks(plistID)
    
    tracks  = results['items']
    tgmr = '' if spPlists[plistID]['num'] == 1 else 's'
    printRe('\033[95m' + spPlists[plistID]['name'] + ' - '
          + str(spPlists[plistID]['num']) + ' track' + tgmr + '\033[0m')

    ptn = 101

    if results['next']: print('     1 - 100')

    # Spotify only returns 100 tracks per request.
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])
        # TODO: PRINT TRACK NUMBERS
        print('  {:>4} - {:<4}'.format(ptn, len(results['items']) + ptn - 1))
        ptn += 100
    print()

    # TODO: $$$$$$$$$$$$$$$$ -- INDEX TRACKS -- $$$$$$$$$$$$$$$$

    spPlists[plistID]['uniqeTrcks'] = 0

    for trckN, track in enumerate(tracks):
        if track['is_local']: continue
        songURI    = track['track']['id']
        if songURI in spSongs: continue
        songName   = track['track']['name']
        albumName  = track['track']['album']['name']
        artistName = track['track']['artists'][0]['name']
        albumURI   = track['track']['album']['id']
        artistURI  = track['track']['artists'][0]['id']

        # The number of tracks unqique to the given playlist
        spPlists[plistID]['uniqeTrcks'] += 1

        # macOS does not allow files/folders to include a colon, so they are removed.
        # Files/folders that start with a period get marked as hidden,
        # so leading periods are removed.
        # A shell-escaped `/` becomes a colon, so `/`s are replaced with colons.
        # For example, if you cd to your desktop and then run `mkdir Some:Folder`,
        # The name of the folder will be `Some/Folder`.
        # See http://bit.ly/38FsMhK for more info.
        for r in ((':', ''), ('/', ':'), ('^\.+', '')):
            if songName:   songName   = re.sub(r[0], r[1], songName)
            if albumName:  albumName  = re.sub(r[0], r[1], albumName)
            if artistName: artistName = re.sub(r[0], r[1], artistName)

        # # DEBUG: NO SONG NAME For LIL WINDEX $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        # if artistURI == '4h76IrYDJITkZC1K9GAVfR':
        #     songName = ''

        ################################################################
        # finderName = The name that the song will be saved as in Finder

        if not albumName: albumName = 'Unknown Album'

        if songName: isSong = True
        else: isSong = False; songName = 'Song'

        if artistName:
            isArt = True
            finderName = songName + ' - ' + artistName
        else:
            isArt = False
            finderName = songName
            artistName = 'Unknown Artist'

        # If the song name is blank after being ran through the regexs
        if not isSong:
            # If the song has already been downloaded, then it already has a name
            # and that should be used.
            if songURI in svdSongs:
                finderName = svdSongs[songURI]['fndrNme']
                dirAlbum   = svdSongs[songURI]['sngDir']
                # print('blank song in saved songs:')
                # print(svdSongs[songURI]['fndrNme'] + ' = ' + songURI); print()
            else:
                blnkN = 1
                # spSongs or svdSongs may be empty; so they must be checked to see if they are emtpty
                # to avoid keyerrors when attempting to access nested elements inside them
                while (spSongs and finderName in (alSng['fndrNme'] for alSng in spSongs.values())) \
                or (svdSongs and finderName in (alSvng['fndrNme'] for alSvng in svdSongs.values())):

                    finderName = 'Song ' + str(blnkN)
                    if isArt: finderName += ' - ' + artistName
                    blnkN += 1

        ################################################################
        # TODO $$$$$$$$$$$$$$ -- Artist and Album Data -- $$$$$$$$$$$$$$

        dirArtist = os.path.join(folder_location, artistName)
        mkrmDir('m', dirArtist)

        if artistURI and not artistURI in spArtists:
            artistImgDict = None
            if custom_icon:
                artistInfo = sp.artist(artistURI)
                if 'images' in artistInfo and artistInfo['images']:
                    artistImgDict = artistInfo['images']

            spArtists[artistURI] = \
        {'name': artistName, 'dir': dirArtist, 'imgs': artistImgDict}


        dirAlbum = os.path.join(dirArtist, albumName)
        mkrmDir('m', dirAlbum)

        if albumURI and not albumURI in spAlbums:
            albumImgDict = None
            if custom_icon:
                isAlbImg = track['track']['album']

                # # DEBUG: Missing Album Image
                # isAlbImg = []

                if 'images' in isAlbImg and isAlbImg['images']:
                    albumImgDict = isAlbImg['images']

            spAlbums[albumURI] = \
        {'name': albumName, 'dir': dirAlbum, 'imgs': albumImgDict, 'artURI': artistURI}

        ################################################################
        # TODO: $$$$$$$$$$$$$$$ -- APPEND TRACK DATA -- $$$$$$$$$$$$$$$$

        spSongs[songURI] = \
        {'fndrNme': finderName, 'sngDir': dirAlbum,
          'albURI': albumURI,   'artURI': artistURI, 'plst': plistID}

        ################################################################

################################################################

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$ -- RENAME OR DELETE SAVED ITEMS -- $$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


# TODO: DELETE SAVED ITEMS NO LONGER ON SPOTIFY
for sngK, sngV in svdSongs.items():
    # If a saved song is no longer in any Spotify playlist
    if not sngK in spSongs:
        rmvdItems[0].append(sngV['fndrNme'])
        # Delete the song itself
        mkrmDir('r', os.path.join(sngV['sngDir'], sngV['fndrNme']) + '.app')

        rmAlb = sngV['albURI']
        if rmAlb and not rmAlb in spAlbums:
            # Delete the album image
            mkrmDir('rf', albImgDir + rmAlb + '.icns')
            # Delete the album folder
            if svdAlbums:
                mkrmDir('r', svdAlbums[rmAlb]['dir'])


        rmArt = sngV['artURI']
        if rmArt and not rmArt in spArtists:
            # Delete the artist image
            mkrmDir('rf', artImgDir + rmArt + '.icns')
            # Delete the artist folder
            if svdArtsts:
                mkrmDir('r', svdArtsts[rmArt]['dir'])


    # TODO: If the song was moved to a different playlist, then update the app
    elif sngV['plst'] != spSongs[sngK]['plst']:
        swtchPlist = os.path.join(sngV['sngDir'], sngV['fndrNme']) \
                     + '.app/Contents/MacOS/' + sngV['fndrNme']

        if os.path.exists(swtchPlist):
            with open(swtchPlist) as rpf:
                newPlist = re.sub('context "(.*)"',
                    'context "spotify:playlist:' + spSongs[sngK]['plst'] + '"', rpf.read())

            with open(swtchPlist, 'w') as owf:
                owf.write(newPlist)

if spPlists:
    mkPlMsg = 'Downloading Playlists'
    if custom_icon: mkPlMsg += ' and Setting Icons'
    print('\033[95m################### -- ' + mkPlMsg + ' -- ###################\033[0m\n')

# TODO: RENAME, DELETE, OR MAKE PLAYLISTS
updatePlaylists(svdPlists, spPlists, isUpdate=updCnt)

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$ -- MAKE APPS AND SET ICONS -- $$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

if spSongs:
    mkSngMsg = 'Downloading Songs'
    if custom_icon: mkSngMsg += ' and Setting Icons'
    print('\n\033[95m################### -- ' + mkSngMsg + ' -- ###################\033[0m')
else:
    print("You Don't have any songs on Spotify!")

plst, sngN = None, 0
for songK, songV in spSongs.items():
    if songV['plst'] != plst:  # Then a new playlist has been reached
        sngN = 0
        plst = songV['plst']
        ggrmr = '' if spPlists[plst]['num'] == 1 else 's'

        printRe('\n\033[95m{} - {} unique track{}\033[0m'
              .format(spPlists[plst]['name'], str(spPlists[plst]['uniqeTrcks']), ggrmr))

        if spPlists[plst]['uniqeTrcks'] <= 100: print()

    chunkPrint(sngN, spPlists[plst]['uniqeTrcks'])
    sngN += 1

    ################################################################

    # Only print the song name and increment the update count once
    isPrntSng = False

    # TODO: MAKE THE APP FOR THE SONG
    if mkApp(songV['sngDir'], songV['fndrNme'], (songK, plst)):
        printRe(songV['fndrNme'])
        updCnt += 1; isPrntSng = True


    # TODO: SET THE ICON FOR THE SONG
    songPath = os.path.join(songV['sngDir'], songV['fndrNme']) + '.app'
    # If the icon has not already been set
    if custom_icon and not os.path.exists(songPath + '/Icon\r'):
        isSngIconSet = False
        sngAlbURI = songV['albURI']
        sngArtURI = songV['artURI']

        # Try to use the album image to set the icon for the song
        if sngAlbURI:
            isSngIconSet = setIcon(
                songPath, spAlbums[sngAlbURI]['imgs'], albImgDir + sngAlbURI, 'alb')
          # setIcon(dir to set, imgs, path to save imgs, type)

        # Elif try to use the artist image to set the icon for the song
        if not isSngIconSet and sngArtURI:
            isSngIconSet = setIcon(
                songPath, spArtists[sngArtURI]['imgs'], artImgDir + sngArtURI, 'art')

        if isSngIconSet and not isPrntSng:
            printRe(songV['fndrNme'])
            updCnt += 1


################################################################

if custom_icon:

    # TODO: SET ARTIST ICONS
    if spArtists:
        artLen = len(spArtists)
        print('\n\033[95mApplying Artist Icons ({})\033[0m'.format(artLen))
        if artLen <= 100: print()

        for n, (artK, artV) in enumerate(spArtists.items()):

            chunkPrint(n, artLen)

            if setIcon(artV['dir'], artV['imgs'], artImgDir + artK, 'art'):
                printRe(artV['name'])
                updCnt += 1


    # TODO: SET ALBUM ICONS
    if spAlbums:
        albLen = len(spAlbums)
        print('\n\033[95mApplying Album Icons ({})\033[0m'.format(albLen))
        if albLen <= 100: print()

        for n, (albK, albV) in enumerate(spAlbums.items()):

            chunkPrint(n, albLen)

            if os.path.exists(albV['dir'] + '/Icon\r'): continue

            setAlbPath = None

            if os.path.exists(albImgDir + albK + '.icns'):
                setAlbPath  = albImgDir + albK

            elif os.path.exists(artImgDir + albV['artURI'] + '.icns'):
                setAlbPath    = artImgDir + albV['artURI']

            if setAlbPath:
                if setIcon(albV['dir'], None, setAlbPath, None):
                        printRe(albV['name'])
                        updCnt += 1

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$ -- END MAIN SCRIPT  -- $$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# TODO: SAVE PICKLE TO FILE
with open(pickleDir, 'wb') as pd:
    pickle.dump([spSongs, spAlbums, spArtists, spPlists], pd, protocol=-1)

# TODO: PRINT REMOVED ITEMS
# rmvdItems = ([removed songs], [removed playlists])
if rmvdItems[0] or rmvdItems[1]:
    rmvdiLen = len(rmvdItems[0] + rmvdItems[1])
    gRmS = ' Item Was' if rmvdiLen == 1 else ' Items Were'
    print('\n\033[91m################### -- {}{} Removed -- ###################\033[0m'
          .format(str(rmvdiLen), gRmS))

    if rmvdItems[0]:
        rmpg = ' Was' if len(rmvdItems[0]) == 1 else 's Were'
        # print('\n\033[95m' + str(len(rmvdItems[0])) + ' Song' + rmpg + ' Removed\033[0m\n')
        print('\n\033[95m{} Song{} Removed\033[0m\n'
            .format(str(len(rmvdItems[0])), rmpg))

        for rmvdSong in rmvdItems[0]:
            printRe(rmvdSong)

    if rmvdItems[1]:
        rmsg = ' Was' if len(rmvdItems[1]) == 1 else 's Were'
        # print('\n\033[95m' + str(len(rmvdItems[1])) + ' Playlist' + rmsg + ' Removed\033[0m\n')
        print('\n\033[95m{} Playlist{} Removed\033[0m\n'
            .format(str(len(rmvdItems[1])), rmsg))
        for rmvdPlist in rmvdItems[1]:
            printRe(rmvdPlist)

def formatTime(s):
    '''
    Takes a number of seconds as input (int or float)
    and returns a length of time in human-readable format with correct grammar.
    '''

    if s == 0: return 'less than one second'
    tList = []

    hours = s // 3600
    if hours != 0:
        strhours = '1 Hour' if hours == 1 else str(hours) + ' hours'
        tList.append(strhours)

    s = s - hours * 3600
    minutes = s // 60
    if minutes != 0:
        strminutes = '1 Minute' if minutes == 1 else str(minutes) + ' minutes'
        tList.append(strminutes)

    s = s - minutes * 60
    if s != 0:
        strseconds = '1 Second' if s == 1 else str(s) + ' seconds'
        tList.append(strseconds)

    if len(tList) == 1: return tList[0]
    if len(tList) == 2: return tList[0] + ' and ' + tList[1]
    return tList[0] + ', ' + tList[1] + ', and ' + tList[2]

if updCnt:
    elapsed  = int(time.time()) - TimeStamp
    elapsedH = formatTime(elapsed)
    perItem  = formatTime(round(elapsed/updCnt, 2))
    fGrmr    = '' if updCnt == 1 else 's'
    finalMsg = 'It took {} to Update {} Item{}'.format(elapsedH, str(updCnt), fGrmr)
    print('\033[95m\n#----------------------------------------------------------------#\033[0m')
    print(finalMsg)
    if updCnt > 1: print(perItem.capitalize() + ' per Item\033[0m\n')

    osaMsg(finalMsg, titl='Indexing Finished')
else:
    print('\n\033[91mNo New Songs or Icons to Apply\n\033[0m')
    osaMsg('No New Songs or Icons to Apply')
