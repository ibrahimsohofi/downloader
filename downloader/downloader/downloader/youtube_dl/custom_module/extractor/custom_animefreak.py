from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
    ExtractorError
)


class CustomAnimefreakIE(InfoExtractor):
    IE_NAME = 'custom animefreak'
    _VALID_URL = r'https?://(?:www\.)?animefreak\.tv/watch/(?P<name>[^/]+)/episode/(?P<detai_name>[^/]+)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)

        title = self._html_search_regex(r'<h1>(.*?)</h1>', webpage, 'title')
        description = self._html_search_meta(r'description', webpage, 'description')
        view_count = ''
        thumbnail = re.findall(r'<img src="(.*?)">', webpage)[-1]
        duration = ''
        publishedAt = self._html_search_regex(r'Date aired : <span>(.*?)</span>', webpage, 'publishedAt')

        video_url = self._html_search_regex(r'var file = "(.*?)";', webpage, 'video url')
        height = 720
        video_info = {
            'url': video_url,
            'format_id': '%dp' % height,
            'height': height,
            'ext': 'mp4'
        }
        formats = [video_info]
        player = '<video controls="" autoplay="" name="media" ' \
                 'width="100%" height="100%">' \
                 '<source src="{}" type="video/mp4"></video>'.format(video_url)
        info = {
            'id': title,
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
            'duration': duration,
            'publishedAt': publishedAt,
            'player': player,
            'formats': formats
        }
        # print(json.dumps(info))
        return info
