from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
)


class CustomNwkingsIE(InfoExtractor):
    'https://learn.nwkings.com/s/courses/5c71a1a0e4b008639095c8d6/take'
    IE_NAME = 'custom nwkings'
    _VALID_URL = r'https?://(?:learn\.|www\.)?nwkings\.com/s/courses/(?P<name>[^/]+)(?:/take)?'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        webpage = self._download_webpage(
            url,
            'request_url',
            headers={
                'cookie': 'id=e047a0f7-03a7-4b80-bda6-674755557216; _ga=GA1.2.675608873.1600846294; JSESSIONID=8629BA99E0CBC396F9D25C2E94974DE5; c_user=fee0e41b7b8c0f75ea3bdd2cf7336038vAa18CZIrr3zTT2n3zmK0EQ8JchdU0i6CORaAVXJgUE=52ba78209deb1e773a4b95f40d9dd245; c_p=749bed1f5779154c2cd28667927643b1BFHE/kb9Ns9DiyXDb9IyGg==24204c03c2e87ca7c661cc78aaa01070; _fbp=fb.1.1601012430448.258092748; _gid=GA1.2.419863781.1601012459; _gat=1'
            }
        )
        items = self._html_search_regex(r'<div')

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
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
            'duration': duration,
            'publishedAt': publishedAt,
            'player': player,
            'formats': formats
        }
        print(json.dumps(info))
