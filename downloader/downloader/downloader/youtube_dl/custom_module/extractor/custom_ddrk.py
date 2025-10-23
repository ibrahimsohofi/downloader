from __future__ import unicode_literals

import re, json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import ExtractorError
from youtube_dl.custom_module.site_packages import urllib3


class CustomDdrkIE(InfoExtractor):
    'https://ddrk.me/leon-the-professional/'
    _VALID_URL = r'https?://(?:www\.)?ddrk\.me/(?P<name>[\dA-Za-z\-]*)/(?:(?P<season>\d+)/)*(?:\?ep=(?P<num>\d+))*'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        # season = mobj.group('season')
        num = mobj.group('num')
        if num:
            num = int(num)

        http = urllib3.PoolManager()
        response = http.request('GET', url)
        if response.status == 200 and response.reason == 'OK':
            webpage = response.data.decode()
        else:
            raise ExtractorError('Can`t Download Webpage, Retry It!')

        json_text = re.search(
            r'<script class="wp-playlist-script" type="application/json">(.+?)</script>',
            webpage, re.S
        )
        if json_text:
            json_text = json_text.group(1)
            json_text = json.loads(json_text)
        else:
            raise ExtractorError('Can`t Search Json, Check It!')

        title = self._html_search_regex(
            r'<title>(.*?)</title>', webpage, 'title',
            default=''
        ).split('-')[0]
        if not title:
            title = name.replace('-', '').capitalize()

        if num:
            item = json_text['tracks'][num - 1]
        else:
            item = json_text['tracks'][0]
        src0 = item['src0']
        src2 = item['src2']
        title += item['caption']

        video_url = f'https://w.ddrk.me{src0}?ddrkey={src2}'

        video_info = {
            'url': video_url,
            'ext': 'mp4'
        }

        formats = [video_info]

        return {
            'id': name,
            'title': title,
            'duration': '',
            'description': '',
            'publishedAt': '',
            'thumbnail': '',
            'formats': formats,
        }
