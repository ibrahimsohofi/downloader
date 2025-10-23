from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    str_to_int,
)


class CustomPornoXOIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?pornoxo\.com/videos/(?P<id>\d+)/(?P<display_id>[^/]+)/'
    _TEST = {
        'url': 'http://www.pornoxo.com/videos/7564/striptease-from-sexy-secretary.html',
        'md5': '582f28ecbaa9e6e24cb90f50f524ce87',
        'info_dict': {
            'id': '7564',
            'ext': 'flv',
            'title': 'Striptease From Sexy Secretary!',
            'display_id': 'striptease-from-sexy-secretary',
            'description': 'md5:0ee35252b685b3883f4a1d38332f9980',
            'categories': list,  # NSFW
            'thumbnail': r're:https?://.*\.jpg$',
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id, display_id = mobj.groups()

        webpage = self._download_webpage(url, video_id)
        video_data = {}

        title = self._html_search_regex(
            r'<title>([^<]+)\s*-\s*PornoXO', webpage, 'title')

        description = self._html_search_meta('description', webpage)

        thumbnail = self._html_search_meta('twitter:image', webpage)

        publishedAt = self._html_search_regex(
            r'''>Added(.*?)</div>''',
            webpage,
            'publishedAt'
        ).strip()

        duration = ''

        view_count = self._html_search_regex(
            r'''<div class="views-count-numbers">([^<]+)</div>''',
            webpage, 'view count', fatal=False)
        if view_count:
            view_count = str_to_int(view_count.split(' ')[0])

        sources = re.search(
            r'''sources: {mp4:(.*?)},\n''',
            webpage, re.S)
        try:
            sources = json.loads(sources.group(1))
        except:
            raise
        formats = []
        for source in sources:
            info = {
                'url': source['src'],
                'format_id': source['desc'],
                'height': int(source['desc'].strip('p')),
            }
            formats.append(info)
        self._sort_formats(formats)

        video_data.update({
            'id': video_id,
            'title': title,
            'display_id': display_id,
            'description': description,
            'publishedAt': publishedAt,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats
        })

        return video_data
