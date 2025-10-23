from __future__ import unicode_literals
import random
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import (
    compat_str,
    compat_urlparse,
)
from youtube_dl.utils import (
    int_or_none,
)


class CustomBeegIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?beeg\.(?:com|porn(?:/video)?)/(?P<id>\d+)'

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        beeg_version = self._search_regex(
            r'beeg_version\s*=\s*([\da-zA-Z_-]+)', webpage, 'beeg version',
            default='1546225636701')

        if len(video_id) >= 10:
            query = {
                'v': 2,
            }
            qs = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
            t = qs.get('t', [''])[0].split('-')
            if len(t) > 1:
                query.update({
                    's': t[0],
                    'e': t[1],
                })
        else:
            query = {'v': 1}

        for api_path in ('', 'api.'):
            video = self._download_json(
                'https://%sbeeg.com/api/v6/%s/video/%s'
                % (api_path, beeg_version, video_id), video_id,
                fatal=api_path == 'api.', query=query)
            if video:
                break

        formats = []
        for format_id, video_url in video.items():
            if not video_url:
                continue
            height = self._search_regex(
                r'^(\d+)[pP]$', format_id, 'height', default=None)
            if not height:
                continue
            formats.append({
                'url': self._proto_relative_url(
                    video_url.replace('{DATA_MARKERS}', 'data=pc_XX__%s_0' % beeg_version), 'https:'),
                'format_id': format_id,
                'height': int(height),
            })
        self._sort_formats(formats)

        title = video['title'] or video.get('desc', '')
        video_id = compat_str(video.get('id') or video_id)
        display_id = video.get('code')
        description = video.get('desc')
        series = video.get('ps_name')

        timestamp = video.get('date').split(' ')[0]
        duration = int_or_none(video.get('duration'))

        tags = [tag.strip() for tag in video['tags'].split(',')] if video.get('tags') else None

        thumbnail = 'https://img.beeg.com/264x198/4x3/{}-{}.jpg'.format(video['set_id'], str(random.randint(30, duration)).rjust(4, '0'))

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'series': series,
            'publishedAt': timestamp,
            'thumbnail': thumbnail,
            'duration': duration,
            'tags': tags,
            'formats': formats,
            'age_limit': self._rta_search(webpage),
        }
