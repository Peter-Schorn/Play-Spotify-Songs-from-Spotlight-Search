# -*- coding: utf-8 -*-
import os, shutil, re, subprocess, requests, pickle, \
    spotipy, time, sys, bisect, glob
from pathlib import Path
from PIL import Image
from pkg_resources import get_distribution
from typing import *

scope = (
    'user-library-read '
    'playlist-read-private '
    'user-modify-playback-state '
    'user-read-playback-state'
)

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

# TODO: $$$$$$$$$$$$$$$$$$$$$ -- SETUP -- $$$$$$$$$$$$$$$$$$$$$

print()

# TODO: Check that the Spotipy version is >= 2.10.0
expectedVersion = '2.10.0'
spotipyVersion = get_distribution('spotipy').version
for ic, ie in zip(spotipyVersion.split('.'), expectedVersion.split('.')):
    if int(ic) < int(ie):
        print(
            'The version of the Spotipy module you have is {}\n'
            'You need {} or greater for this script to work.\n'
            'If you have pip, you can upgrade spotipy by running\n\n'
            '\033[95mpip install spotipy --upgrade\033[0m\n\n'
                .format(spotipyVersion, expectedVersion)
        )
        sys.exit()
    if int(ic) > int(ie): break

if len(sys.argv) > 1 and sys.argv[1] in \
        ('___chngPlist___', '___rnPlist___'):
    isMain = False
else:
    isMain = True

# TODO: Retrieve client id and client secret
if os.path.exists(credentials):
    with open(credentials) as crdnts:
        rdcrednts = crdnts.read()
        client_id = re.search(r'client[\W_]*id[\W]*([a-zA-Z0-9]+)', rdcrednts)
        if client_id:
            client_id = client_id.group(1).strip()
        else:
            print("Couldn't find client id")
        client_secret = re.search(r'client[\W_]*secret[\W]*([a-zA-Z0-9]+)', rdcrednts)
        if client_secret:
            client_secret = client_secret.group(1).strip()
        else:
            print("Couldn't find client secret")
    if not client_id or not client_secret: print(); sys.exit()
else:
    print(
        'The file where your client id and client secrets are stored could not be found:'
        f'\n{credentials}\n'
    )
    sys.exit()

# TODO: Constants
redirect_url = 'http://localhost/'
updateCount = 0
fullScriptPath = f'{sys.executable} "{sys.argv[0]}"'
rmvdItems = {'Artist': [], 'Album': [], 'Song': [], 'Playlist': []}
dataDir = os.path.join(folder_location, '.Data/')
pickleDir = os.path.join(dataDir, 'Pickle')
plistsDir = os.path.join(folder_location, 'Playlists/')
artImgDir = os.path.join(dataDir, 'Artists/')
albImgDir = os.path.join(dataDir, 'Albums/')


################################################################

# TODO: $$$$$$$$$$$$$$$$$$$ -- FUNCTIONS -- $$$$$$$$$$$$$$$$$$$$

def rePrint(prntItem: str, prnt=True):
    """
    When saving an item to Finder, a `/` must be
    shell-escaped as a ':', so this function
    un-shell-escapes an item so it can be printed
    as it originally appeared.
    See http://bit.ly/38FsMhK for more info.
    """

    prntItem = re.sub(':', '/', prntItem)
    if not prnt: return prntItem
    print(prntItem)


def osaMsg(msg: str, knd='n', titl='Spotify', snd='Glass'):
    """
    Displays notifications or modal dialogs

    :param msg: the content to display
    :param knd: n: notification; d: modal dialog
    :param titl: The title
    :param snd: The sound to play if the knd is a notification
    """

    # See https://apple.co/2N9hedH for more info about applescript notifications
    if not sys.platform.startswith('darwin'): return
    if knd == 'n':
        os.system(
            'osascript -e \'display notification "{}" with title "{}" sound name "{}"\''
                .format(msg, titl, snd)
        )
    elif knd == 'd':
        os.system(
            'osascript -e \'display dialog "{}" with title "{}"\''
                .format(msg, titl)
        )


def mkrmDir(mkrm: str, fItem: str or tuple):
    """
    Makes, removes, or overwrites a directory or file

    :param mkrm:
        mkDir: make directory
        rmDir: remove directory
        rmFile: remove file
        owrDir: make directory and delete previous directory if it exists
    :param fItem:
        a file/folder path
        or a tuple with partial file paths, which will be joined.
    """

    if type(fItem) is tuple: fItem = os.path.join(*fItem)

    # Make a directory
    if mkrm == 'mkDir':
        if not os.path.exists(fItem):
            os.makedirs(fItem);
            return True
    # Remove a directory
    elif mkrm == 'rmDir':
        if os.path.exists(fItem):
            shutil.rmtree(fItem);
            return True
    # Remove a file
    elif mkrm == 'rmFile':
        if os.path.exists(fItem):
            os.remove(fItem);
            return True
    # Make folder and replace it if it already exists
    elif mkrm == 'owrDir':
        if os.path.exists(fItem):
            shutil.rmtree(fItem)
        os.mkdir(fItem)


