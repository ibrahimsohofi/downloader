from __future__ import unicode_literals
from youtube_dl.extractor.common import InfoExtractor


class CustomFunimateIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?funimate\.com/p/(?P<id>[^&]+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_meta('twitter:title', webpage, 'twitter:title')
        description = self._html_search_meta('twitter:description', webpage, 'twitter:description')
        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail')
        publishedAt, view_count, duration = [''] * 3

        height = int(self._html_search_meta('og:video:height', webpage, 'og:video:height'))
        video_url = self._html_search_meta('og:video', webpage, 'og:video')
        video_info = {
            'url': video_url,
            'format_id': '%dp' % height,
            'height': height,
            'ext': 'mp4'
        }
        formats = [video_info]
        return {
            'id': video_id,
            'title': title,
            'description': description,
            'publishedAt': publishedAt,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats,
        }
