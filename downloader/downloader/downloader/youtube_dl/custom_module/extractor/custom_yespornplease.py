from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError,
    str_to_int
)


class CustomYesPornPleaseIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?yespornplease\.to/en(?:2|4)/v/(?P<id>\d+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_data = {}

        title = self._html_search_regex(
            r'<title>(.*?)</title>',
            webpage, 'title', default='') or \
            self._html_search_meta('description', webpage)

        description = self._html_search_meta('description', webpage)

        thumbnail = self._html_search_regex(
            r'poster="(.*?)"', webpage, 'thumbnail')

        duration = ''

        view_count = self._html_search_regex(
            r'''<span class="view-count">(.*?)</span>''',
            webpage, 'view count', default='')
        if view_count:
            view_count = str_to_int(view_count.strip('views'))

        video_url = self._html_search_regex(
            r'''<source src="(.*?)"''', webpage, 'video_url', default=''
        )
        if not video_url:
            raise ExtractorError('Could`t found video url!')
        formats = []
        info = {
            'url': video_url,
            'protocol': 'https',
            'ext': 'mp4'
        }
        formats.append(info)

        video_data.update({
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats
        })

        return video_data
