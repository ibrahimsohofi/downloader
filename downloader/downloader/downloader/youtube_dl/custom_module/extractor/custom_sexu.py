from __future__ import unicode_literals

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import int_or_none
import re


class CustomSexuIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?sexu\.com/(?P<id>\d+)'
    _TEST = {
        'url': 'http://sexu.com/961791/',
        'md5': 'ff615aca9691053c94f8f10d96cd7884',
        'info_dict': {
            'id': '961791',
            'ext': 'mp4',
            'title': 'md5:4d05a19a5fc049a63dbbaf05fb71d91b',
            'description': 'md5:2b75327061310a3afb3fbd7d09e2e403',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_url = self._html_search_meta(
            'og:video:url',
            webpage,
            'og:video:url'
        )
        if not video_url.startswith(('https', 'http')):
            video_url = 'https:' + video_url
        ext_info = video_url.split('/')[-1].split('.')[0].split('-')
        format_id = ext_info[1]
        height = int(format_id.strip('p'))
        formats = [
            {
                'url': video_url,
                'format_id': format_id,
                'height': height
            }
        ]

        title = self._html_search_regex(
            r'<title>(.*?)</title>',
            webpage,
            'title')

        description = self._html_search_meta(
            'description', webpage, 'description')

        thumbnail = self._html_search_meta(
            'og:image',
            webpage,
            'og:image'
        )

        if not thumbnail.startswith(('https', 'http')):
            thumbnail = 'https:' + thumbnail

        duration = int_or_none(self._html_search_meta(
            'video:duration',
            webpage,
            'video:duration'
        ))
        view_count = self._html_search_regex(
            r'''var sum_type = (.*?);''',
            webpage,
            'views'
        )
        view_count = re.search(r'\d+', view_count)
        if view_count:
            view_count = int(view_count.group())
        else:
            view_count = ''
        uploader = None
        upload_date = self._html_search_regex(
            r'''<div class="player-block__date">(.*?)</div>''',
            webpage,
            'upload date'
        ).strip()

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'uploader': uploader,
            'publishedAt': upload_date,
            'formats': formats,
            'age_limit': 18,
        }
