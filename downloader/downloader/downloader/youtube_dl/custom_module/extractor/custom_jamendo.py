#!/usr/bin/env python
# coding: utf-8
from __future__ import unicode_literals

import hashlib
import random
import re
import json
import time

from youtube_dl.compat import compat_str
from youtube_dl.extractor.common import InfoExtractor, SearchInfoExtractor
from youtube_dl.utils import (
    clean_html,
    int_or_none,
    try_get,
    ExtractorError
)


class CustomJamendoIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            licensing\.jamendo\.com/[^/]+|
                            (?:www\.)?jamendo\.com
                        )
                        /track/(?P<id>[0-9]+)(?:/(?P<display_id>[^/?#&]+))?
                    '''
    _TESTS = [{
        'url': 'https://www.jamendo.com/track/196219/stories-from-emona-i',
        'md5': '6e9e82ed6db98678f171c25a8ed09ffd',
        'info_dict': {
            'id': '196219',
            'display_id': 'stories-from-emona-i',
            'ext': 'flac',
            'title': 'Maya Filipič - Stories from Emona I',
            'artist': 'Maya Filipič',
            'track': 'Stories from Emona I',
            'duration': 210,
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1217438117,
            'upload_date': '20080730',
        }
    }, {
        'url': 'https://licensing.jamendo.com/en/track/1496667/energetic-rock',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        track_id, display_id = self._VALID_URL_RE.match(url).groups()
        webpage = self._download_webpage(
            'https://www.jamendo.com/track/' + track_id, track_id)
        title = self._html_search_meta(['og:title', 'twitter:title'], webpage, 'title')
        description = self._html_search_meta(['og:description', 'description'], webpage, 'description')
        thumbnail = self._html_search_meta(['image', 'og:image'], webpage, 'thumbnail')

        audio_url = self._html_search_meta(['og:audio', 'og:audio:secure_url'], webpage, 'audio_url')

        if not audio_url:
            raise ExtractorError('Not Find audio_url')

        formats = [{
            'url': audio_url,
            'format_id': 'mp31',
            'ext': 'mp3'
        }]
        self._sort_formats(formats)

        return {
            'id': track_id,
            'display_id': display_id,
            'thumbnail': thumbnail,
            'title': title,
            'description': description,
            'duration': description,
            'formats': formats,
            'timestamp': None,
        }


class CustomJamendoPlaylistIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/(?:album|playlist)/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'https://www.jamendo.com/album/121486/duck-on-cover',
        'info_dict': {
            'id': '121486',
            'title': 'Duck On Cover',
            'description': 'md5:c2920eaeef07d7af5b96d7c64daf1239',
        },
        'playlist': [{
            'md5': 'e1a2fcb42bda30dfac990212924149a8',
            'info_dict': {
                'id': '1032333',
                'ext': 'flac',
                'title': 'Shearer - Warmachine',
                'artist': 'Shearer',
                'track': 'Warmachine',
                'timestamp': 1368089771,
                'upload_date': '20130509',
            }
        }, {
            'md5': '1f358d7b2f98edfe90fd55dac0799d50',
            'info_dict': {
                'id': '1032330',
                'ext': 'flac',
                'title': 'Shearer - Without Your Ghost',
                'artist': 'Shearer',
                'track': 'Without Your Ghost',
                'timestamp': 1368089771,
                'upload_date': '20130509',
            }
        }],
        'params': {
            'playlistend': 2
        }
    }

    def _call_api(self, resource, resource_id):
        path = '/api/%ss' % resource
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com' + path, resource_id, query={
                'id[]': resource_id,
            }, headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            })[0]

    def _call_api1(self, resource, resource_id, query):
        path = '/api/%ss' % resource
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com' + path + f'?{query}', resource_id,
            headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            })

    def _real_extract(self, url):
        resource_id = self._match_id(url)
        if '/album/' in url:
            name = 'album'
        else:
            name = 'playlist'
        resources = self._call_api(name, resource_id)

        ids = resources.get('tracks', [])
        if ids:
            ids = [x['id'] for x in ids]
            query = '&'.join([f'id[]={x}' for x in ids])
        else:
            raise ExtractorError('Can`t get track ids')

        results = self._call_api1('track', resource_id, query)

        tracks = []
        for result in results:
            music_info = {
                '_type': 'url',
                'url': f"https://www.jamendo.com/track/{result['id']}",
                'ie_key': CustomJamendoIE.ie_key()
            }
            music_info.update(result)
            tracks.append(music_info)

        ie_result = self.playlist_result(tracks, query)
        ie_result.update({'is_next_page': False})
        # print(json.dumps(ie_result))
        return ie_result


class CustomJamendoRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/radios/(?P<id>[^/]+)'
    # '''https://www.jamendo.com/api/radios/planning?radioId=9&limit=1000'''

    def _call_api_radio(self, radio_id):
        path = '/api/radios/planning'
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com' + path, radio_id, query={
                'radioId': f'{radio_id}',
                'limit': '500'
            }, headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            })

    def _call_api(self, resource, resource_id):
        path = '/api/%ss' % resource
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com' + path, resource_id, query={
                'idstr[]': resource_id,
            }, headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            })[0]

    def _call_api_track(self, resource, resource_id, query):
        path = '/api/%ss' % resource
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com' + path + f'?{query}', resource_id,
            headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            })

    def _real_extract(self, url):
        current_time = int(time.time())
        radio_name = self._match_id(url)
        radio_base_info = self._call_api('radio', radio_name)

        radio_id = radio_base_info.get('id')
        if not radio_id:
            raise ExtractorError('Can`t get radio id')

        bulk_radios = self._call_api_radio(radio_id)
        current_track_id = None
        for radio in bulk_radios:
            if current_time in range(radio['datePlay'], radio['datePlay'] + (radio['duration'] // 1000) + 1):
                current_track_id = radio['trackId']
                break
        if current_track_id:
            query = f'id[]={current_track_id}'
        else:
            raise ExtractorError('Can`t get current_radio_id')

        results = self._call_api_track('track', current_track_id, query)

        tracks = []
        for result in results:
            music_info = {
                '_type': 'url',
                'url': f"https://www.jamendo.com/track/{result['id']}",
                'ie_key': CustomJamendoIE.ie_key()
            }
            music_info.update(result)
            tracks.append(music_info)

        ie_result = self.playlist_result(tracks, query)
        ie_result.update({'is_next_page': False})
        # print(json.dumps(ie_result))
        return ie_result


class CustomJamendoSearchIE(SearchInfoExtractor, InfoExtractor):
    IE_NAME = 'custom jamendo search'
    IE_DESC = 'custom jamendo search'
    # '''https://www.jamendo.com/search/tracks?q=linkin%20park'''
    _VALID_URL = r'https?://(?:www\.)?jamendo\.com/search/tracks\?(.*?&)?(?:q)=(?P<query>[^&]+)(?:[&]|$)'
    _SEARCH_KEY = 'custom jamendo search'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _call_api(self, resource, resource_id):
        path = '/api/%s' % resource
        rand = compat_str(random.random())
        return self._download_json(
            'https://www.jamendo.com/api/search?query={}'
            '&type=track&limit=100&identities=www'.format(resource_id),
            resource_id,
            headers={
                'X-Jam-Call': '$%s*%s~' % (hashlib.sha1((path + rand).encode()).hexdigest(), rand)
            }
        )

    def _real_extract(self, query):
        mobj = re.match(self._VALID_URL, query)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % query)
        query = mobj.group('query')
        results = self._call_api('search', query)

        tracks = []
        for result in results:
            music_info = {
                    '_type': 'url',
                    'url': f"https://www.jamendo.com/track/{result['id']}",
                    'ie_key': CustomJamendoIE.ie_key()
                }
            music_info.update(result)
            tracks.append(music_info)
        ie_result = self.playlist_result(tracks, query)
        ie_result.update({'is_next_page': False})
        # print(json.dumps(ie_result))
        return ie_result
