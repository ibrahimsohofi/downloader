from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError,
    str_to_int
)


class CustomPornGoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?porngo\.com/videos/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_data = {}

        title = self._html_search_regex(
            r'<title>(.*?)</title>',
            webpage, 'title', default='') or \
            self._html_search_meta('og:title', webpage)

        description = self._html_search_meta('description', webpage)

        thumbnail = self._html_search_regex(
            r"poster='(.*?)'", webpage, 'thumbnail'
        )

        duration = ''

        view_count = self._html_search_regex(
            r'''<span class="video-info__text">(.*?)</span>''',
            webpage, 'view count', default='')
        if view_count:
            view_count = str_to_int(view_count.strip('views'))

        videos = re.findall(
            '''<div class="video-links__list video-links__list_tags">(.*?)</div>''',
            webpage, re.S
        )
        if videos:
            videos = videos[-1]
        else:
            raise ExtractorError('Could`t found video url!')
        links = re.findall('''<a class="video-links__link"(.*?)</a>''', videos, re.S)
        formats = []
        for link in links:
            video_url = self._html_search_regex(
                r'''href="(.*?)"''',
                link, 'video_url', default=''
            )
            height_size = link.split('no-load-content>')[-1]
            height = int(height_size.split(' ')[0].strip('p'))
            size = re.search(r'\((.*?)\)', height_size)
            size = size.group(1)
            if 'Mb' in size:
                size = size.split(' ')[0]
                size = float(size) * 1024 * 1024
            elif 'Gb' in size:
                size = size.split(' ')[0]
                size = float(size) * 1024 * 1024 * 1024
            info = {
                'url': video_url,
                'protocol': 'https',
                'ext': 'mp4',
                'height': height,
                'filesize': size
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