def mkApp(parentDir=None, appName=None, code=None):
    """
    Makes an application

    :param parentDir: the parent directory of the app
    :param appName: the name of the app
    :param code:
        either a string consisting of a playlist id - used to make playlist app
        or a tuple consisting of
        (song id, playlist/album id to play song in context of, albumId, artistId)
        - used to make song app
    :returns True if the app was made and None if the app already exists
    """

    global fullScriptPath  # the path to THIS python script
    if type(parentDir) is tuple:
        parentDir = os.path.join(*parentDir)

    appPth = os.path.join(parentDir, appName) + '.app'
    if mkrmDir('mkDir', appPth):
        os.mkdir(appPth + '/Contents')
        with open(appPth + '/Contents/PkgInfo', 'w') as fa:
            fa.write('APPL????')
        os.mkdir(appPth + '/Contents/MacOS')
        with open(appPth + '/Contents/MacOS/' + appName, 'w') as fa:
            fa.write('#!/bin/bash\n')

            if type(code) is str:  # makes playlist app: code = playlist id
                fa.write(
                    'osascript -e \'tell application "Spotify" to set shuffling to true\' '
                    '-e \'tell application "Spotify" to play track "spotify:playlist:{0}"\''
                    '\n\n{1} ___rnPlist___ {0}'.format(code, fullScriptPath))

            else:  # makes song app: code = (song id, context, album id, artist id)
                fa.write(
                    'osascript -e \'tell application "Spotify" to play '
                    'track "spotify:track:{0}" in context "spotify:{1}"\''
                    '\n\n{4} ___chngPlist___ {0} {2} {3}'
                        .format(code[0], code[1], code[2], code[3], fullScriptPath))
            # song id, context, album id, artist id

        # The shell script is given permission to execute
        os.lchmod(f'{appPth}/Contents/MacOS/{appName}', 0o777)
        return True


def chngSongContext(parentDir: str or tuple = None, appName: str = None, context: str = None):
    """
    Changes the context that a song is played in
    :param parentDir: the file path to the song
    :param appName: the name of the app
    :param context: the new context to play the song in
    """

    if type(parentDir) is tuple: parentDir = os.path.join(*parentDir)
    binaryPath = f'{os.path.join(parentDir, appName)}.app/Contents/MacOS/{appName}'

    if not os.path.exists(binaryPath):
        # print(f"chngSongContext: path doesn't exist: {binaryPath}")
        return

    with open(binaryPath) as find:
        chngContext = re.sub(
            '" in context "spotify:(.*)"',
            f'" in context "spotify:{context}"',
            find.read())

    with open(binaryPath, 'w') as repl:
        repl.write(chngContext)


def spExtend(spResults, pagePrint=True):
    """
    The Spotify web API sometimes returns paginated results
    This function makes multiple requests to the API until all pages
    are returned
    :param spResults: The Spotify endpoint to retrieve results from
    :param pagePrint: Truthy = print the current page. Else don't print anything
    :returns: all pages of the reults in one list
    """

    global sp
    extendedResults = spResults['items']
    limitt = spResults['limit']

    if spResults['next']:
        if pagePrint:
            # print(f' 1 - {limitt}')
            print('\t{:>4} - {:<4}'.format(1, limitt))
            num = limitt + 1
        while spResults['next']:
            spResults = sp.next(spResults)
            extendedResults.extend(spResults['items'])
            if pagePrint:
                print('\t{:>4} - {:<4}'.format(
                    num, len(spResults['items']) + num - 1))
                num += limitt

    if pagePrint:
        print()
    return extendedResults


def renamePlaylistApp(oldName: str = None, newName: str = None):
    """Renames a playlist app"""

    global plistsDir

    if not newName:
        newName = oldName + ' '

    os.rename(
        plistsDir + oldName + '.app',
        plistsDir + newName + '.app'
    )

    os.rename(
        plistsDir + newName + '.app/Contents/MacOS/' + oldName,
        plistsDir + newName + '.app/Contents/MacOS/' + newName
    )


def sysPlaylist(sysPlstId: str):
    """
    Every time a playlist app is launched,
    the Spotify web API is called to check if
    it has been renamed or unfollwed by the user,
    and it is renamed or deleted as necessary.

    :param sysPlstId: the Id of the playlist
    """
    global username, sp, plistsDir

    # print(f'sysplaylist called with [{sysPlstId}]')

    # TODO: Retrieve saved playlist info
    rsvdLibrary = SpotifyLibrary.fromPickle()
    if not rsvdLibrary: return

    rspLibrary = SpotifyLibrary(pickleLibrary=rsvdLibrary)

    # TODO: Index playlists from Spotify
    rawPlaylists = spExtend(sp.user_playlists(username))
    for rawPlst in rawPlaylists:
        rspLibrary.addPlaylist(rawPlst)

    if not sysPlstId in rspLibrary.playlists or \
            rsvdLibrary.playlists[sysPlstId]['name'] != rspLibrary.playlists[sysPlstId]['name']:
        rspLibrary.updatePlaylists()

        if sysPlstId in rspLibrary.playlists:
            osaMsg(
                '{} was renamed to {}'.format(
                    rePrint(rsvdLibrary.playlists[sysPlstId]['name'], prnt=False),
                    rePrint(rspLibrary.playlists[sysPlstId]['name'], prnt=False)
                )
            )
        else:
            osaMsg(
                rePrint(rsvdLibrary.playlists[sysPlstId]['name'], prnt=False) +
                ' was removed because it was unfollowed'
            )

        # TODO: Saved updated pickle back to file
        rspLibrary.dump()

    if rspLibrary.playlists[sysPlstId]['num'] == 0:
        osaMsg('There are no tracks in this playlist')


