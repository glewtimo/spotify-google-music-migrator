# gm api imports
from __future__ import print_function, division, absolute_import, unicode_literals
from builtins import *  # noqa
from getpass import getpass
from gmusicapi import Mobileclient

# spotify api imports
import spotipy
import spotipy.util as util


def _chunker(seq, size):
    """Helper function to chunk lists into certain sizes to help
       with managing rate limits
    """
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def _gm_ask_for_credentials():
    """Make an instance of the api and attempts to login with it.
    Return the authenticated api.
    """

    # We're not going to upload anything, so the Mobileclient is what we want.
    api = Mobileclient()

    logged_in = False
    attempts = 0

    while not logged_in and attempts < 3:
        email = input('Google Music Email: ')
        password = getpass()

        logged_in = api.login(email, password, Mobileclient.FROM_MAC_ADDRESS)
        attempts += 1

    return api


def _gm_get_songs(api):
    """Get all songs from a users' Google Music library.
    """
    # Get all of the users songs. library is a list of dictionaries, each of which contains a single song.
    print('Loading GM library...', end=' ')
    library = api.get_all_songs()
    print('done.')

    print(len(library), 'tracks detected.')
    print()

    return library


def _gm_get_playlists(api):
    """Get all playlists from a users' Google Music library.
    """
    # Get all of the users songs. library is a list of dictionaries, each of which contains a single song.
    print('Loading GM library...', end=' ')
    playlists = api.get_all_user_playlist_contents()
    print('done.')

    print(len(playlists), 'playlists detected.')
    print()

    return playlists


def gm_get_music():
    # get authenticated api
    api = _gm_ask_for_credentials()

    if not api.is_authenticated():
        print("Sorry, those credentials weren't accepted.")
        return

    print('Successfully logged in to Google Music.')
    print()

    songs = _gm_get_songs(api)  # get songs
    playlists = _gm_get_playlists(api)  # get playlists

    # logout of gm when finished.
    api.logout()
    print('All done!')

    return songs, playlists


def _sp_find_track_idx(track, album):
    count = 0
    track_idx = 0
    for track_num in track['tracks']['items']:
        if track_num['album']['name'] == album:
            track_idx = count
            break
        else:
            count += 1

    return track_idx


def sp_parse_albums(spotify_tracks, spotify_albums):
    """Takes a list of song dictionaries of spotify tracks,
       and separates out track ids of single songs in a library
       from common album ids of songs that were added as an album
       and returns lists of these ids. If > 50% of songs from an
       album appear in spotify_tracks the entire album will be
       added. Else, individual songs will be added. Returns lists
       of track and album ids.
    """
    aids_dict = {}
    tids = []
    aids = []

    # calculate the number of tracks from each unique albums
    for key in spotify_tracks:
        if key['aid'] not in aids_dict:  # if first time seeing an aid, add to dict and set count to 1
            aids_dict[key['aid']] = 1
        else:  # else if already seen aid, inc its count
            aids_dict[key['aid']] += 1

    # calculate which albums have > 50% of their tracks and add their aids to aids list
    # by dividing number of tracks found by total songs on an album
    for key in aids_dict:
        ratio = aids_dict[key] / spotify_albums[key]  # calc the ratio
        if ratio > 0.5:
            aids.append(key)  # if ratio is over 50% add aid to list of whole albums to be added

    # cycle through all tracks, if their assocaited aid isn't in aids, it is a single track, so add to tids
    for key in spotify_tracks:
        if key['aid'] not in aids:
            tids.append(key['tid'])

    return aids, tids


def sp_parse_playlists(spotify_tracks):
    """Takes a list of song dictionaries of spotify tracks,
       and separates out track ids of songs. Returns a list
       of track ids.
    """
    tids = []

    # cycle through all tracks and add their ids to list
    for key in spotify_tracks:
        tids.append(key['tid'])

    return tids


