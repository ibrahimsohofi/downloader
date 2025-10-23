from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    get_elements_by_class,
    extract_attributes,
    ExtractorError
)


class CustomGogoanimeIE(InfoExtractor):
    IE_NAME = 'gogoanime'
    _VALID_URL = r'https?://(?:www(?:\d+)?\.)?gogoanime\.(?:movie|so|ai)/(?P<name>[^/]+)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        name = mobj.group('name')
        webpage = self._download_webpage(url, name)

        title = self._html_search_meta(r'og:description', webpage, 'title')
        description = self._html_search_meta(r'og:title', webpage, 'description')
        view_count = ''
        thumbnail = self._html_search_meta(r'og:image', webpage, 'og:image')
        publishedAt = ''

        download_url = self._html_search_regex([
            r'<li class="dowloads"><a href="(.*?)"',
        ], webpage, 'iframe url')
        if not download_url:
            raise ExtractorError(f'a wrong happen, the webpage content is {webpage}')
        download_web_page = self._download_webpage(download_url, title)
        duration = self._html_search_regex(
            r'<span id="duration">(.*?)</span>',
            download_web_page, 'duration'
        )
        items = get_elements_by_class('dowload', download_web_page)
        items = [item for item in items if '- mp4)' in item and '(HDP - mp4)' not in item]
        formats = []
        for item in items:
            attr = extract_attributes(item)
            height_info = re.search(r'\((.*?)\)</a>', item, re.S).group(1)
            height = height_info.split('-')[0].strip('pP ')
            video_info = {
                'url': attr['href'],
                'format_id': '%sp' % height,
                'height': int(height),
                'ext': 'mp4'
            }
            formats.append(video_info)

        player = '<video controls="" autoplay="" name="media" ' \
                 'width="100%" height="100%">' \
                 '<source src="{}" type="video/mp4"></video>'.format(formats[-1]['url'])
        info = {
            'id': name or title,
            'title': title,
            'description': description,
            'view_count': view_count,
            'thumbnail': thumbnail,
            'duration': duration,
            'publishedAt': publishedAt,
            'player': player,
            'formats': formats,
            'extractor': self.IE_NAME
        }
        # print(json.dumps(info))
        return info
