# coding: utf-8
from __future__ import unicode_literals

import re
import datetime
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError
)


class CustomPornFlipIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornflip\.com/(?P<id>\w+)(?:/(?P<display_id>[^/?#&]+))?'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        json_ld = self._search_json_ld(webpage, display_id, default={})

        title = json_ld['title']

        duration = json_ld.get('duration')
        view_count = json_ld.get('view_count')

        publishedAt = datetime.datetime.fromtimestamp(json_ld['timestamp']).strftime('%Y-%m-%d')
        description = json_ld.get('description')
        thumbnail = self._html_search_meta(r'og:image', webpage, default='')

        formats = []
        if 'data-hls-src' in webpage:
            p240 = self._html_search_regex(r'data-hls-src240="(.*?)"', webpage, '240p', default='')
            p360 = self._html_search_regex(r'data-hls-src360="(.*?)"', webpage, '360p', default='')
            p480 = self._html_search_regex(r'data-hls-src480="(.*?)"', webpage, '480p', default='')
            p720 = self._html_search_regex(r'data-hls-src720="(.*?)"', webpage, '720p', default='')
            p1080 = self._html_search_regex(r'data-hls-src1080="(.*?)"', webpage, '1080p', default='')
            p1440 = self._html_search_regex(r'data-hls-src1440="(.*?)"', webpage, '1440p', default='')
            p2160 = self._html_search_regex(r'data-hls-src2160="(.*?)"', webpage, '2160p', default='')
            for (p, h) in zip((p240, p360, p480, p720, p1080, p1440, p2160), (240, 360, 480, 720, 1080, 1440, 2160)):
                if p:
                    formats.append({
                        'url': p,
                        'protocol': 'm3u8',
                        'ext': 'mp4',
                        'height': h,
                    })

        else:
            raise ExtractorError('Can`t found video format!')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'duration': duration,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'thumbnail': thumbnail,
            'formats': formats,
            'age_limit': 18,
            'player': f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.pornflip.com/embed/{video_id}"></iframe>'
        }
