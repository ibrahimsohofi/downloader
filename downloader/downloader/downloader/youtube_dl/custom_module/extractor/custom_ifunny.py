from __future__ import unicode_literals

import re
import datetime
from youtube_dl.extractor.common import InfoExtractor


class CustomIfunnyIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?ifunny\.co/(?:video|gif)/(?P<slug>[\dA-Za-z\-]*)?(?P<id>[\da-zA-Z]{9})'
    _TESTS = [
        {
            'url': 'https://ifunny.co/video/introduce-you-to-the-fly-swatter-jh6D3QSz7',
            'md5': '77108c1e4ab58f48031101a1a2119789',
            'info_dict': {
                'id': '0C0CNNNU',
                'ext': 'mp4',
                'title': 'Woman at the well.',
                'duration': 159,
                'timestamp': 1205712000,
                'uploader': 'beverlybmusic',
                'upload_date': '20080317',
                'thumbnail': r're:^https?://.*\.jpg$',
            },
        },
    ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)

        info = self._search_json_ld(webpage, video_id, default={})
        title = self._html_search_meta('og:title', webpage, 'title')
        description = info.get('description', '')
        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail', default='')
        publishedAt = datetime.datetime.fromtimestamp(info['timestamp']).strftime('%Y-%m-%d')

        height = self._html_search_meta('og:video:height', webpage, 'video_url')
        video_info = {
            'url': info.get('url') or self._html_search_meta('og:video:url', webpage, 'video_url'),
            'ext': 'mp4'
        }
        if height:
            height = int(height)
            video_info.update({
                'format_id': '%sp' % height,
                'height': height
            })

        formats = [video_info]

        return {
            'id': video_id,
            'title': title,
            'duration': '',
            'description': description,
            'publishedAt': publishedAt,
            'thumbnail': thumbnail,
            'formats': formats,
        }
