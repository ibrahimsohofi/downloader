from __future__ import unicode_literals

import re

from youtube_dl.utils import (
    int_or_none,
    str_to_int,
)
from youtube_dl.extractor.keezmovies import KeezMoviesIE


class CustomTube8IE(KeezMoviesIE):
    _VALID_URL = r'https?://(?:www\.)?tube8\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/(?P<id>\d+)'
    _TESTS = [{
        'url': 'http://www.tube8.com/teen/kasia-music-video/229795/',
        'md5': '65e20c48e6abff62ed0c3965fff13a39',
        'info_dict': {
            'id': '229795',
            'display_id': 'kasia-music-video',
            'ext': 'mp4',
            'description': 'hot teen Kasia grinding',
            'uploader': 'unknown',
            'title': 'Kasia music video',
            'age_limit': 18,
            'duration': 230,
            'categories': ['Teen'],
            'tags': ['dancing'],
        },
    }, {
        'url': 'http://www.tube8.com/shemale/teen/blonde-cd-gets-kidnapped-by-two-blacks-and-punished-for-being-a-slutty-girl/19569151/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+\bsrc=["\']((?:https?:)?//(?:www\.)?tube8\.com/embed/(?:[^/]+/)+\d+)',
            webpage)

    def _real_extract(self, url):
        webpage, info = self._extract_info(url)

        if not info['title']:
            info['title'] = self._html_search_regex(
                'og:title', webpage, 'og:title')

        description = self._html_search_meta(
            'og:description', webpage, 'og:description')

        view_count = str_to_int(self._search_regex(
            r'Views:\s*</dt>\s*<dd>([\d,\.]+)',
            webpage, 'view count', fatal=False))

        publishedAt = self._html_search_regex(
            '"datePublished": "(.*?)"',
            webpage,
            'publishedAt'
        )
        if publishedAt:
            publishedAt = publishedAt.split('T')[0]

        info.update({
            'description': description,
            'view_count': view_count,
            'publishedAt': publishedAt
        })

        return info
