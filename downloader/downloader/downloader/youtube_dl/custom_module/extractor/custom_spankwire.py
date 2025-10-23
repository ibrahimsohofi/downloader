from __future__ import unicode_literals

import re
import datetime
from youtube_dl.extractor.common import InfoExtractor
# from youtube_dl.compat import (
#     compat_urllib_parse_unquote,
#     compat_urllib_parse_urlparse,
# )
from youtube_dl.utils import (
    # sanitized_Request,
    str_to_int,
    # unified_strdate,
)
# from youtube_dl.aes import aes_decrypt_text


class CustomSpankwireIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?(?P<url>spankwire\.com/[^/]*/video(?P<id>[0-9]+)/?)'
    _TESTS = [{
        # download URL pattern: */<height>P_<tbr>K_<video_id>.mp4
        'url': 'http://www.spankwire.com/Buckcherry-s-X-Rated-Music-Video-Crazy-Bitch/video103545/',
        'md5': '8bbfde12b101204b39e4b9fe7eb67095',
        'info_dict': {
            'id': '103545',
            'ext': 'mp4',
            'title': 'Buckcherry`s X Rated Music Video Crazy Bitch',
            'description': 'Crazy Bitch X rated music video.',
            'uploader': 'oreusz',
            'uploader_id': '124697',
            'upload_date': '20070507',
            'age_limit': 18,
        }
    }, {
        # download URL pattern: */mp4_<format_id>_<video_id>.mp4
        'url': 'http://www.spankwire.com/Titcums-Compiloation-I/video1921551/',
        'md5': '09b3c20833308b736ae8902db2f8d7e6',
        'info_dict': {
            'id': '1921551',
            'ext': 'mp4',
            'title': 'Titcums Compiloation I',
            'description': 'cum on tits',
            'uploader': 'dannyh78999',
            'uploader_id': '3056053',
            'upload_date': '20150822',
            'age_limit': 18,
        },
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        rs = self._download_json(
            'https://www.spankwire.com/api/video/{}.json'.format(video_id),
            video_id)

        title = rs.get('title') or ''
        description = rs.get('description') or ''
        thumbnail = rs.get('poster') or rs.get('poster2x') or ''

        uploader = ''
        uploader_id = rs['userId'] or ''
        upload_date = datetime.datetime.fromtimestamp(rs['time_approved_on']).strftime('%Y-%m-%d')

        view_count = str_to_int(rs['viewed'])
        duration = rs['duration']
        comment_count = rs['comments']
        videos = rs['videos']
        formats = []
        for fmt in videos:
            height = int(fmt.split('_')[-1].strip('p'))
            video_url = videos[fmt]
            formats.append({
                'url': video_url,
                'format_id': '%dp' % height,
                'height': height,
                'tbr': '',
            })
        self._sort_formats(formats)

        age_limit = 18

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'publishedAt': upload_date,
            'view_count': view_count,
            'duration': duration,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': age_limit,
        }