def sysSong(csongId, sysAlbId, sysArtId):
    """
    If a song has been moved to a different playlist,
    then this function attempts to find the playlist
    it was moved to. If the song is no longer in any playlist,
    then it is played in the context of the album it belongs to.

    :param csongId: the id of the song
    :param sysAlbId: the album id of the song
    :param sysArtId: the artist id of the song
    """

    global username, sp

    osaMsg('The song was moved to a different playlist.\nRetrieving new playlist...')

    sysLibrary = SpotifyLibrary.fromPickle()
    if not sysLibrary:
        time.sleep(2)
        osaMsg('Missing Data. Try running the script again.')
        return

    sysSongDict = sysLibrary.library[sysArtId]['albums'][sysAlbId]['tracks'][csongId]
    prevContext = sysSongDict['context'].split(':')[1]
    snapshotForOld = sysLibrary.playlists.get(prevContext, {}).get('snapshot')
    snapshotForNew = None

    cPlaylists = spExtend(sp.user_playlists(username))
    for cPlist in cPlaylists:
        cPlsId = cPlist['id']
        cPlsSnap = cPlist['snapshot_id']

        if cPlsId == prevContext:
            snapshotForOld = cPlsSnap
            print('snapshot for old:', cPlsSnap)
            continue

        if cPlsSnap == sysLibrary.playlists.get(cPlsId, {}).get('snapshot'):
            print('snaps hots same; continuing')
            continue

        cPlsName = cPlist['name']
        print(cPlsName)
        cTracks = spExtend(sp.playlist_tracks(cPlsId))
        for cTrack in (cTrckk['track'] for cTrckk in cTracks):
            if cTrack['id'] == csongId:
                # TODO: NEW PLAYLIST FOUND
                osaMsg(f'{cTrack["name"]} was moved to {cPlsName}')
                nwContextId = cPlsId
                nwContext = f'playlist:{cPlsId}'
                snapshotForNew = cPlsSnap
                break
        else:
            continue
        break
    else:  # if the song was not found in any playlists
        nwContext = f'album:{sysAlbId}'
        osaMsg('Song not found in any playlists.\n'
               'Playing in context of album.')

    os.system(
        'osascript -e \'tell application "Spotify" to play '
        'track "spotify:track:{}" in context "spotify:{}"\''
            .format(csongId, nwContext)
    )

    # TODO: edit song app
    chngSongContext(
        parentDir=sysSongDict['sngDir'],
        appName=sysSongDict['fndrNme'],
        context=nwContext
    )
    # TODO: Update context and snapshots of retrieved pickle and save back to file
    sysSongDict['context'] = nwContext
    if snapshotForNew:
        sysLibrary.playlists[nwContextId]['snapshot'] = snapshotForNew
    if snapshotForOld:
        sysLibrary.playlists[prevContext]['snapshot'] = snapshotForOld

    # DEBUG: saving context in pickle $$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    # osaMsg(
    #     'saving context in pickle:' + '\n' +
    #     sysLibrary.library[sysArtId]['albums'][sysAlbId]['tracks'][csongId]['context']
    # )

    sysLibrary.dump()


def sysQueue(songPath):
    """
    Adds a song to a user's queue

    :param songPath: the path to a song app
    """

    global sp
    appContents = f'{songPath}/Contents/MacOS/'
    fullPath = glob.glob(f'{appContents}*')[0]
    with open(fullPath) as sngQ:
        uri = re.search(
            '''osascript -e 'tell application "Spotify" to play track "(.*?)" in context "''',
            sngQ.read()
        )
    if uri:
        uri = uri.group(1)
        devices = sp.devices().get('devices')
        if devices:
            deviceId = devices[0]['id']
            sp.add_to_queue(uri, device_id=deviceId)

            # Get song name
            qsongName = re.search(f'{appContents}(.*)', fullPath).group(1)
            osaMsg(f'Added to queue: {qsongName}')

        else:
            osaMsg('No devices found')
    else:
        raise Exception


