from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError
)


class CustomEromeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?erome\.com/a/(?P<id>[^/]+)'

    def _real_extract(self, url):
        display_id = self._match_id(url)

        webpage = self._download_webpage(
            fr'https://www.erome.com/a/{display_id}', display_id)

        title = self._html_search_meta(
            'og:title', webpage, 'title')

        description = self._html_search_meta(
            'description', webpage, 'description')

        thumbnail = self._html_search_meta(
            'og:image', webpage, 'og:image'
        )

        view_count = self._html_search_regex(
            r'''</i>(.*?)<span class="hidden-sm''', webpage, 'views', default=''
        ).strip()

        # content = re.search(r'<div id="album"(.+?)<div class="clearfix">', webpage, re.DOTALL).group(1)
        group_items = re.findall(r'(<div class="img".*?)(<div class="media-group"|<div class="clearfix"></div>)', webpage, re.DOTALL)
        # group_items = re.findall(r'class="media-group".*?</div>.*?</div>', content, re.S)
        formats = []
        for (group_item, _) in group_items:
            if 'class="video' in group_item:
                # video
                thumbnail = self._html_search_regex(r'poster="(.*?)"', group_item, 'thumbnail', default='')
                video_url = self._html_search_regex(r'<source src="(.*?)"', group_item, 'video_url', default='')
                height = self._html_search_regex(r"res='(\d+)'", group_item, 'video_url', default=None)
                if height:
                    height = int(height)

                if not thumbnail and not video_url and not height:
                    raise ExtractorError('Can`t found thumbnail or video_url or height!')
                info = {
                    'type': 'video',
                    'url': video_url,
                    'thumbnail': thumbnail,
                    'width': None,
                    'height': height
                }
            else:
                # image
                image_url = self._html_search_regex(r'class="img" data-src="(.*?)"', group_item, 'img', default='')
                if not image_url:
                    raise ExtractorError('Can!t found image_url!')
                info = {
                    'type': 'image',
                    'url': image_url,
                    'width': None,
                    'height': None
                }
            formats.append(info)

        return {
            'id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': None,
            'view_count': view_count,
            'publishedAt': '',
            'formats': formats,
            'age_limit': 18,
        }
