from __future__ import unicode_literals

import re

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    determine_ext,
    int_or_none,
    parse_duration,
    url_or_none,
)


class CustomYouJizzIE(InfoExtractor):
    _VALID_URL = r'https?://(?:\w+\.)?youjizz\.com/videos/(?:[^/#?]*-(?P<id>\d+)\.html|embed/(?P<embed_id>\d+))'
    _TESTS = [{
        'url': 'http://www.youjizz.com/videos/zeichentrick-1-2189178.html',
        'md5': 'b1e1dfaa8bb9537d8b84eeda9cf4acf4',
        'info_dict': {
            'id': '2189178',
            'ext': 'mp4',
            'title': 'Zeichentrick 1',
            'age_limit': 18,
            'duration': 2874,
        }
    }, {
        'url': 'http://www.youjizz.com/videos/-2189178.html',
        'only_matching': True,
    }, {
        'url': 'https://www.youjizz.com/videos/embed/31991001',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('embed_id')

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title')
        description = self._html_search_meta('og:description', webpage, 'og:description')
        thumbnail = self._html_search_meta('og:image', webpage, 'og:image')
        formats = []

        encodings = self._parse_json(
            self._search_regex(
                r'[Ee]ncodings\s*=\s*(\[.+?\]);\n', webpage, 'encodings',
                default='[]'),
            video_id, fatal=False)
        for encoding in encodings:
            if not isinstance(encoding, dict):
                continue
            format_url = url_or_none(encoding.get('filename'))
            if not format_url:
                continue
            if determine_ext(format_url) == 'mp4':
                format_id = encoding.get('name') or encoding.get('quality')
                height = int_or_none(self._search_regex(
                    r'^(\d+)[pP]', format_id, 'height', default=None))
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'height': height,
                })

        if formats:
            info_dict = {
                'formats': formats,
            }
        else:
            # YouJizz's HTML5 player has invalid HTML
            webpage = webpage.replace('"controls', '" controls')
            info_dict = self._parse_html5_media_entries(
                url, webpage, video_id)[0]

        duration = parse_duration(self._search_regex(
            r'<strong data-i18n="video.videotime.runtime">Runtime:</strong>([^<]+)', webpage, 'duration',
            default=None))
        view_count = self._html_search_regex(
            r'''data-views="(.*?)"''',
            webpage,
            'view_count',
            default=None
        )
        if view_count:
            view_count = int(view_count)
        publishedAt = self._html_search_regex(
            [
                r'''<span class="pretty-date">(.*?)</span>''',
                r"new Date\('(.*?)'\)",
            ],
            webpage,
            'publishedAt'
        )
        uploader = None

        info_dict.update({
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'age_limit': self._rta_search(webpage),
            'duration': duration,
            'uploader': uploader,
        })

        return info_dict
