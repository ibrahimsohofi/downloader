from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_duration,
    int_or_none,
)


class CustomCamWithHerIE(InfoExtractor):
    IE_NAME = 'custom camwithher'
    '''https://www.camwithher.tv/exec/clips/6qMgqfe4LoorKw6n4Aqp'''
    _VALID_URL = r'https?://(?:www\.)?camwithher\.tv/exec/clips/(?P<id>[^/]+)'

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
        display_id = self._match_id(url)

        webpage = self._download_webpage(url, display_id)

        info = {
            'ext': 'mp4',
            'width': None,
            'height': 480,
            'tbr': None,
            'format_id': None,
            'url': 'https://www.camwithher.tv/fanclub_content.jsp?vkey={}'.format(display_id),
            'vcodec': None
        }
        array = [info]

        ext = self._html_search_meta(
            'encodingFormat', webpage, 'ext', default='.mp4')[1:]

        title = self._html_search_meta('og:title', webpage, 'og:title')
        description = self._html_search_meta('og:description', webpage, 'og:description')
        thumbnail = self._html_search_meta('og:image', webpage, 'og:image')
        timestamp = self._html_search_regex(
            (
                '<span class="date">(.*?)</span>',
                '<span title="Date"><i class="fa fa-calendar-o"></i>\n?(.*?)</span>'
            ),
            webpage, 'upload date', default='')
        duration = parse_duration(self._html_search_regex(
            '<span><i class="fa fa-clock-o"></i>(.*?)</span>', webpage, 'duration'))

        view_count = re.search(r'<span><i class="fa fa-eye"></i>(.*?)</span>', webpage, re.S)
        if view_count:
            view_count = view_count.group(1).strip()
            if view_count.isdigit():
                view_count = int(view_count.strip())
            else:
                view = int(view_count.strip('kmb'))
                if 'k' in view_count:
                    view_count = view * 1000
                elif 'm' in view_count:
                    view_count = view * 1000000
                else:
                    view_count = view * 1000000000
        else:
            view_count = ''

        bitrate = int_or_none(self._html_search_meta(
            'bitrate', webpage, 'bitrate'))
        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')
        publishedAt = self._html_search_regex(
            (
                r'<span class="date">(.*?)</span>',
                r'<span title="Date"><i class="fa fa-calendar-o"></i>\n?(.*?)</span>'
            ),
            webpage,
            'publishedAt', default=''
        )

        age_limit = self._rta_search(webpage)

        return {
            'id': display_id,
            'display_id': display_id,
            'formats': array,
            'url': array[-1]['url'],
            'ext': ext,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'duration': duration,
            'publishedAt': publishedAt,
            'view_count': view_count,
            'tbr': bitrate,
            'categories': categories,
            'age_limit': age_limit,
        }
