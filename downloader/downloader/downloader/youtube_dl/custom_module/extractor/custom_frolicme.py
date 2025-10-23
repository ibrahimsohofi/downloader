from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor


class CustomFrolicmeIE(InfoExtractor):
    'https://www.frolicme.com/films/secretary-personal-assistant-lift-sex/'
    _VALID_URL = r'https?://(?:www\.|m\.)?frolicme\.com/films/(?P<display_id>[^/?#&]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        display_id = mobj.group('display_id')

        webpage = self._download_webpage(url, display_id)

        title = self._html_search_meta('og:title', webpage)

        description = self._html_search_meta('og:description', webpage)

        thumbnail = self._html_search_meta('og:image', webpage)

        duration = ''

        view_count = ''

        publishedAt = self._html_search_regex(
            r'"dateModified": "(.*?)",', webpage, 'publishedAt', default=''
        )
        if publishedAt:
            publishedAt = publishedAt.split('T')[0]

        video_url = self._html_search_regex(
            r'data-videofile="(.*?)"', webpage, 'video url'
        )
        video_type = self._html_search_regex(
            r'data-videoType="(.*?)"', webpage, 'video type'
        )
        if video_type == 'mp4':
            protocol = 'https'
            ext = 'mp4'
        else:
            protocol = 'm3u8'
            ext = 'm3u8'
        formats = []
        info = {
            'url': video_url,
            'protocol': protocol,
            'ext': ext,
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
            'age_limit': 18,
            'formats': formats
        }

        # print(json.dumps(result))
        return result
