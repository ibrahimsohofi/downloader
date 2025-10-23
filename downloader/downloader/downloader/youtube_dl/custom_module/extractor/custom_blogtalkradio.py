from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import int_or_none


class CustomBlogTalkRadioIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?blogtalkradio\.com/(?:[^/]+/)*(?P<id>[^/?]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_meta(['title', 'og:title'], webpage)

        description = self._html_search_meta('og:description', webpage)

        thumbnail = self._html_search_meta('og:image', webpage)

        duration = int_or_none(self._html_search_regex(
            r'Duration: (.*?),', webpage, 'publishedAt', default=None
        ))

        view_count = ''

        publishedAt = self._html_search_regex(
            r'ads: "(.*?)",', webpage, 'publishedAt', default=''
        )

        formats = []
        info = {
            'url': url + '.mp3',
            'protocol': 'https',
            'ext': 'mp3',
        }
        formats.append(info)

        result = {
            'id': display_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'formats': formats
        }

        return result
