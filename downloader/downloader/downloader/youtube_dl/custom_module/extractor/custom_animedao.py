from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
)


class CustomAnimedaoIE(InfoExtractor):
    IE_NAME = 'custom animedao'
    _VALID_URL1 = r'https?://(?:www\.)?animedao(?:\d+)?\.(?:com|to)/watch-online/(?P<name>[^\.]+)'
    _VALID_URL2 = r'https?://(?:www\.)?animedao(?:\d+)?\.(?:stream|to)/view/(?P<id>[^/]+)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or re.match(cls._VALID_URL2, url) is not None
        return rs

    def _real_extract(self, url):
        webpage = self._download_webpage(url, 'request_url')
        domain = url.split('/')[2]

        title = self._html_search_regex(r'<h2 class="page_title">(.*?)</h2>', webpage, 'title').strip()
        description = self._html_search_regex(r'<h4>(.*?)</h4>', webpage, 'description', default='') or \
                      self._html_search_meta(r'description', webpage, 'description')
        view_count = ''
        thumbnail = self._html_search_regex(
            r'data-src="(.*?)" alt=".*?" height=".*?" class="lozad hidden-xs"', webpage, 'real_url')
        thumbnail = f'https://{domain}{thumbnail}'
        duration = ''
        publishedAt = ''

        video_url = self._html_search_regex(r"src: '(.*?)',", webpage, 'video_url')
        video_url = f'https://{domain}{video_url}'
        height = parse_count(self._html_search_regex(r"size: (.*?),", webpage, 'video_url'))

        video_info = {
            'url': video_url,
            'format_id': '%sp' % height,
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
