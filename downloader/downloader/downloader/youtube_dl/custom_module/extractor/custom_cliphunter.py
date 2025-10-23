from __future__ import unicode_literals

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
    int_or_none,
    url_or_none,
)


class CustomCliphunterIE(InfoExtractor):
    IE_NAME = 'custom cliphunter'

    _VALID_URL = r'''(?x)https?://(?:www\.)?cliphunter\.com/w/
        (?P<id>[0-9]+)/
        (?P<seo>.+?)(?:$|[#\?])
    '''

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        video_title = self._search_regex(
            r'mediaTitle = "([^"]+)"', webpage, 'title')
        description = self._html_search_meta('description', webpage, 'description')
        duration = int(self._html_search_meta(
            'og:video:duration', webpage,
            'og:video:duration'))
        view_count = parse_count(self._html_search_regex(
            'noseo="(.*?)<span>views</span>"></div>', webpage, 'view_count'
        ))

        gexo_files = self._parse_json(
            self._search_regex(
                r'var\s+gexoFiles\s*=\s*({.+?});', webpage, 'gexo files'),
            video_id)

        formats = []
        for format_id, f in gexo_files.items():
            video_url = url_or_none(f.get('url'))
            if not video_url:
                continue
            fmt = f.get('fmt')
            height = f.get('h')
            format_id = '%s_%sp' % (fmt, height) if fmt and height else format_id
            formats.append({
                'url': video_url,
                'format_id': format_id,
                'width': int_or_none(f.get('w')),
                'height': int_or_none(height),
                'tbr': int_or_none(f.get('br')),
            })
        self._sort_formats(formats)

        thumbnail = self._search_regex(
            r"var\s+mov_thumb\s*=\s*'([^']+)';",
            webpage, 'thumbnail', fatal=False)
        publishedAt = self._html_search_meta('uploadDate', webpage, 'uploadDate').split('T')[0]

        return {
            'id': video_id,
            'title': video_title,
            'description': description,
            'duration': duration,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
            'thumbnail': thumbnail,
        }