def sp_get_ids_library(songs, sp):
    """Takes a list of song dictionaries of gm songs and
       finds the spotify track/album IDs for each and returns
       lists of them. If a song can't be located add to
       list of unavailable songs and return that list too
    """
    spotify_tracks = []
    not_on_spotify = []
    spotify_albums = {}

    # loop through each
    for i in range(len(songs)):
        song = songs[i]

        # get track info
        artist = song['artist']
        album = song['album']
        title = song['title']

        # clean track info
        title_feat_idx = title.find(" (")  # check if gm title includes " (*" to remove features/explicit/etc from title
        if title_feat_idx != -1:  # if title includes it
            title = title[0:title_feat_idx]  # strip away " (*"

        title = title.replace("'", "")  # remove apostrophes from song titles
        album = album.replace("'", "")  # remove apostrophes from albums titles
        artist = artist.replace(" & ", ", ")  # replace & with , to conform to spotify nomenclature

        # use sp search api to get spotify id for each song
        track = sp.search(q='artist:' + artist + ' track:' + title + ' album:' + album, type='track')

        # if song appears on multiple albums, try to pull from album it appears on in gm library
        track_idx = _sp_find_track_idx(track, song['album'])

        # if song can't be found on spotify on a given album, check if it can be found on another album
        if len(track['tracks']['items']) == 0:
            # use sp search api to get spotify id for song without an associated album
            track = sp.search(q='artist:' + artist + ' track:' + title, type='track')
            track_idx = _sp_find_track_idx(track, song['album'])
            if len(track['tracks']['items']) == 0:
                # if song still can't be found put into list of unavailable songs
                not_on_spotify.append({"artist": artist, "track": title, "album": album})
            else:
                # else add dictionary of tid, and aid to tracks list
                spotify_tracks.append({"tid": track['tracks']['items'][track_idx]['id'],
                                       "aid": track['tracks']['items'][track_idx]['album']['id']})
                # add aid and associated number of songs on the album to album dictionary
                spotify_albums[track['tracks']['items'][track_idx]['album']['id']] = track['tracks']['items'][track_idx]['album']['total_tracks']
        else:
            # else add dictionary of tid, and aid to tracks list
            spotify_tracks.append({"tid": track['tracks']['items'][track_idx]['id'],
                                   "aid": track['tracks']['items'][track_idx]['album']['id']})
            # add aid and associated number of songs on the album to album dictionary
            spotify_albums[track['tracks']['items'][track_idx]['album']['id']] = track['tracks']['items'][track_idx]['album']['total_tracks']

    # parse spotify tracks into albums and individual tracks to get lists of their ids
    album_ids, track_ids = sp_parse_albums(spotify_tracks, spotify_albums)
    return album_ids, track_ids, not_on_spotify


def sp_get_ids_playlist(songs, sp):
    """Takes a list of song dictionaries of gm songs from a
       playlist and finds the spotify track IDs for each and
       returns a list of them. If a song can't be located add to
       list of unavailable songs and return that list too
    """
    track_ids = []
    not_on_spotify = []

    # loop through each
    for i in range(len(songs)):
        song = songs[i]

        # get track info if it exists
        if 'track' in song:
            artist = song['track']['artist']
            album = song['track']['album']
            title = song['track']['title']
        # if there is no track info, then gm didn't provide any info when pulling the playlist, skip to next iteration
        else:
            continue

        # clean track info
        title_feat_idx = title.find(" (")  # check if gm title includes " (*" to remove features/explicit/etc from title
        if title_feat_idx != -1:  # if title includes it
            title = title[0:title_feat_idx]  # strip away " (*"

        title = title.replace("'", "")  # remove apostrophes from song titles
        album = album.replace("'", "")  # remove apostrophes from albums titles
        artist = artist.replace(" & ", ", ")  # replace & with , to conform to spotify nomenclature

        # use sp search api to get spotify id for each song
        track = sp.search(q='artist:' + artist + ' track:' + title + ' album:' + album, type='track')

        # if song appears on multiple albums, try to pull from album it appears on in gm library
        track_idx = _sp_find_track_idx(track, song['track']['album'])

        # if song can't be found on spotify on a given album, check if it can be found on another album
        if len(track['tracks']['items']) == 0:
            # use sp search api to get spotify id for song without an associated album
            track = sp.search(q='artist:' + artist + ' track:' + title, type='track')
            track_idx = _sp_find_track_idx(track, song['album'])
            if len(track['tracks']['items']) == 0:
                # if song still can't be found put into list of unavailable songs
                not_on_spotify.append({"artist": artist, "track": title, "album": album})
            else:
                # else add to list of tids
                track_ids.append(track['tracks']['items'][track_idx]['id'])
        else:
            # else add to list of tids
            track_ids.append(track['tracks']['items'][track_idx]['id'])

    return track_ids, not_on_spotify


