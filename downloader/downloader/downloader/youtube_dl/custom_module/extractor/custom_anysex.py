from __future__ import unicode_literals

import re
# import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    extract_attributes,
    int_or_none,
    ExtractorError
)


class CustomAnySexIE(InfoExtractor):
    IE_NAME = 'custom anysex'
    _VALID_URL = r'https?://(?:www\.)?anysex\.com/(?P<id>[^/]+)'

    @classmethod
    def suitable(cls, url):
        """Receives a URL and returns True if suitable for this IE."""

        # This does not use has/getattr intentionally - we want to know whether
        # we have cached the regexp for *this* class, whereas getattr would also
        # match the superclass
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
        return cls._VALID_URL_RE.match(url) is not None

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        sources = re.findall(r'<source.*?>', webpage)
        array = []
        for source in sources:
            attr = extract_attributes(source)
            info = {
                'ext': attr['type'].split('/')[-1],
                'width': None,
                'height': int(attr['title'].split(' ')[0].strip('p')),
                'tbr': None,
                'format_id': None,
                'url': attr['src'],
                'vcodec': None
            }
            array.append(info)
        if not array:
            raise ExtractorError('not found video info, please check function')

        self._sort_formats(array)

        title = self._html_search_regex(
            r'<title>(.+?)</title>', webpage, 'title')
        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail')
        description = self._html_search_meta('description', webpage, 'description')
        publishedAt = self._html_search_regex(
            r'''content="(.*?)"><b>Added:''',
            webpage,
            'publishedAt'
        ).strip() or ''
        duration = self._html_search_regex(
            r'''<b>Duration:</b> <q>(.*?)</q>''',
            webpage,
            'duration'
        )

        view_count = int_or_none(self._html_search_regex(
            r'''<b>Views:</b>(.*?)</span>''',
            webpage,
            'view count'
        ))
        return {
                'id': video_id,
                'display_id': url,
                'formats': array,
                'url': array[-1]['url'],
                'ext': 'mp4',
                'title': title,
                'description': description,
                'thumbnail': thumbnail,
                'publishedAt': publishedAt,
                'duration': duration,
                'view_count': view_count,
                'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://anysex.com/embed/{}"></iframe>'.format(
                    video_id),
                'age_limit': 18,
            }
        # print(json.dumps(
        #     {
        #         'id': video_id,
        #         'display_id': url,
        #         'formats': array,
        #         'url': array[-1]['url'],
        #         'ext': 'mp4',
        #         'title': title,
        #         'description': description,
        #         'thumbnail': thumbnail,
        #         'publishedAt': publishedAt,
        #         'duration': duration,
        #         'view_count': view_count,
        #         'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://anysex.com/embed/{}"></iframe>'.format(
        #             video_id),
        #         'age_limit': 18,
        #     }
        # ))
