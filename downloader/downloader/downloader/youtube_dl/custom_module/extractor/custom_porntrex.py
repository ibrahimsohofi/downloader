# coding: utf-8
from __future__ import unicode_literals

import json
import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError,
    urljoin
)


class CustomPornTrexIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?:porntrex|whoreshub)\.com/videos?/(?P<id>\d+)/(?:(?P<display_id>[^/?#&]+))?'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id') or video_id

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_meta('og:title', webpage, 'title', default='')

        duration = self._html_search_regex(
            r'<div class="durations"><i class="fa fa-clock-o"></i>(.*?)</div>',
            webpage, 'duration', default=''
        ).strip()
        if duration:
            duration_parts = duration.split(':')
            if len(duration_parts) == 2:
                mins, seconds = duration_parts
                mins, seconds = int(mins) * 60, int(seconds)
                duration = mins + seconds
            else:
                hours, mins, seconds = duration_parts
                hours, mins, seconds = int(hours) * 3600, int(
                    mins) * 60, int(seconds)
                duration = hours + mins + seconds
        view_count = self._html_search_regex(
            r'<div class="viewsthumb">(.*?)</div>',
            webpage, 'view_count', default=''
        ).replace(' views', '').replace(' ', '')

        publishedAt = self._html_search_regex(
            r'<span><i class="fa fa-calendar"></i>\s*<em class="badge">(.*?)</em></span>',
            webpage, 'publishedAt', default=None
        )
        description = self._html_search_meta('description', webpage, 'description', default='')
        thumbnail = self._html_search_meta(r'og:image', webpage, 'thumbnail', default='')
        thumbnail = urljoin('https://', thumbnail)

        flashvars = re.search(r'var\s+flashvars\s*=\s*({.+?});', webpage, re.DOTALL)
        if flashvars:
            video_var = flashvars.group(1).replace('\n', '').replace('\t', '')
        else:
            raise ExtractorError('Can`t found video format!')

        formats = []
        if 'video_url' in video_var:
            p360 = self._html_search_regex(r"video_url: '(.*?)',", webpage, '360p', default='').replace('function/0/', '')
            p480 = self._html_search_regex(r"video_alt_url: '(.*?)',", webpage, '480p', default='').replace('function/0/', '')
            p720 = self._html_search_regex(r"video_alt_url2: '(.*?)',", webpage, '720p', default='').replace('function/0/', '')
            p1080 = self._html_search_regex(r"video_alt_url3: '(.*?)',", webpage, '1080p', default='').replace('function/0/', '')
            p1440 = self._html_search_regex(r"video_alt_url4: '(.*?)',", webpage, '1440p', default='').replace('function/0/', '')
            p2160 = self._html_search_regex(r"video_alt_url5: '(.*?)',", webpage, '2160p', default='').replace('function/0/', '')
            for (p, h) in zip((p360, p480, p720, p1080, p1440, p2160), (360, 480, 720, 1080, 1440, 2160)):
                if p:
                    formats.append({
                        'url': p,
                        'protocol': 'https',
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
            'player': f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.{"porntrex" if "porntrex" in url else "whoreshub"}.com/embed/{video_id}"></iframe>'
        }
