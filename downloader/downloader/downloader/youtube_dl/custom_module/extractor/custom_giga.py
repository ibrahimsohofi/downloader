# coding: utf-8
from __future__ import unicode_literals


from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import ExtractorError
import datetime


class CustomGigaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?giga\.de/(?:[^/]+/)*(?P<id>[^/]+)'
    _TESTS = [{
        'url': 'http://www.giga.de/filme/anime-awesome/trailer/anime-awesome-chihiros-reise-ins-zauberland-das-beste-kommt-zum-schluss/',
        'md5': '6bc5535e945e724640664632055a584f',
        'info_dict': {
            'id': '2622086',
            'display_id': 'anime-awesome-chihiros-reise-ins-zauberland-das-beste-kommt-zum-schluss',
            'ext': 'mp4',
            'title': 'Anime Awesome: Chihiros Reise ins Zauberland – Das Beste kommt zum Schluss',
            'description': 'md5:afdf5862241aded4718a30dff6a57baf',
            'thumbnail': r're:^https?://.*\.jpg$',
            'duration': 578,
            'timestamp': 1414749706,
            'upload_date': '20141031',
            'uploader': 'Robin Schweiger',
            'view_count': int,
        },
    }, {
        'url': 'http://www.giga.de/games/channel/giga-top-montag/giga-topmontag-die-besten-serien-2014/',
        'only_matching': True,
    }, {
        'url': 'http://www.giga.de/extra/netzkultur/videos/giga-games-tom-mats-robin-werden-eigene-wege-gehen-eine-ankuendigung/',
        'only_matching': True,
    }, {
        'url': 'http://www.giga.de/tv/jonas-liest-spieletitel-eingedeutscht-episode-2/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        info = self._search_json_ld(webpage, display_id, default={})

        if not info.get('url'):
            raise ExtractorError('not found info json_ld')
        title = info['title']
        description = info['description']
        thumbnail = info['thumbnail']

        duration = info['duration']

        publishedAt = datetime.datetime.fromtimestamp(info['timestamp']).strftime('%Y-%m-%d')

        format_id = info['url'].split('/')[-1].split('.')[0]

        video_info = {
            'url': info['url'],
            'format_id': format_id,
            'height': int(format_id.strip('p')),
            'ext': 'mp4'
        }
        formats = [video_info]

        return {
            'id': display_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'publishedAt': publishedAt,
            'formats': formats,
        }
