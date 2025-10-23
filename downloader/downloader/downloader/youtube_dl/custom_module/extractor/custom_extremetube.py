from __future__ import unicode_literals

import re
from youtube_dl.aes import aes_decrypt_text
from youtube_dl.utils import (
    str_to_int,
    url_or_none,
    int_or_none,
    strip_or_none,
    determine_ext,
    ExtractorError,
)
from youtube_dl.compat import compat_urllib_parse_unquote
from youtube_dl.extractor.keezmovies import KeezMoviesIE


class CustomExtremeTubeIE(KeezMoviesIE):
    _VALID_URL = r'https?://(?:www\.)?extremetube\.com/(?:[^/]+/)?video/(?P<id>[^/#?&]+)'

    def _extract_info(self, url, fatal=True):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = (mobj.group('display_id')
                      if 'display_id' in mobj.groupdict()
                      else None) or mobj.group('id')

        webpage = self._download_webpage(
            url, display_id, headers={'Cookie': 'age_verified=1'})

        formats = []
        format_urls = set()

        title = None
        description = None
        thumbnail = None
        duration = None
        encrypted = False

        def extract_format(format_url, height=None):
            format_url = url_or_none(format_url)
            if not format_url or not format_url.startswith(('http', '//')):
                return
            if format_url in format_urls:
                return
            format_urls.add(format_url)
            tbr = int_or_none(self._search_regex(
                r'[/_](\d+)[kK][/_]', format_url, 'tbr', default=None))
            if not height:
                height = int_or_none(self._search_regex(
                    r'[/_](\d+)[pP][/_]', format_url, 'height', default=None))
            if encrypted:
                format_url = aes_decrypt_text(
                    video_url, title, 32).decode('utf-8')
            formats.append({
                'url': format_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
                'tbr': tbr,
            })

        flashvars = self._parse_json(
            self._search_regex(
                r'flashvars\s*=\s*({.+?});', webpage,
                'flashvars', default='{}'),
            display_id, fatal=False)

        if flashvars:
            title = flashvars.get('video_title')
            description = self._html_search_meta('description', webpage, 'description')
            thumbnail = self._html_search_meta('og:image', webpage, 'og:image')
            duration = int_or_none(flashvars.get('video_duration'))
            encrypted = flashvars.get('encrypted') is True
            for key, value in flashvars.items():
                mobj = re.search(r'quality_(\d+)[pP]', key)
                if mobj:
                    extract_format(value, int(mobj.group(1)))
            video_url = flashvars.get('video_url')
            if video_url and determine_ext(video_url, None):
                extract_format(video_url)

        video_url = self._html_search_regex(
            r'flashvars\.video_url\s*=\s*(["\'])(?P<url>http.+?)\1',
            webpage, 'video url', default=None, group='url')
        if video_url:
            extract_format(compat_urllib_parse_unquote(video_url))

        if not formats:
            if 'title="This video is no longer available"' in webpage:
                raise ExtractorError(
                    'Video %s is no longer available' % video_id, expected=True)

        try:
            formats = list(filter(lambda x: x['height'], formats))
            self._sort_formats(formats)
        except ExtractorError:
            if fatal:
                raise

        if not title:
            title = self._html_search_regex(
                r'<h1[^>]*>([^<]+)', webpage, 'title')

        return webpage, {
            'id': video_id,
            'display_id': display_id,
            'title': strip_or_none(title),
            'description': strip_or_none(description),
            'thumbnail': thumbnail,
            'duration': duration,
            'age_limit': 18,
            'formats': formats,
        }

    def _real_extract(self, url):
        webpage, info = self._extract_info(url)

        if not info['title']:
            info['title'] = self._search_regex(
                r'<h1[^>]+title="([^"]+)"[^>]*>', webpage, 'title')

        uploader = self._html_search_regex(
            r'Uploaded by:\s*</[^>]+>\s*<a[^>]+>(.+?)</a>',
            webpage, 'uploader', fatal=False)
        view_count = str_to_int(self._search_regex(
            r'Views:\s*</[^>]+>\s*<[^>]+>([\d,\.]+)</',
            webpage, 'view count', fatal=False))
        publishedAt = self._search_regex(
            r'Date:\s*</[^>]+>\s*<[^>]+>([^/]+)</',
            webpage, 'publishedAt', fatal=False
        ).strip()

        info.update({
            'uploader': uploader,
            'view_count': view_count,
            'publishedAt': publishedAt
        })

        return info
