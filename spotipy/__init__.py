# coding: utf-8

from __future__ import print_function

import requests
import json
import sys

__all__ = ['oauth2']

'''
A simple and thin Python library for the Spotify Web API
'''


class SpotifyException(Exception):
    def __init__(self, http_status, code, msg):
        self.http_status = http_status
        self.code = code
        self.msg = msg

    def __str__(self):
        return u'http status: {0}, code:{1} - {2}'.format(
            self.http_status, self.code, self.msg)


class Spotify(object):
    '''
        Example usage:

            import spotipy

            urn = 'spotify:artist:3jOstUTkEu2JkjvRdBA5Gu'
            sp = spotipy.Spotify()

            sp.trace = True # turn on tracing

            artist = sp.artist(urn)
            print(artist)

            user = sp.user('plamere')
            print(user)
    '''

    trace = False
    _auth = None

    def __init__(self, auth=None):
        self.prefix = 'https://api.spotify.com/v1/'
        self._auth = auth

    def _auth_headers(self):
        if self._auth:
            return {'Authorization': 'Bearer {0}'.format(self._auth)}
        else:
            return {}

    def _internal_call(self, verb, method, params):
        if not method.startswith('http'):
            url = self.prefix + method
        else:
            url = method
        args = dict(params=params)
        if 'data' in params.keys():
            args['data'] = params['data']
            del args['params']['data']
        headers = self._auth_headers()
        headers['Content-Type'] = 'application/json'
        if self.trace:
            print()
            print(args)
        r = requests.request(verb, url, headers=headers, **args)
        if self.trace:
            print()
            print(verb, r.url)
        try:
            r.raise_for_status()
        except:
            raise SpotifyException(
                r.status_code,
                -1,
                u'%s:\n %s' % (r.url, r.json()['error']['message'])
            )
        if len(r.text) > 0:
            results = r.json()
            if self.trace:
                print()
                print('RESP', results)
                print()
            return results
        else:
            return {}

    def get(self, method, args=None, **kwargs):
        if args:
            kwargs.update(args)
        return self._internal_call('GET', method, kwargs)

    def delete(self, method, payload=None, args=None, **kwargs):
        if args:
            kwargs.update(args)
        if payload:
            kwargs['data'] = json.dumps(payload)
        return self._internal_call('DELETE', method, kwargs)

    def put(self, method, payload=None, args=None, **kwargs):
        if args:
            kwargs.update(args)
        if payload:
            kwargs['data'] = json.dumps(payload)
        return self._internal_call('PUT', method, kwargs)

    def post(self, method, payload=None, args=None, **kwargs):
        if args:
            kwargs.update(args)
        if payload:
            kwargs['data'] = json.dumps(payload)
        return self._internal_call('POST', method, kwargs)

    def next(self, result):
        ''' returns the next result given a result
        '''
        if result['next']:
            return self.get(result['next'])
        else:
            return None

    def previous(self, result):
        ''' returns the previous result given a result
        '''
        if result['previous']:
            return self.get(result['previous'])
        else:
            return None

    def _warn(self, msg):
        print('warning:' + msg, file=sys.stderr)

    def track(self, track_id):
        ''' returns a single track given the track's ID, URN or URL
        '''

        trid = self._get_id('track', track_id)
        return self.get('tracks/' + trid)

    def tracks(self, tracks):
        ''' returns a list of tracks given the track IDs, URNs, or URLs
        '''

        tlist = [self._get_id('track', t) for t in tracks]
        return self.get('tracks/?ids=' + ','.join(tlist))

    def artist(self, artist_id):
        ''' returns a single artist given the artist's ID, URN or URL
        '''

        trid = self._get_id('artist', artist_id)
        return self.get('artists/' + trid)

    def artists(self, artists):
        ''' returns a list of artists given the artist IDs, URNs, or URLs
        '''

        tlist = [self._get_id('artist', a) for a in artists]
        return self.get('artists/?ids=' + ','.join(tlist))

    def artist_albums(
        self, artist_id, album_type=None, country=None, limit=20, offset=0
    ):
        ''' Get Spotify catalog information about an artist’s albums
        '''

        trid = self._get_id('artist', artist_id)
        return self.get(
            'artists/' + trid + '/albums',
            album_type=album_type,
            country=country,
            limit=limit,
            offset=offset
        )

    def artist_top_tracks(self, artist_id, country='US'):
        '''
        Get Spotify catalog information about an artist’s top 10 tracks
        by country.
        '''

        trid = self._get_id('artist', artist_id)
        return self.get('artists/' + trid + '/top-tracks', country=country)

    def artist_related_artists(self, artist_id):
        '''
        Get Spotify catalog information about artists similar to an identified
        artist. Similarity is based on analysis of the Spotify community’s
        listening history.
        '''
        trid = self._get_id('artist', artist_id)
        return self.get('artists/' + trid + '/related-artists')

    def album(self, album_id):
        ''' returns a single album given the album's ID, URN or URL
        '''

        trid = self._get_id('album', album_id)
        return self.get('albums/' + trid)

    def album_tracks(self, album_id):
        ''' Get Spotify catalog information about an album’s tracks
        '''

        trid = self._get_id('album', album_id)
        return self.get('albums/' + trid + '/tracks/')

    def albums(self, albums):
        ''' returns a list of albums given the album IDs, URNs, or URLs
        '''

        tlist = [self._get_id('album', a) for a in albums]
        return self.get('albums/?ids=' + ','.join(tlist))

    def search(self, q, limit=10, offset=0, type='track'):
        ''' searches for an item
        '''
        return self.get('search', q=q, limit=limit, offset=offset, type=type)

    def user(self, user_id):
        ''' Gets basic profile information about a Spotify User
        '''
        return self.get('users/' + user_id)

    def user_playlists(self, user):
        ''' Gets playlists of a user
        '''
        return self.get("users/%s/playlists" % user)

    def user_playlist(self, user, playlist_id=None, fields=None):
        ''' Gets playlist of a user
        '''
        if playlist_id is None:
            return self.get("users/%s/starred" % (user), fields=fields)
        return self.get(
            "users/%s/playlists/%s" % (user, playlist_id),
            fields=fields
        )

    def user_playlist_create(self, user, name, public=True):
        ''' Creates a playlist for a user
        '''
        data = {'name': name, 'public': True}
        return self.post("users/%s/playlists" % (user,), payload=data)

    def user_playlist_add_tracks(
        self, user, playlist_id, tracks, position=None
    ):
        '''
        Adds tracks identified by URI to a playlist
        '''
        return self.post(
            "users/%s/playlists/%s/tracks" % (user, playlist_id),
            payload=tracks,
            position=position
        )

    def user_playlist_delete_tracks(
        self, user, playlist_id, track_uris, position=None
    ):
        '''
        Deletes a list of tracks from a playlist, identified by their URI, e.g.

        [
            "spotify:track:4iV5W9uYEdYUVa79Axb7Rh",
            "spotify:track:1301WleyT98MSxVHPZCA6M"
        ]


        { "tracks": [{ "uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh" },{
"uri": "spotify:track:1301WleyT98MSxVHPZCA6M" }] }
        TODO: support snapshot_id
        '''

        to_delete = {"tracks": []}
        for t in track_uris:
            to_delete['tracks'].append({'uri': t})
        return self.delete(
            "users/%s/playlists/%s/tracks" % (user, playlist_id),
            payload=to_delete,
            position=position
        )

    def me(self):
        ''' Get detailed profile information about the current user.
        '''
        return self.get('me/')

    def current_user(self):
        ''' Get detailed profile information about the current user.
        '''
        return self.me()

    def current_user_saved_tracks(self, limit=20, offset=0):
        ''' Gets a list of the tracks saved in the current authorized user's
            "Your Music" library
        '''
        return self.get('me/tracks', limit=limit, offset=offset)

    def current_user_saved_tracks_delete(self, ids=[]):
        ''' Remove one or more tracks from the current user’s
            “Your Music” library.
        '''
        tlist = [self._get_id('track', t) for t in ids]
        return self.delete('me/tracks/?ids=' + ','.join(tlist))

    def current_user_saved_tracks_add(self, ids=[]):
        ''' Add one or more tracks to the current user’s
            “Your Music” library.
        '''
        tlist = [self._get_id('track', t) for t in ids]
        return self.put('me/tracks/?ids=' + ','.join(tlist))

    def _get_id(self, id_type, item_id):
        msg = 'expected id of type %s but found type %s %s'
        fields = item_id.split(':')
        if len(fields) == 3:
            if id_type != fields[1]:
                self._warn(msg % id_type, fields[2], item_id)
            return fields[2]
        fields = item_id.split('/')
        if len(fields) >= 3:
            itype = fields[-2]
            if id_type != itype:
                self._warn(msg % id_type, itype, item_id)
            return fields[-1]
        return item_id