def sp_add_tracks(tids, sp):
    """Takes a list of spotify track ids and adds them to sp library
    """
    # use spotify api to add songs 20 at a time to stay within rate limits
    for group in _chunker(tids, 20):  # call chunker to split tids into groups before adding
        results = sp.current_user_saved_tracks_add(tracks=group)


def sp_add_albums(aids, sp):
    """Takes a list of spotify album ids and adds them to sp library
    """
    # use spotify api to add songs 20 at a time to stay within rate limits
    for group in _chunker(aids, 20):  # call chunker to split aids into groups before adding
        results = sp.current_user_saved_albums_add(albums=group)


def sp_add_gm_music(songs, sp_username, sp):
    """Takes a list of song dictionaries of gm songs that
        are to be added to spotify, parses them between
        individual songs and full albums, adds them, then
        returns any tracks that couldn't be found
    """
    # use list of songs generated by gm api to get a list of spotify track IDs and tracks unavailable
    aids, tids, invalid_ids = sp_get_ids_library(songs, sp)

    # add albums
    sp_add_albums(aids, sp)

    # add tracks
    sp_add_tracks(tids, sp)

    # return any invalid ids
    return invalid_ids


def sp_add_tracks_to_playlist(tids, pl_id, sp_username, sp):
    """Takes a username, list of spotify track ids, and a playlist id and
       adds those tracks to that playlist for that user
    """
    # use spotify api to add songs 20 at a time to stay within rate limits
    for group in _chunker(tids, 20):  # call chunker to split tids into groups before adding
        sp.user_playlist_add_tracks(sp_username, pl_id, tids, position=None)


def sp_process_gm_playlist(pl, sp_username, sp):
    """Takes a playlist dictionary of a gm playlists,
       adds the playlist and songs to Spotify and then
       returns a list of dictionaries of tracks that
       couldn't be found
    """
    # get playlist name
    pl_name = pl['name']

    # create playlist
    new_playlist = sp.user_playlist_create(sp_username, pl_name, public=False, description='')

    # get ids of songs on playlist and ids of songs that couldn't be found
    tids, invalid_ids = sp_get_ids_playlist(pl['tracks'], sp)

    # add songs to playlist
    sp_add_tracks_to_playlist(tids, new_playlist['id'], sp_username, sp)

    # return songs that couldn't be found
    return invalid_ids


def sp_add_gm_playlists(playlists, sp_username, sp):
    """Takes a list of playlist dictionaries of gm playlists that
        are to be added to spotify, adds them, then
        returns any tracks that couldn't be found
    """
    invalid_ids = []  # to store tracks that can't be found in Spotify

    # iterate through playlists and add them one by one
    for pl in playlists:
        bad_ids = sp_process_gm_playlist(pl, sp_username, sp)  # add playlist and store any invalid songs
        invalid_ids.append(bad_ids)  # add invalid songs dictionaries to list

    # return any invalid track ids
    return invalid_ids


if __name__ == '__main__':
    # retrieve songs and playlists from Google Music library
    gm_songs, gm_playlists = gm_get_music()

    # get users' spotify username
    username = input("Spotify username: ")

    # generate spotify token and add music/playlists
    SPOTIPY_CLIENT_ID = ''
    SPOTIPY_CLIENT_SECRET = ''
    SPOTIPY_REDIRECT_URI = ''
    scope = 'user-library-modify user-library-read playlist-modify-private playlist-read-private'
    token = util.prompt_for_user_token(username, scope, client_id=SPOTIPY_CLIENT_ID,
                                       client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False

        # parses gm music into albums and individual tracks, adds them to spotify, and returns any
        # tracks that couldn't be found in spotify
        invalid_tids = sp_add_gm_music(gm_songs, username, sp)

        # build spotify playlists from playlists retrieved from gm
        sp_add_gm_playlists(gm_playlists, username, sp)

        # print out which songs couldn't be added
        songNum = 1
        for key in invalid_tids:
            print("Song %d: %s - %s - %s" % (songNum, key['track'], key['artist'], key['album']))
            songNum += 1
    else:
        print("Can't get token for", username)
