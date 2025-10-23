# coding: utf-8
from __future__ import unicode_literals

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import int_or_none
import json


class CustomToypicsIE(InfoExtractor):
    IE_DESC = 'custom Toypics video'
    _VALID_URL = r'https?://videos\.toypics\.net/view/(?P<id>[0-9]+)'
    _TEST = {
        'url': 'http://videos.toypics.net/view/514/chancebulged,-2-1/',
        'md5': '16e806ad6d6f58079d210fe30985e08b',
        'info_dict': {
            'id': '514',
            'ext': 'mp4',
            'title': "Chance-Bulge'd, 2",
            'age_limit': 18,
            'uploader': 'kidsune',
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        formats = self._parse_html5_media_entries(
            url, webpage, video_id)[0]['formats']
        title = self._html_search_regex([
            r'<h1[^>]+class=["\']view-video-title[^>]+>([^<]+)</h',
            r'<title>([^<]+) - Toypics</title>',
        ], webpage, 'title')

        description = self._html_search_meta('description', webpage,
                                             'description') or ''

        thumbnail = self._html_search_regex(
            r'<link rel="thumbnail" href="(.*?)"',
            webpage, 'thumbnail'
        )

        duration = self._html_search_regex(
            r'''</span> Length:<strong>(.*?)</strong>''',
            webpage,
            'duration'
        ).strip()
        if duration.count(':') == 1:
            minute, second = duration.split(':')
            duration = int(minute) * 60 + int(second)
        elif duration.count(':') == 2:
            hour, minute, second = duration.split(':')
            duration = int(hour) * 3600 + int(minute) * 60 + int(second)
        else:
            raise
        view_count = int_or_none(self._html_search_regex(
            r'''aria-valuenow="(.*?)"''', webpage, 'views'
        ))

        publishedAt = self._html_search_regex(
            r'''<span class="glyphicon glyphicon-upload"></span>Added on (.*?)</strong>''',
            webpage,
            'publishedAt'
        )

        height = int_or_none(self._html_search_meta(
            'video_height', webpage, 'video_height'))

        if len(formats) == 1:
            formats[0]['height'] = height

        uploader = self._html_search_regex(
            r'More videos from <strong>([^<]+)</strong>', webpage, 'uploader',
            fatal=False)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'uploader': uploader,
            'age_limit': 18,
        }
