# spotify api imports
import spotipy
import spotipy.util as util


def sp_remove_all_albums(sp):
    """Removes all albums from a users' spotify
    """
    # can only retrieve 20 albums at a time so loop and remove albums until all are gone
    do = True  # force loop to run at least once
    while do is True or len(aids) > 0:  # var do forces first loop then we check if the last loop returned results
        do = False

        # use spotify api to get list of spotify albums currently liked by the user (max 20 will be returned)
        sp_albums = sp.current_user_saved_albums()

        # extract album ids from list of albums returned from spotify api
        aids = []
        for i in range(len(sp_albums['items'])):
            aids.append(sp_albums['items'][i]['album']['id'])

        # use spotify api to remove liked albums based on their album id
        if len(aids) > 0:
            results = sp.current_user_saved_albums_delete(albums=aids)


def sp_remove_all_songs(sp):
    """Removes all songs from a users' spotify
    """
    # can only retrieve 20 songs at a time so loop and remove songs until all are gone
    do = True  # force loop to run at least once
    while do is True or len(tids) > 0:  # var do forces first loop then we check if the last loop returned results
        do = False

        # use spotify api to get list of spotify tracks currently liked by the user (max 20 will be returned)
        sp_songs = sp.current_user_saved_tracks()

        # extract track ids from list of tracks returned from spotify api
        tids = []
        for i in range(len(sp_songs['items'])):
            tids.append(sp_songs['items'][i]['track']['id'])

        # use spotify api to remove liked songs based on their track id
        if len(tids) > 0:
            results = sp.current_user_saved_tracks_delete(tracks=tids)


def sp_remove_all_playlists(sp_username, sp):
    """Removes all playlists from a users' spotify
    """
    # can only retrieve 20 playlists at a time so loop and remove playlists until all are gone
    do = True  # force loop to run at least once
    while do is True or len(pl_ids) > 0:  # var do forces first loop then we check if the last loop returned results
        do = False

        # use spotify api to get list of spotify playlists currently followed by the user (max 20 will be returned)
        sp_playlists = sp.current_user_playlists()

        # extract playlist ids from list of playlists returned from spotify api
        pl_ids = []
        for i in range(len(sp_playlists['items'])):
            pl_ids.append(sp_playlists['items'][i]['id'])

        # use spotify api to remove playlists based on their ids and username
        for pl in pl_ids:
            results = sp.user_playlist_unfollow(sp_username, pl)


if __name__ == '__main__':
    # get users' spotify username
    username = input("Spotify username: ")

    SPOTIPY_CLIENT_ID = ''
    SPOTIPY_CLIENT_SECRET = ''
    SPOTIPY_REDIRECT_URI = ''

    scope = 'user-library-modify user-library-read playlist-modify-private playlist-read-private'

    token = util.prompt_for_user_token(username, scope, client_id=SPOTIPY_CLIENT_ID,
                                       client_secret=SPOTIPY_CLIENT_SECRET, redirect_uri=SPOTIPY_REDIRECT_URI)

    if token:
        sp = spotipy.Spotify(auth=token)
        sp.trace = False

        sp_remove_all_songs(sp)
        sp_remove_all_albums(sp)
        sp_remove_all_playlists(username, sp)
    else:
        print("Can't get token for", username)


