from __future__ import unicode_literals

import itertools
import re

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    extract_attributes,
    str_to_int,
)


class CustomPornOneIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornone\.com/(?P<name>[^/?#&]+)/(?P<display_id>[^/?#&]+)/(?P<id>\d+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        if not display_id:
            display_id = video_id

        webpage = self._download_webpage(url, display_id or video_id)
        description = self._html_search_meta(
            'description',
            webpage,
            'description'
        )
        title = self._html_search_regex(
            r'<title>(.*?)</title>',
            webpage,
            'title')
        thumbnail = self._html_search_regex(
            r'''poster="(.*?)"''',
            webpage,
            'thumbnail'
        ).strip()
        duration = self._html_search_regex(
            r'''alt="Video Duration">(.*?)</span>''',
            webpage,
            'duration'
        ).strip().split()
        duration = ':'.join(list(filter(lambda x: x.isdigit(), duration)))
        if duration.count(':') == 1:
            minute, second = duration.split(':')
            duration = (int(minute) * 60) + int(second)
        elif duration.count(':') == 2:
            hour, minute, second = duration.split(':')
            duration = (int(hour) * 3600) + (int(minute)) * 60 + int(second)
        else:
            if duration:
                duration = int(duration)
            else:
                duration = ''
        formats = []
        source_infos = re.findall(r'<source.*?>', webpage, re.S)
        size_infos = re.findall(r'<a class="size links noselect".*?Download">(.*?)</a>', webpage, re.S)
        for source_info, size_info in zip(source_infos, size_infos[::-1]):
            source_attr = extract_attributes(source_info)
            if source_attr['type'] == 'video/mp4':
                height = int(source_attr['res'])
                video_url = source_attr['src']
                format_id = source_attr['label']
                size_info = size_info.replace('&nbsp', '').strip()
                if 'Mb' in size_info:
                    size_info = size_info.strip('Mb')
                    size = float(size_info) * 1024 * 1024
                else:
                    if 'Gb' in size_info:
                        size_info = size_info.strip('Mb')
                        size = float(size_info) * 1024 * 1024 * 1024
                    else:
                        size = ''
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'height': height,
                    'filesize': size
                })
        self._remove_duplicate_formats(formats)
        self._sort_formats(formats)

        uploader = None
        upload_date = self._html_search_regex(
            r'''<img class="video-img" src=".*?" alt="Video Added" width="\d+" height="\d+">(.*?)</span>''',
            webpage,
            'upload date'
        ).strip()
        view_count = str_to_int(self._search_regex(
            r'''<span class="view-count">([^<]*)</span>''',
            webpage, 'view count', fatal=False).replace('views', '').strip())

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'publishedAt': upload_date,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats,
        }
