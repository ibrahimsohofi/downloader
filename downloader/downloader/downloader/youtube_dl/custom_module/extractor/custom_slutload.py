from __future__ import unicode_literals

import json
import re

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    urljoin,
    ExtractorError
)


class CustomSlutLoadLiveIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<host>(?:[^/]+\.)?slutload\.com)/(?P<id>[\da-z-]+)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None and '/media/' not in url and '/exclusive-videos/' not in url
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        channel_id = mobj.group('id')

        amf = self._download_json(
            f'https://www.slutload.com/api/v1/video/vtoken/{channel_id}', channel_id)

        index_m3u8 = f'https://{amf["edge_servers"][0]}/{amf["stream_name"]}_h264_aac_720p/index.m3u8?token={amf["token"]}'

        formats = self._extract_m3u8_formats(
            index_m3u8, channel_id, 'mp4', m3u8_id='hls', live=True)
        self._sort_formats(formats)

        webpage = self._download_webpage(url, channel_id)

        title = self._html_search_regex(
            r'<title data-rh="true">(.*?)</title>',
            webpage,
            'title'
        ).strip()
        description = self._html_search_meta(r'description', webpage, 'description')
        thumbnail = self._html_search_meta(r'og:image', webpage, 'og:image')
        thumbnail = urljoin('https:', thumbnail)

        return {
            'id': channel_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'age_limit': 18,
            'is_live': True,
            'formats': formats,
        }


class CustomSlutLoadMediaIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<host>(?:[^/]+\.)?slutload\.com)/media/(?P<user_name>[^/?#&]+)/(?P<display_id>[^/?#&]+)/(?P<id>[^/?&#]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')
        media_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        preload = re.search(r'window.__PRELOADED_STATE__ = (.+?)\n*</script>', webpage, re.DOTALL).group(1)
        preload = json.loads(preload)
        media = preload['media']['byId'][media_id]
        title = media['name']
        description = self._html_search_meta(r'description', webpage, 'description') or media['description']
        thumbnail = media['thumbnail_url']
        duration = media['duration']
        publishAt = media['created_at'].split()[0]

        if media.get('items') is None:
            raise ExtractorError('Can`t get video, maybe require login!')

        formats = [
            {
                'url': media['items'][0]['url'],
                'ext': 'mp4',
                'protocol': 'https'
            }
        ]

        return {
            'id': media_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'publishAt': publishAt,
            'formats': formats,
        }


class CustomSlutLoadVideoIE(InfoExtractor):
    _VALID_URL = r'https?://(?P<host>(?:[^/]+\.)?slutload\.com)/exclusive-videos/(?P<display_id>[^/?#&]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        preload = re.search(r'window.__PRELOADED_STATE__ = (.+?)\n*</script>', webpage, re.DOTALL).group(1)
        preload = json.loads(preload)
        medias = preload['exclusiveVideos']['videoList']
        media = [x for x in medias if x['id'] == display_id]
        if not media:
            raise ExtractorError('Can`t get video, maybe require login!')
        else:
            media = media[0]
        title = media['title']
        description = self._html_search_meta(r'description', webpage, 'description') or media['desc']
        thumbnail = media['thumb_name']

        formats = [
            {
                'url': media['video_name'],
                'ext': 'mp4',
                'protocol': 'https'
            }
        ]

        return {
            'id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'age_limit': 18,
            'formats': formats,
        }