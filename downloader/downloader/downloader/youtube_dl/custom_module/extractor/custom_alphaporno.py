from __future__ import unicode_literals

import re
# import datetime
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    # parse_iso8601,
    parse_duration,
    # parse_filesize,
    extract_attributes,
    int_or_none,
    ExtractorError
)


class CustomAlphaPornoIE(InfoExtractor):
    IE_NAME = 'custom alphaporno'
    _VALID_URL = r'https?://(?:www\.)?alphaporno\.com/videos/(?P<id>[^/]+)'
    _TEST = {
        'url': 'http://www.alphaporno.com/videos/sensual-striptease-porn-with-samantha-alexandra/',
        'md5': 'feb6d3bba8848cd54467a87ad34bd38e',
        'info_dict': {
            'id': '258807',
            'display_id': 'sensual-striptease-porn-with-samantha-alexandra',
            'ext': 'mp4',
            'title': 'Sensual striptease porn with Samantha Alexandra',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1418694611,
            'upload_date': '20141216',
            'duration': 387,
            'filesize_approx': 54120000,
            'tbr': 1145,
            'categories': list,
            'age_limit': 18,
        }
    }

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

        video_id = self._search_regex(
            # r"video_id\s*:\s*'([^']+)'"
            r"params\[\'video_id\'\] \= (\d+);", webpage, 'video id', default=None)

        video_str = self._search_regex(
            r'''<video id="bravoplayer"(.*?)</video>''', webpage, 'video content'
        )
        if video_str:
            sources = re.findall(r'<source.*?/>', video_str)
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
        else:
            raise ExtractorError('not found video info, please check function')

        ext = self._html_search_meta(
            'encodingFormat', webpage, 'ext', default='.mp4')[1:]

        title = self._html_search_meta(
            'og:title', webpage, 'title')
        thumbnail = self._html_search_meta('og:image', webpage, 'thumbnail')
        description = self._html_search_meta('og:description', webpage, 'description')
        publishedAt = self._html_search_meta(
            'og:video:release_date', webpage, 'upload date').split(' ')[0]
        duration = parse_duration(self._html_search_meta(
            'og:video:duration', webpage, 'duration'))
        # filesize_approx = parse_filesize(self._html_search_meta(
        #     'contentSize', webpage, 'file size'))
        # filesize_approx = self._html_search_meta(
        #     'contentSize', webpage, 'file size')
        # filesizes = re.split(r'Mb|Gb', filesize_approx)
        # for info, size in zip(array, filesizes[:len(array)]):
        #     size = size.strip()
        #     size = round(float(size))
        #     if size <= 3:
        #         size = size * 1024 * 1024 * 1024
        #     else:
        #         size = size * 1024 * 1024
        #     info['filesize'] = size

        view_count = re.search(r'class="views">(.*?)</span>', webpage, re.S)
        if view_count:
            view_count = int(view_count.group(1).strip())
        else:
            view_count = ''

        bitrate = int_or_none(self._html_search_meta(
            'bitrate', webpage, 'bitrate'))
        categories = self._html_search_meta(
            'keywords', webpage, 'categories', default='').split(',')

        age_limit = self._rta_search(webpage)

        return {
            'id': video_id,
            'display_id': display_id,
            'formats': array,
            'url': array[-1]['url'],
            'ext': ext,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'publishedAt': publishedAt,
            'duration': duration,
            'view_count': view_count,
            'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.alphaporno.com/embed/{}"></iframe>'.format(video_id),
            # 'filesize_approx': filesize_approx,
            'tbr': bitrate,
            'categories': categories,
            'age_limit': age_limit,
        }
