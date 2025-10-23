from __future__ import unicode_literals

import re

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_duration,
    int_or_none,
)


class CustomSunPornoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www\.)?sunporno\.com/videos|embeds\.sunporno\.com/embed)/(?P<id>\d+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'http://www.sunporno.com/videos/%s' % video_id, video_id)

        title = self._html_search_regex(
            r'<title>([^<]+)</title>', webpage, 'title')
        description = self._html_search_regex(
            r'<span itemprop="description".*?>(.*?)</span>', webpage,
            'description')
        thumbnail = self._html_search_regex(
            r'poster="([^"]+)"', webpage, 'thumbnail', fatal=False)

        duration = parse_duration(self._search_regex(
            (r'itemprop="duration"[^>]*>\s*(\d+:\d+)\s*<',
             r'>Duration:\s*<span[^>]+>\s*(\d+:\d+)\s*<'),
            webpage, 'duration', fatal=False))

        view_count = int_or_none(self._html_search_regex(
            r'class="views">(?:<noscript>)?\s*(\d+)\s*<',
            webpage, 'view count', fatal=False))

        publishedAt = self._html_search_regex(
            r'''<span itemprop="uploadDate">(.*?)</span>''',
            webpage,
            'publishedAt'
        )

        formats = []
        video_url = self._html_search_regex(
            r"video_url: '(.*?)',",
            webpage,
            'video_url'
        )
        size = self._html_search_regex(
            r'''data-size="(.*?)"''',
            webpage,
            'size'
        )
        size = int(size.split(',')[0]) * 1024 * 1024
        formats.append({
            'url': video_url + '&amoysharetype={"headers": {"referer": "%s"}}' % url,
            'format_id': '720p',
            'height': 720,
            'ext': 'mp4',
            'filesize': size
        })
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'formats': formats,
            'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://embeds.sunporno.com/embed/{}"></iframe>'.format(
                video_id),
            'age_limit': 18,
        }
