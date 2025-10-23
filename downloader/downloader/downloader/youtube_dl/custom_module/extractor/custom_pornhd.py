from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    compat_http_client,
    parse_duration,
    determine_ext,
    ExtractorError,
    int_or_none,
    js_to_json,
    merge_dicts,
    urljoin,
)


class PornHdIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?pornhd(?:prime)?\.com/(?:[a-z]{2,4}/)?videos/(?P<id>\d+)(?:/(?P<display_id>.+))?'
    _TESTS = [{
        'url': 'http://www.pornhd.com/videos/9864/selfie-restroom-masturbation-fun-with-chubby-cutie-hd-porn-video',
        'md5': '87f1540746c1d32ec7a2305c12b96b25',
        'info_dict': {
            'id': '9864',
            'display_id': 'selfie-restroom-masturbation-fun-with-chubby-cutie-hd-porn-video',
            'ext': 'mp4',
            'title': 'Restroom selfie masturbation',
            'description': 'md5:3748420395e03e31ac96857a8f125b2b',
            'thumbnail': r're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
        },
        'skip': 'HTTP Error 404: Not Found',
    }, {
        'url': 'http://www.pornhd.com/videos/1962/sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
        'md5': '1b7b3a40b9d65a8e5b25f7ab9ee6d6de',
        'info_dict': {
            'id': '1962',
            'display_id': 'sierra-day-gets-his-cum-all-over-herself-hd-porn-video',
            'ext': 'mp4',
            'title': 'md5:98c6f8b2d9c229d0f0fde47f61a1a759',
            'description': 'md5:8ff0523848ac2b8f9b065ba781ccf294',
            'thumbnail': r're:^https?://.*\.jpg',
            'view_count': int,
            'like_count': int,
            'age_limit': 18,
        },
    }]

    def _download_webpage(
            self, url_or_request, video_id, note=None, errnote=None,
            fatal=True, tries=1, timeout=5, encoding=None, data=None,
            headers={}, query={}, expected_status=None):

        success = False
        try_count = 0
        while success is False:
            try:
                res = self._download_webpage_handle(
                    url_or_request, video_id, note, errnote, fatal,
                    encoding=encoding, data=data, headers=headers, query=query,
                    expected_status=expected_status)
                success = True
            except compat_http_client.IncompleteRead as e:
                try_count += 1
                if try_count >= tries:
                    raise e
                self._sleep(timeout, video_id)
        if res is False:
            return res, ''
        else:
            content, urlh = res
            headers = urlh.headers._headers
            cookies = '; '.join([y for (x, y) in headers if x == 'Set-Cookie'])
            return content, cookies

    # '''
    # __cfduid=d0f28ccb8a5cc278bc705e83f4dd0fed41600420579;
    # tsid=eyJpdiI6Ilo0RFQ4YlZXVHlIMU9WTHhRdVwvZUtRPT0iLCJ2YWx1ZSI6ImZiZ0MwSCt1SnZGQTB6RGVueEtBNGc9PSIsIm1hYyI6IjgxMDdkZDNmYjRhNDg1NTU5MGE0MTc4YzAyM2JhMGMzZmIzNjc2ODY0OGMxYTIzOWQ4NGMxYzI0YzlmNzgyYjAifQ%3D%3D;
    # _ga=GA1.2.335598250.1600421061; _gid=GA1.2.1508345126.1600421061;
    # exo_slider_closed_3723099=1; playerVolume=1; playCount=1;
    # wmttrd=eyJpdiI6ImpMWVhwUlVsTjJGMzMwYllzMWNPQ3c9PSIsInZhbHVlIjoiU1FiN3B2WEVcL1J2NnJiTHRzd1NtV0E9PSIsIm1hYyI6ImYwYzNlMTA0NDMxOWM0YWYxZGNmYmMyMDRjNWE4ZDFjNjVhMDczYTAxM2I5M2QwNzY1MTE2YjNiN2QxNTdhMzgifQ%3D%3D;
    # _gat_UA-40453573-15=1; _gat_UA-40453573-16=1;
    # pageViewCount=eyJpdiI6InVoMWsrR3NBc24rbFRDK2NhMWFORmc9PSIsInZhbHVlIjoiYVd1VG1qUWdOUmI0VDM5MHBoNHFJZz09IiwibWFjIjoiOWM5NmIwMzQxNWRkMjU4MDEwY2JlYWVjYzU3NWY0MWQxNzhmZGU2MDIxZjVjZWMyZWM1NmRjZDBlNGEzMzBlOSJ9;
    # XSRF-TOKEN=eyJpdiI6IkV4RDZqRlJiME9DSU5uMFwvdEVmZ0hnPT0iLCJ2YWx1ZSI6ImU0N3JkRlkxQmZQNkFlcitJSWE3ZU1jVnVubWJZbW5vRUJ4Zk1SbnJoMjI1VUVqQXFzSlwvY0ZnMUZNbmc0WFg4IiwibWFjIjoiOWMyMWY3ZWU2YzlmYzk4ZWM2MTAxZTQ1YjE3YzgyNDY5ODY5MjcyMmM0ZTIyZTU3MWMzYzkzYWUxMzYzZGNmOCJ9;
    # laravel_session=eyJpdiI6InkyWXZ2aU93V0dmYmdGRmYxdzNpT0E9PSIsInZhbHVlIjoiWlh5VVgzS2JhRU5xR0R4N1k0c2VsK01hSVZrUm1OQVVxU1VsYlZLRU9iTmRQSzNPNVQ2UExLd05xZjNBamxOUSIsIm1hYyI6IjFlMGY3ZGFlODRlMTFkZDkwNmQ4YmU4NzM3MTBjNTVjMjExNzIwYzRmNGUxZDE0N2MxNjZmZDcxYjVlMWJjMmUifQ%3D%3D
    # '''

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        webpage, cookies = self._download_webpage(url, display_id or video_id)
        if not webpage:
            raise ExtractorError('download failure!!')
        title = self._html_search_regex(
            [r'<span[^>]+class=["\']video-name["\'][^>]*>([^<]+)',
             r'<title>(.+?) - .*?[Pp]ornHD.*?</title>'], webpage, 'title', default='')
        if not title:
            titles = re.findall(r'"name": "(.*?)",', webpage, re.S)
            title = [t for t in titles if t][0]

        publishedAt = self._html_search_regex(
            r'''"uploadDate": "(.*?)",''',
            webpage,
            'publishedAt'
        )
        publishedAt = publishedAt.split(' ')[0]

        duration = self._html_search_regex(
            r'''"duration": "(.*?)"''',
            webpage,
            'duration'
        )
        duration = parse_duration(duration)

        sources = self._parse_json(js_to_json(self._search_regex(
            r"(?s)sources'?\s*[:=]\s*(\{.+?\})",
            webpage, 'sources', default='{}')), video_id)

        info = {}
        if not sources:
            entries = self._parse_html5_media_entries(url, webpage, video_id)
            if entries:
                info = entries[0]

        if not sources and not info:
            message = self._html_search_regex(
                r'(?s)<(div|p)[^>]+class="no-video"[^>]*>(?P<value>.+?)</\1',
                webpage, 'error message', group='value')
            raise ExtractorError('%s said: %s' % (self.IE_NAME, message), expected=True)

        formats = []
        for format_id, video_url in sources.items():
            video_url = urljoin(url, video_url)
            if not video_url:
                continue
            height = int_or_none(self._search_regex(
                r'^(\d+)[pP]', format_id, 'height', default=None))
            video_url = video_url + '&amoysharetype={"headers": {"cookie": "%s"}}' % cookies
            formats.append({
                'url': video_url,
                'ext': determine_ext(video_url, 'mp4'),
                'format_id': format_id,
                'height': height,
            })
        if formats:
            info['formats'] = formats
        else:
            for x in info['formats']:
                x['url'] += '&amoysharetype={"headers": {"cookie": "%s"}}' % cookies
        self._sort_formats(info['formats'])

        content_url = self._html_search_regex(
            '"contentUrl": "(.*?)"',
            webpage, 'title', default=''
        ) or info['formats'][0]['url']
        info['player'] = f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="{content_url}"></iframe>'
        description = self._html_search_meta(
            'description', webpage, default=None) or \
            self._og_search_description(webpage)
        view_count = int_or_none(self._html_search_regex(
            r'(\d+) views\s*<', webpage, 'view count', fatal=False))
        thumbnail = self._search_regex(
            r"poster'?\s*:\s*([\"'])(?P<url>(?:(?!\1).)+)\1", webpage,
            'thumbnail', default=None, group='url')
        if not thumbnail:
            thumbnail = self._html_search_regex(
                r'''poster="(.*?)"''',
                webpage,
                'thumbnail'
            )

        like_count = int_or_none(self._search_regex(
            (r'(\d+)</span>\s*likes',
             r'(\d+)\s*</11[^>]+>(?:&nbsp;|\s)*\blikes',
             r'class=["\']save-count["\'][^>]*>\s*(\d+)'),
            webpage, 'like count', fatal=False))

        result_info = merge_dicts(info, {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'publishedAt': publishedAt,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'like_count': like_count,
            'formats': formats,
            'age_limit': 18,
        })
        # print(json.dumps(result_info))
        return result_info
