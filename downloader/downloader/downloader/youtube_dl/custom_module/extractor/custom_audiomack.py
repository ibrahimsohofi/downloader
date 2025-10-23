# coding: utf-8
from __future__ import unicode_literals

import itertools
import time
import re
# import json

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.extractor.soundcloud import SoundcloudIE
from youtube_dl.compat import compat_str
from youtube_dl.utils import (
    ExtractorError,
    url_basename,
)


class CustomAudiomackIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/(?:[^&]+\/)?song/(?P<id>[\w/-]+)'
    IE_NAME = 'custom audiomack'
    _TESTS = [
        # hosted on audiomack
        {
            'url': 'http://www.audiomack.com/song/roosh-williams/extraordinary',
            'info_dict':
            {
                'id': '310086',
                'ext': 'mp3',
                'uploader': 'Roosh Williams',
                'title': 'Extraordinary'
            }
        },
        # audiomack wrapper around soundcloud song
        {
            'add_ie': ['Soundcloud'],
            'url': 'http://www.audiomack.com/song/hip-hop-daily/black-mamba-freestyle',
            'info_dict': {
                'id': '258901379',
                'ext': 'mp3',
                'description': 'mamba day freestyle for the legend Kobe Bryant ',
                'title': 'Black Mamba Freestyle [Prod. By Danny Wolf]',
                'uploader': 'ILOVEMAKONNEN',
                'upload_date': '20160414',
            }
        },
    ]

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        # URLs end with [uploader name]/[uploader title]
        # this title is whatever the user types in, and is rarely
        # the proper song title.  Real metadata is in the api response
        album_url_tag = self._match_id(url)

        if 'audiomack.com/song/' not in url:
            url_split = url.split('/')
            album_url_tag = '{}/{}'.format(url_split[-3], url_split[-1])
        # Request the extended version of the api for extra fields like artist and title
        api_response = self._download_json(
            'http://www.audiomack.com/api/music/url/song/%s?extended=1&_=%d' % (
                album_url_tag, time.time()),
            album_url_tag)

        # API is inconsistent with errors
        if 'url' not in api_response or not api_response['url'] or 'error' in api_response:
            raise ExtractorError('Invalid url %s' % url)

        # Audiomack wraps a lot of soundcloud tracks in their branded wrapper
        # if so, pass the work off to the soundcloud extractor
        if SoundcloudIE.suitable(api_response['url']):
            return self.url_result(api_response['url'], SoundcloudIE.ie_key())

        return {
            'id': compat_str(api_response.get('id', album_url_tag)),
            'uploader': api_response.get('artist'),
            'title': api_response.get('title'),
            'url': api_response['url'],
        }


class CustomAudiomackAlbumIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?audiomack\.com/album/(?P<id>[\w/-]+)'
    _VALID_URL1 = r'https?://(?:www\.)?audiomack\.com/(?P<album_name>[\w/-]+)/album/(?P<song_name>[\w/-]+)'
    IE_NAME = 'custom audiomack:album'
    _TESTS = [
        # Standard album playlist
        {
            'url': 'http://www.audiomack.com/album/flytunezcom/tha-tour-part-2-mixtape',
            'playlist_count': 15,
            'info_dict':
            {
                'id': '812251',
                'title': 'Tha Tour: Part 2 (Official Mixtape)'
            }
        },
        # Album playlist ripped from fakeshoredrive with no metadata
        {
            'url': 'http://www.audiomack.com/album/fakeshoredrive/ppp-pistol-p-project',
            'info_dict': {
                'title': 'PPP (Pistol P Project)',
                'id': '837572',
            },
            'playlist': [{
                'info_dict': {
                    'title': 'PPP (Pistol P Project) - 9. Heaven or Hell (CHIMACA) ft Zuse (prod by DJ FU)',
                    'id': '837577',
                    'ext': 'mp3',
                    'uploader': 'Lil Herb a.k.a. G Herbo',
                }
            }],
            'params': {
                'playliststart': 9,
                'playlistend': 9,
            }
        }
    ]

    def _match_id1(self, url):
        self._VALID_URL_RE = re.compile(self._VALID_URL1)
        m1 = self._VALID_URL_RE.match(url)
        assert m1
        return compat_str(f"{m1.group('album_name')}/{m1.group('song_name')}")

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None or re.match(cls._VALID_URL1, url) is not None
        return rs

    def _real_extract(self, url):
        # URLs end with [uploader name]/[uploader title]
        # this title is whatever the user types in, and is rarely
        # the proper song title.  Real metadata is in the api response
        if re.match(self._VALID_URL, url) is not None:
            album_url_tag = self._match_id(url)
        else:
            album_url_tag = self._match_id1(url)
        artist = album_url_tag.split('/')[0]
        thumbnail_request_url = f'https://audiomack.com/oembed?url={url}'
        page_info = self._download_json(
            thumbnail_request_url, album_url_tag
        )
        thumbnail = page_info.get('thumbnail_url', '')
        result = {'_type': 'playlist', 'entries': []}
        # There is no one endpoint for album metadata - instead it is included/repeated in each song's metadata
        # Therefore we don't know how many songs the album has and must infi-loop until failure
        for track_no in itertools.count():
            # Get song's metadata
            api_response = self._download_json(
                'http://www.audiomack.com/api/music/url/album/%s/%d?extended=1&_=%d'
                % (album_url_tag, track_no, time.time()), album_url_tag,
                note='Querying song information (%d)' % (track_no + 1))

            # Total failure, only occurs when url is totally wrong
            # Won't happen in middle of valid playlist (next case)
            if 'url' not in api_response or 'error' in api_response:
                raise ExtractorError('Invalid url for track %d of album url %s' % (track_no, url))
            # URL is good but song id doesn't exist - usually means end of playlist
            elif not api_response['url']:
                break
            else:
                # Pull out the album metadata and add to result (if it exists)
                for resultkey, apikey in [('id', 'album_id'), ('title', 'album_title')]:
                    if apikey in api_response and resultkey not in result:
                        result[resultkey] = api_response[apikey]
                song_id = url_basename(api_response['url']).rpartition('.')[0]
                song_id = song_id.replace('.', '')
                while 1:
                    if song_id.endswith('-'):
                        song_id = song_id[:-1]
                    else:
                        break
                web_url = f'https://audiomack.com/{artist}/song/{song_id}'
                result['entries'].append({
                    'id': compat_str(api_response.get('id', song_id)),
                    'uploader': api_response.get('artist'),
                    'title': api_response.get('title', song_id),
                    'url': web_url,
                    'download_url': api_response['url'],
                    'thumbnail': thumbnail,
                    'player': f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://audiomack.com/embed/song/{artist}/{song_id}?background=1&color=57bb6e"></iframe>'
                })
        # print(json.dumps(result))
        return result