def setIcon(folder, imgDict=None, imgPath=None, typ=None, isPNG=False):
    """
    Sets an icon for a directory

    :param folder: the directory/file to set the icon for
    :param imgDict:
        a dictonary containing links to imgaes and their heights and widths,
        or a tuple with a link to an image and the height/width of the image,
        which must be a square or it will be distorted into a square.
    :param imgPath: The location to save the image that will be used as the icon
    :param typ:
        'alb': album image
        'art': artist image
        'pls': playlist image
        the user can set different preferred sizes for images in each category
    :param isPNG: Is the image a PNG? If not, it is assumed to be JPEG and converted to PNG
    :returns:
        True if the icon was applied
        Else returns None—the icon may have already been applied or data was missing.
    """

    global dimd, resetPlistImgs, fileIconExists

    if type(folder) is tuple: folder = os.path.join(*folder)
    if type(imgPath) is tuple: imgPath = os.path.join(*imgPath)

    # If the icon has already been set, then a `Icon\r` file will be inside the folder.
    if os.path.exists(folder + '/Icon\r') and not \
            (resetPlistImgs and typ == 'pls' and fileIconExists):
        return

    ICNS = imgPath + '.icns'
    if not os.path.exists(ICNS):
        if not imgDict: return

        # print('\n\033[91m#################### -- BEGIN setICON() -- ####################\033[0m')
        # print(f'Dir to set: {folder}')
        # print(f'Type: {typ}')
        # if typ: print(f'Preferred Size: {dimd[typ]}')
        # else: print(f'Preferred Size: {imgDict[1]}')

        icnset = imgPath + '.iconset/'
        mkrmDir('owrDir', icnset)

        if isPNG:
            # print('Is tuple')
            selectedImg = preferred = imgDict[1]
            JPG = None
            PNG = icnset + 'icon_{0}x{0}.png'.format(selectedImg)
            with open(PNG, 'wb') as fi:
                fi.write(requests.get(imgDict[0]).content)
        else:
            # DEBUG: NO IMAGE SIZES
            # for dbgiD in imgDict:
            #     dbgiD['height'] = None

            preferred = dimd[typ]
            for gtn, gtsz in enumerate(imgDict):
                if not gtsz['width'] or not gtsz['height']:
                    # print('gtsz: ' + str(gtsz))
                    # print('^ No height ^')
                    with open(f'{imgPath}{gtn}.jpeg', 'wb') as fi:
                        fi.write(requests.get(gtsz['url']).content)
                    gtsz['file'] = imgPath + str(gtn) + '.jpeg'
                    gtsz['width'], gtsz['height'] = Image.open(f'{imgPath}{gtn}.jpeg').size
                    # print("gtsz['height'] = " + str(gtsz['height']), end='; ')
                    # print("gtsz['width'] = " + str(gtsz['width']))
                    # print("gtsz['file'] = " + str(gtsz['file']))

            imgDict.sort(key=lambda x: min(x['width'], x['height']))

            # List of sizes returned from Spotify
            bsctht = list(min(avsz['width'], avsz['height']) for avsz in imgDict)
            # print(f'Available sizes: {bsctht}')

            bsct = bisect.bisect_left(bsctht, preferred)
            if bsct == len(imgDict): bsct = -1

            selectedImg = max(imgDict[bsct]['height'], imgDict[bsct]['width'])
            if 'file' in imgDict[bsct]:
                JPG = imgDict[bsct]['file']
            else:
                with open(imgPath + '.jpeg', 'wb') as fi:
                    fi.write(requests.get(imgDict[bsct]['url']).content)
                JPG = imgDict[bsct]['file'] = imgPath + '.jpeg'

        # print('size of choosen image:', selectedImg)

        dims = [16, 32, 128, 256, 512, 1024]
        del dims[dims.index(preferred) + 1:]

        if selectedImg < 128:
            # print('less than 128')
            dims = dims[:3]
        else:
            dims = dims[:bisect.bisect_left(dims, selectedImg) + 1]

        dims.reverse()

        if not isPNG and max(imgDict[bsct]['width'], imgDict[bsct]['height']) != dims[0]:
            dims.insert(0, dims[0])
        # else:
        # print('######## -- IMAGE ALREADY IN ICNS SIZE -- ########')

        PNG = icnset + 'icon_{0}x{0}.png'.format(dims[0])

        if not isPNG:
            os.system('sips -s format png {} -o {} >/dev/null'.format(JPG, PNG))

        # TODO: Pad non-square images with transparent borders to make them square.
        # the fileicon utility will distort non-square icons to make them square
        if not isPNG:
            width, height = imgDict[bsct]['width'], imgDict[bsct]['height']
            if width != height:
                # print('width != height: ', end='')
                pil_img = Image.open(PNG)

                if width > height:
                    sqrImg = Image.new('RGBA', (width, width))
                    sqrImg.paste(pil_img, (0, (width - height) // 2))
                elif width < height:
                    sqrImg = Image.new('RGBA', (height, height))
                    sqrImg.paste(pil_img, ((height - width) // 2, 0))

                sqrImg.save(PNG)

                # # DEBUG: Print resized image dimensions
                # print(width, height)
                # print('new dimensions: ', end='')
                # debug_width, debug_height = Image.open(PNG).size
                # print(debug_width, debug_height)

        # print(f'ICNS sizes: {dims}')

        for a, c in enumerate(dims[1:]):
            os.system(
                'sips -z {1} {1} {0}icon_{2}x{2}.png -o {0}icon_{1}x{1}.png >/dev/null'
                    .format(icnset, c, dims[a]))

        os.system(f'iconutil -c icns {icnset} -o {ICNS}')

        # TODO: remove Iconset and jpeg files
        shutil.rmtree(icnset)
        if not isPNG:
            mkrmDir('rmFile', JPG)
            for rmfi in imgDict:
                if 'file' in rmfi:
                    mkrmDir('rmFile', rmfi['file'])

    # TODO: Set the Icon
    subprocess.run([fileicon_path, 'set', '-q', folder, ICNS])

    if typ == 'pls': mkrmDir('rmFile', ICNS)
    # print('\033[91m#################### -- END setICON() -- ####################\033[0m\n')
    return True


def modded_auth_response(self):
    """
    Overrides Spotipy's get_auth_response because
    of the following bug in PyCharm: When a script run from the Pycharm
    console asks for user input, if a URL is pasted, then after the user
    presses enter, the URL is re-opened in the browser intead of being
    passed back into the script. This function uses AppleScript to display
    a dialog box in which to paste the URL.

    :param self: inherits from the SpotifyOAuth class
    """

    print('\n\033[95mAuthenticating\n\033[0m')

    auth_url = self.get_authorize_url()

    try:
        import webbrowser
        webbrowser.open(auth_url)
    except:
        pass

    auth_prompt = (
        'User authentication requires interaction with your web browser. '
        'Once you enter your credentials and give authorization, '
        'you will be redirected to a url. '
        'Paste the url you were directed to to complete the authorization.\n\n'

        'Opened the following URL in your browser:\n\n'

        f'{auth_url}'
    )

    response = subprocess.run(
        [
            'osascript',
            f'-e set x to display dialog "{auth_prompt}" default answer""',
            '-e set x to text returned of x'
        ],
        capture_output=True
    ).stdout.decode('utf-8').strip()

    if not response:
        print('Cancelled')
        sys.exit()

    return response


if sys.platform.startswith('darwin'):
    spotipy.SpotifyOAuth.get_auth_response = modded_auth_response


class SpotifyLibrary:
    """Processes, then stores data retrieved from Spotify in nested dictionaries"""

    def __init__(self, pickleLibrary=None):
        """
        :param pickleLibrary:
            Data about the user's library
            from the previous time the script was run.
            If not None, must be another instance of THIS class.
        """

        self.library = {}
        self.playlists = {}
        self.pickleLibrary = pickleLibrary or {}

    @classmethod
    def fromPickle(cls):
        """
        Returns an instance of IndexLibrary that was saved to a pickle
        using self.dump
        """

        if os.path.exists(pickleDir):
            with open(pickleDir, 'rb') as rp:
                svdpickle = pickle.load(rp)
            return svdpickle

        return cls()

    @staticmethod
    def _finderFormat(f, usedNames=None, default=None, songArtist=False):
        """
        Removes/Escapes characters that can't be
        used/have special meaning in the macOS file system.

        Also appends numbers to strings that are duplicated.
        For example, if two or more playlists have the same name, the number 2 will be added
        to the second one, 3 to the third, and so on.

        This function is applied to all strings that will be used as names for files/folders

        macOS does not allow files/folders to include a colon, so they are removed.
        Files/folders with a leading period get marked as hidden, so they are removed.
        A shell-escaped `/` becomes a colon, so `/`s are replaced with colons.
        For example, if you cd to your desktop and then run `mkdir Some:Folder`,
        The name of the folder will be `Some/Folder`.
        See http://bit.ly/38FsMhK for more info.

        :param f: the name of an item
        :param usedNames: the names that have already been used
        :param default: the default name if f becomes a blank string after the regex
        :param songArtist: If f is a songname, then the artist name gets appended to the end
        """

        if f:
            for r in ((':', ''), ('/', ':'), ('^\.+', '')):
                f = re.sub(r[0], r[1], f)

        # If f is None or an empty string, then the default name is used
        if f:
            fExact = f
        else:
            f = fExact = default

        if songArtist: f += f' - {songArtist}'

        n = 2
        while f in usedNames:
            f = f'{fExact} {n}'
            if songArtist: f += f' - {songArtist}'
            n += 1

        assert f, f'f is falsy: [{f}]; default: [{default}]'
        return f

    def dump(self):
        """Saves the Spotify data into a pickle file"""

        if hasattr(self, 'pickleLibrary'):
            if not self.library:
                self.library = self.pickleLibrary.library

            del self.pickleLibrary

        with open(pickleDir, 'wb') as pd:
            pickle.dump(self, pd, protocol=-1)

    def __bool__(self):
        if self.library and self.playlists:
            return True
        return False

    def add(self, kinds=None, albumKey=None,
            artId=None, artName=None, artImgs=None,
            albId=None, albName=None, albImgs=None,
            sngId=None, sngName=None, context=None
    ):
        """
        Accepts data returned from the Spotify web API, processes it,
        and then adds it into a nested dictionary.

        :param context:
            contains the id of a playlist if the song
            is in a playlist. Else None.
        """

        if albumKey:
            artId = albumKey['artId'] or artId
            artName = albumKey['artName'] or artName
            albId = albumKey['albId'] or albId
            albName = albumKey['albName'] or albName

        albumBox = {
            'artName': artName,
            'artId': artId,
            'albName': albName,
            'albId': albId
        }

        if artId:
            isArtId = True
        else:
            isArtId = False
            artId = artName or 'blank'

        albId = albId or albName or 'blank'

        pcklArts = self.pickleLibrary.library
        pcklAlbs = pcklArts.get(artId, {}).get('albums', {})
        pcklSngs = pcklAlbs.get(albId, {}).get('tracks', {})

        if 'artist' in kinds:
            if not artId in self.library:

                if artName:
                    noArtName = False
                else:
                    artName = 'Unknown Artist'
                    noArtName = True

                if artId in pcklArts:
                    artName = pcklArts[artId]['name']
                else:
                    artNames = [art['name'] for art in self.library.values()] + \
                               [part['name'] for part in pcklArts.values()]

                    artName = self._finderFormat(artName, usedNames=artNames, default='Artist')

                if custom_icon and isArtId:
                    try:
                        artInfo = sp.artist(artId)
                        artImgs = artInfo.get('images')
                    except:
                        pass

                self.library[artId] = {
                    'name': artName, 'noArtName': noArtName,
                    'imgs': artImgs, 'albums': {}
                }

        if 'album' in kinds:
            assert artId in self.library, \
                "can't add album because associated artist hasn't been added"

            albums = self.library[artId]['albums']
            if not albId in albums:

                if albId in pcklAlbs:
                    albName = pcklAlbs[albId]['name']
                else:
                    albNames = [alb['name'] for alb in albums.values()] + \
                               [palb['name'] for palb in pcklAlbs.values()]

                    albName = self._finderFormat(
                        albName or 'Unknown Album', usedNames=albNames, default='Album'
                    )

                self.library[artId]['albums'][albId] = {
                    'name': albName, 'imgs': albImgs, 'tracks': {}
                }

        if 'track' in kinds:
            assert albId in self.library.get(artId, {}).get('albums', {}), \
                "can't add track because associated album and/or artist hasn't been addded"

            songs = self.library[artId]['albums'][albId]['tracks']

            if not sngId in songs:

                sngArtDict = self.library[artId]
                if sngArtDict['noArtName']:
                    sngArtist = False
                else:
                    sngArtist = sngArtDict['name']

                if context:
                    context = f'playlist:{context}'
                else:
                    context = f'album:{albId}'

                sngDir = os.path.join(
                    folder_location, sngArtDict['name'], sngArtDict['albums'][albId]['name']
                )

                if sngId in pcklSngs:
                    fndrNme = pcklSngs[sngId]['fndrNme']
                    sngDir = pcklSngs[sngId]['sngDir']
                else:

                    fndrNames = [sng['fndrNme'] for sng in songs.values()] + \
                                [psng['fndrNme'] for psng in pcklSngs.values()]

                    fndrNme = self._finderFormat(
                        sngName, usedNames=fndrNames, default='Song', songArtist=sngArtist
                    )

                self.library[artId]['albums'][albId]['tracks'][sngId] = {
                    'fndrNme': fndrNme, 'context': context, 'sngDir': sngDir
                }

        return albumBox

    def addPlaylist(self, playlist):

        tTracks = playlist['tracks']['total']
        plistName = playlist['name']
        plistID = playlist['id']
        plistImgDict = playlist.get('images')
        plistSnapshot = playlist.get('snapshot_id')

        plistNames = [pNme['name'] for pNme in self.playlists.values()]
        plistName = self._finderFormat(plistName, usedNames=plistNames, default='Playlist')

        self.playlists[plistID] = {
            'name': plistName, 'imgs': plistImgDict, 'num': tTracks, 'snapshot': plistSnapshot
        }

        plLenGrmr = '' if tTracks == 1 else 's'
        rePrint(f'{plistName} - {tTracks} Track{plLenGrmr}')

        return plistID

    def updatePlaylists(self):
        """
        Compares playlists from Spotify with downloaded playlists
        and renames, makes, and sets icons for them as needed
        """

        global rmvdItems, custom_icon, updateCount

        spotifyPlists = self.playlists
        savedPlists = self.pickleLibrary.playlists

        for svdpK, svdpV in savedPlists.items():
            if svdpK in spotifyPlists and os.path.exists(plistsDir + svdpV['name'] + '.app'):
                # Add a blank space to the end of the playlist app
                renamePlaylistApp(oldName=svdpV['name'])
            elif svdpK not in spotifyPlists:
                # Remove the playlist if it is no longer in Spotify
                mkrmDir('rmDir', plistsDir + svdpV['name'] + '.app')
                rmvdItems['Playlist'].append(svdpV['name'])

        for spPK, spPV in spotifyPlists.items():
            prntPls = False
            # TODO: Rename the playlist to the new name if it exists
            if spPK in savedPlists and os.path.exists(plistsDir + savedPlists[spPK]['name'] + ' .app'):
                oldName = savedPlists[spPK]['name']
                newName = spPV['name']
                renamePlaylistApp(oldName=f'{oldName} ', newName=newName)
                if oldName != newName:
                    rePrint(f'{oldName} was renamed to {newName}')

            # TODO: MAKE THE APP FOR THE PLAYLIST
            else:
                if mkApp(parentDir=plistsDir, appName=spPV['name'], code=spPK):
                    prntPls = True

            # TODO: SET THE ICON FOR THE PLAYLIST
            if custom_icon or resetPlistImgs:
                if setIcon(
                        (plistsDir, spPV['name'] + '.app'),
                        imgDict=spPV['imgs'], imgPath=(dataDir, spPK), typ='pls'
                ):
                    prntPls = True

            if prntPls:
                updateCount += 1
                rePrint(spPV['name'])


################################################################
# TODO: $$$ -- Instantiate Spotify Authentication Manager -- $$$

sp = spotipy.Spotify(
    auth_manager=spotipy.SpotifyOAuth(
        client_id, client_secret, redirect_url,
        scope=scope, cache_path=cachePath, username=username,
        show_dialog=True
    )
)

################################################################
# TODO: $$$$$$$$$$$$$$$$ -- SYSTEM ARGUMENTS -- $$$$$$$$$$$$$$$$

if True:
    sysDelay = False
    resetPlistImgs = False

    if len(sys.argv) > 1:

        if any(s.casefold().startswith('noicon') for s in sys.argv):
            sysDelay = True
            # print('\033[95mIcons Have Been Disabled\033[0m\n')
            custom_icon = False
            # if isMain: time.sleep(2)

        if any(s.casefold().startswith('playlist') for s in sys.argv):
            sysDelay = True
            resetPlistImgs = True

    if not custom_icon:
        sysDelay = True
        print('\033[95mIcons Have Been Disabled\033[0m\n')

    # TODO: Check if fileicon is installed
    if os.path.exists(fileicon_path):
        fileIconExists = True
        dimd = {'alb': 256, 'art': 256, 'pls': 256}
        for dx in (('alb', album_image_size), ('art', artist_image_size), ('pls', playlist_image_size)):
            if dx[1] in (1024, 512, 256, 128):
                dimd[dx[0]] = dx[1]
    else:
        fileIconExists = False
        if custom_icon:
            custom_icon = False
            sysDelay = True
            print(f'Icons have been disabled because\n{fileicon_path}\nwas not found\n')
            # if isMain: time.sleep(3)

    if resetPlistImgs:
        sysDelay = True
        if fileIconExists:
            print('\033[95mPlaylist images will be reset\033[0m\n')
        else:
            print("Can't reset playlist images because fileicon was not found")
            resetPlistImgs = False

    if len(sys.argv) > 1:

        if sys.argv[1] == '___chngPlist___':
            if os.system(
                    'osascript -e \'tell application "Spotify" to get id of current track\''
            ) != 0:
                sysSong(*sys.argv[2:])
            sys.exit()

        elif sys.argv[1] == '___rnPlist___':
            sysPlaylist(sys.argv[2])
            sys.exit()

        elif sys.argv[1] == '___queue___':
            sysQueue(sys.argv[2])
            sys.exit()

    # DEBUG: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
    # print('\ncustom icon =', custom_icon)
    # print('resetPlistImgs =', resetPlistImgs)

    if isMain and sysDelay: time.sleep(2)

################################################################

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$ -- BEGIN MAIN SCRIPT  -- $$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

for mkfolder in (folder_location, dataDir, plistsDir, artImgDir, albImgDir):
    mkrmDir('mkDir', mkfolder)

# TODO: Set the icon for the folder that contains all the songs
#  and the playlist folder
if custom_icon:
    for icon in (folder_location, plistsDir):
        setIcon(
            icon, isPNG=True,
            imgDict=('https://i.ibb.co/89MbxQv/Spotify-Folder-Square.png', 1024),
            imgPath=(dataDir, 'Folder_Icon')
        )

# TODO: Instantiate IndexLibrary objects
svdLibrary = SpotifyLibrary.fromPickle()
spLibrary = SpotifyLibrary(pickleLibrary=svdLibrary)

################################################################

print('\033[95m################### -- Retrieving Saved Playlists -- ###################\033[0m')
playlists = spExtend(sp.user_playlists(username))
plistLen = len(playlists)

TimeStamp = time.time()

if plistLen == 0:
    print('No saved playlists\n')
else:
    print(f'Found {plistLen} Playlist{"" if plistLen == 1 else "s"}\n')

    for playlist in playlists:

        plistID = spLibrary.addPlaylist(playlist)

        # TODO: Get all playlist tracks
        playlistTracks = spExtend(sp.playlist_tracks(plistID))

        for plTrack in playlistTracks:
            if plTrack['is_local']: continue
            plTrack = plTrack['track']

            # TODO: Get playlist track data
            spLibrary.add(
                kinds=('artist', 'album', 'track'),
                artId=plTrack.get('artists', [{}])[0].get('id'),
                artName=plTrack.get('artists', [{}])[0].get('name'),
                albId=plTrack.get('album', {}).get('id'),
                albName=plTrack.get('album', {}).get('name'),
                albImgs=plTrack.get('album', {}).get('images'),
                sngId=plTrack.get('id'),
                sngName=plTrack.get('name'),
                context=plistID
            )

################################################################

print('\033[95m################### -- Retrieving Saved Albums -- ###################\033[0m')

userAlbums = spExtend(sp.current_user_saved_albums(limit=50))

userAlbLen = len(userAlbums)

if userAlbLen == 0:
    print('No saved albums\n')
else:
    print(f'Found {userAlbLen} album{"" if userAlbLen == 1 else "s"}\n')

    for album in (albb['album'] for albb in userAlbums):

        artistName = album.get('artists', [{}])[0].get('name')
        albumName = album.get('name')
        albumLen = album.get('total_tracks')
        print('{} - {} ({} Track{})'
              .format(albumName, artistName, albumLen, '' if albumLen == 1 else 's'))

        albumKey = spLibrary.add(
            kinds=('artist', 'album'),
            artId=album.get('artists', [{}])[0].get('id'),
            artName=artistName,
            albId=album.get('id'),
            albName=albumName,
            albImgs=album.get('images'),
        )

        # TODO: Get all album tracks
        albTracks = spExtend(album['tracks'])

        # TODO: Get Track Data
        for albTrack in albTracks:
            if albTrack['is_local']: continue
            spLibrary.add(
                kinds=('track',),
                albumKey=albumKey,
                sngId=albTrack.get('id'),
                sngName=albTrack.get('name')
            )

################################################################

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$ -- RENAME OR DELETE SAVED ITEMS -- $$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

for artK, artV in svdLibrary.library.items():

    # TODO: If the artist is no longer in the user's library
    artPath = (folder_location, artV['name'])
    if not artK in spLibrary.library:
        # Maintains dictionary of removed items
        rmvdItems['Artist'].append(artV['name'])
        # Delete the artist folder
        mkrmDir('rmDir', artPath)
        # Delete the artist image
        mkrmDir('rmFile', (artImgDir, f'{artK}.icns'))
        # Delete all album images for the artist
        for rmArtAlb in artV['albums']:
            mkrmDir('rmFile', (albImgDir, f'{rmArtAlb}.icns'))

    else:

        allArtAlbs = spLibrary.library[artK]['albums']
        for artAlbK, artAlbV in artV['albums'].items():

            # TODO: If the album is no longer in the user's library
            albPath = (*artPath, artAlbV['name'])
            if not artAlbK in allArtAlbs:

                rmvdItems['Album'].append(artAlbV['name'])
                # Delete the album folder
                mkrmDir('rmDir', albPath)
                # Delete the album image
                mkrmDir('rmFile', (albImgDir, f'{artAlbK}.icns'))

            else:

                allArtAlbSngs = allArtAlbs[artAlbK]['tracks']
                for artAlbSngK, artAlbSngV in artAlbV['tracks'].items():

                    # TODO: If the song is no longer in the user's library
                    if not artAlbSngK in allArtAlbSngs:
                        rmvdItems['Song'].append(artAlbSngV['fndrNme'])
                        # Delete the song
                        mkrmDir('rmDir', (*albPath, artAlbSngV['fndrNme'] + '.app'))


                    # TODO: If the song was moved to a different playlist or to an album, then update the app
                    else:
                        oldContext = artAlbSngV['context']
                        newContext = allArtAlbSngs[artAlbSngK]['context']
                        # if allArtAlbSngs[artAlbSngK]['context'] != artAlbSngV['context']:
                        if newContext != oldContext:
                            chngSongContext(
                                parentDir=albPath,
                                appName=artAlbSngV['fndrNme'],
                                context=newContext
                            )

# TODO: RENAME, DELETE, OR MAKE PLAYLISTS
if spLibrary.playlists:
    mkPlMsg = 'Downloading Playlists'
    if custom_icon: mkPlMsg += ' and Setting Icons'
    print(f'\033[95m################### -- {mkPlMsg} -- ###################\033[0m\n')
    plsLen = len(spLibrary.playlists)
    print(f'{plsLen} playlist{"" if plsLen == 1 else "s"}\n')

spLibrary.updatePlaylists()

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$ -- MAKE APPS AND SET ICONS -- $$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

if spLibrary.library:
    mkSngMsg = 'Downloading Songs'
    if custom_icon: mkSngMsg += ' and Setting Icons'
    artLen = len(spLibrary.library)
    print(f'\n\033[95m################### -- {mkSngMsg} -- ###################\033[0m')
    print(f'\n{artLen} artist{"" if artLen == 1 else "s"}')

else:
    print("You Don't have any songs on Spotify!")

for spArtK, spArtV in spLibrary.library.items():

    # Print the artist name
    albLen = len(spArtV['albums'])
    rePrint(f'\n\033[95m{spArtV["name"]} ({albLen} album{"" if albLen == 1 else "s"})\033[0m')

    # Make the artist folder
    artFolder = os.path.join(folder_location, spArtV['name'])
    mkrmDir('mkDir', artFolder)

    # Set artist icon
    if custom_icon:
        if setIcon(
                artFolder, imgDict=spArtV['imgs'],
                imgPath=(artImgDir, spArtK), typ='art'
        ):
            updateCount += 1

    ################################################################
    # TODO: For each of an artist's albums
    for albK, albV in spArtV['albums'].items():

        # Print the album name
        trkLen = len(albV['tracks'])
        # rePrint('\t' + albV['name'] + f' ({trkLen} tracks{"" if trkLen == 1 else "s"})')
        rePrint(f'\n\t\033[95m{albV["name"]} ({trkLen} track{"" if trkLen == 1 else "s"})\033[0m')

        # Make the album folder
        albFolder = os.path.join(artFolder, albV['name'])
        mkrmDir('mkDir', albFolder)

        # Set the album icon if it is not already set
        if custom_icon and not os.path.exists(albFolder + '/Icon\r'):

            # Try to use album image
            isAlbIconSet = setIcon(albFolder, imgDict=albV['imgs'],
                                   imgPath=(albImgDir, albK), typ='alb')

            # Else try to use the artist image
            if not isAlbIconSet:
                isAlbIconSet = setIcon(
                    albFolder, imgDict=spArtV['imgs'],
                    imgPath=(artImgDir, spArtK), typ='alb'
                )

            if isAlbIconSet: updateCount += 1

        # If the artist image doesn't exist, try to use the album image for the artist
        if custom_icon and not os.path.exists(artFolder + '/Icon\r'):
            if setIcon(
                    artFolder, imgDict=albV['imgs'],
                    imgPath=(albImgDir, albK), typ='alb'
            ):
                updateCount += 1

        ################################################################
        # TODO: For each of an album's tracks
        for sngK, sngV in albV['tracks'].items():

            # TODO: Make the song app
            prntSng = False
            # mkApp returns True if the app was made, else None
            if mkApp(
                    parentDir=albFolder, appName=sngV['fndrNme'],
                    code=(sngK, sngV['context'], albK, spArtK)
            ):
                # (songId, context, albumId, artistId)
                prntSng = True

            # set song Icon
            songApp = os.path.join(albFolder, sngV['fndrNme']) + '.app'
            if custom_icon and not os.path.exists(songApp + '/Icon\r'):
                # Try to use album img, then artist img
                # setIcon returns None if the icon was not set and True if it was
                if setIcon(songApp, imgPath=(albImgDir, albK)):
                    prntSng = True
                elif setIcon(songApp, imgPath=(artImgDir, spArtK)):
                    prntSng = True

            # Print the song name only if it has been newly downloaded
            # or its icon has been newly set
            if prntSng:
                rePrint('\t\t' + sngV['fndrNme'])
                updateCount += 1

# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$ -- END MAIN SCRIPT  -- $$$$$$$$$$$$$$$
# TODO: $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

spLibrary.dump()

# Print removed items
rmvdLen = (sum(len(rr) for rr in rmvdItems.values()))
if rmvdLen > 0:
    print('\n\033[91m################### -- {}{} Removed -- ###################\033[0m'
          .format(rmvdLen, ' Item Was' if rmvdLen == 1 else ' Items Were'))

    for rmK, rmV in rmvdItems.items():
        leni = len(rmV)
        if leni:
            print('\n\033[91m{} {}{} Removed\033[0m\n'
                  .format(leni, rmK, ' Was' if leni == 1 else 's Were'))
            for rmvdi in rmV:
                rePrint(rmvdi)

print('\n\n###############################################################\n')


def formatTime(s):
    """
    Takes a number of seconds as input (int or float)
    and returns a length of time in human-readable format with correct grammar.
    """

    if s < 0.01: return 'less than 0.01 seconds'
    tList = []

    hours = s // 3600
    if hours != 0:
        strhours = '1 Hour' if hours == 1 else f'{int(hours)} hours'
        tList.append(strhours)

    s -= hours * 3600
    minutes = s // 60
    if minutes != 0:
        strminutes = '1 Minute' if minutes == 1 else f'{int(minutes)} minutes'
        tList.append(strminutes)

    s -= minutes * 60
    if s != 0:
        strseconds = '1 Second' if s == 1 else f'{round(s, 2)} seconds'
        tList.append(strseconds)

    if len(tList) == 1: return tList[0]
    if len(tList) == 2: return f'{tList[0]} and {tList[1]}'
    return f'{tList[0]}, {tList[1]}, and {tList[2]}'


if updateCount:
    elapsed = time.time() - TimeStamp
    elapsedH = formatTime(elapsed)
    perItem = formatTime(elapsed / updateCount)
    fGrmr = '' if updateCount == 1 else 's'
    finalMsg = f'It took {elapsedH} to Update {updateCount} Item{fGrmr}'
    # print('\033[95m\n#----------------------------------------------------------------#\033[0m')
    print(finalMsg)
    if updateCount > 1: print(f'{perItem.capitalize()} per Item\033[0m\n')

    osaMsg(finalMsg, titl='Indexing Finished')
else:
    finalMsg = 'No New Songs or Icons to Apply'
    print(f'\n\033[91m{finalMsg}\n\033[0m')
    osaMsg(finalMsg)
