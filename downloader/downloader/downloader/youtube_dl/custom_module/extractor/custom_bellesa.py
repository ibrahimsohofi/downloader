from __future__ import unicode_literals

import re
import json
import datetime
from youtube_dl.extractor.common import InfoExtractor


class CustomBellesaIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?bellesa\.co/videos/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        webpage = self._download_webpage(url, video_id)
        video_data = self._html_search_regex(
            r'window.__INITIAL_DATA__ = (.*?);', webpage, 'video data'
        )
        video_data = self._parse_json(video_data, video_id)

        title = video_data['video']['title']

        description = video_data['video'].get('description') or self._html_search_meta('description', webpage)

        thumbnail = self._html_search_meta('og:image', webpage)

        duration = video_data['video'].get('duration', '')

        view_count = video_data['video'].get('views', '')

        timestamp = video_data['video']['posted_on']
        publishedAt = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')

        video_source = video_data['video']['_videoSource']
        video_url = f'https://s.bellesa.co/v/{video_source}/%s.mp4'
        formats = []
        for h in (360, 480, 720):
            info = {
                'url': video_url % h,
                'protocol': 'https',
                'ext': 'mp4',
                'height': h,
            }
            formats.append(info)

        result = {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'age_limit': 18,
            'formats': formats
        }
        return result
        # print(json.dumps(result))
