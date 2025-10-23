from __future__ import unicode_literals

import json
import re
import datetime
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import compat_str
from youtube_dl.utils import (
    get_element_by_class,
    str_to_int,
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_duration,
    try_get,
    unified_strdate,
    url_or_none,
    float_or_none,
    urljoin,
    str_or_none
)


class CustomXHamsterIE(InfoExtractor):
    _DOMAINS = r'(?:xhamster\.(?:com|one|desi)|xhms\.pro|xhamster\d+\.com)'
    _VALID_URL = r'''(?x)
                        https?://
                            (?:.+?\.)?%s/
                            (?:
                                movies/(?P<id>[\dA-Za-z]+)/(?P<display_id>[^/]*)\.html|
                                videos/(?P<display_id_2>[^/]*)-(?P<id_2>[\dA-Za-z]+)
                            )
                        ''' % _DOMAINS

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        url = url.replace('.one', '.com').replace('.desi', '.com')
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id') or mobj.group('id_2')
        display_id = mobj.group('display_id') or mobj.group('display_id_2')

        desktop_url = re.sub(r'^(https?://(?:.+?\.)?)m\.', r'\1', url)
        webpage, urlh = self._download_webpage_handle(desktop_url, video_id)

        error = self._html_search_regex(
            r'<div[^>]+id=["\']videoClosed["\'][^>]*>(.+?)</div>',
            webpage, 'error', default=None)
        if error:
            raise ExtractorError(error, expected=True)

        age_limit = self._rta_search(webpage)

        def get_height(s):
            return int_or_none(self._search_regex(
                r'^(\d+)[pP]', s, 'height', default=None))

        initials = self._parse_json(
            self._search_regex(
                (r'window\.initials\s*=\s*({.+?})\s*;\s*</script>',
                 r'window\.initials\s*=\s*({.+?})\s*;'), webpage, 'initials',
                default='{}'),
            video_id, fatal=False)
        if initials:
            video = initials['videoModel']
            title = video['title']
            formats = []
            format_urls = set()
            format_sizes = {}
            sources = try_get(video, lambda x: x['sources'], dict) or {}
            for format_id, formats_dict in sources.items():
                if not isinstance(formats_dict, dict):
                    continue
                download_sources = try_get(sources, lambda x: x['download'],
                                           dict) or {}
                for quality, format_dict in download_sources.items():
                    if not isinstance(format_dict, dict):
                        continue
                    format_sizes[quality] = float_or_none(
                        format_dict.get('size'))
                for quality, format_item in formats_dict.items():
                    if format_id == 'download':
                        # Download link takes some time to be generated,
                        # skipping for now
                        continue
                    format_url = format_item
                    format_url = url_or_none(format_url)
                    if not format_url or format_url in format_urls:
                        continue
                    format_urls.add(format_url)
                    formats.append({
                        'format_id': '%s-%s' % (format_id, quality),
                        'url': format_url + '&amoysharetype={"headers": {"referer": "%s"}}' % url,
                        'ext': determine_ext(format_url, 'mp4'),
                        'height': get_height(quality),
                        'filesize': format_sizes.get(quality),
                        'http_headers': {
                            'Referer': urlh.geturl(),
                        },
                    })
            xplayer_sources = try_get(
                initials, lambda x: x['xplayerSettings']['sources'], dict)
            if xplayer_sources:
                hls_sources = xplayer_sources.get('hls')
                if isinstance(hls_sources, dict):
                    for hls_format_key in ('url', 'fallback'):
                        hls_url = hls_sources.get(hls_format_key)
                        if not hls_url:
                            continue
                        hls_url = urljoin(url, hls_url)
                        if not hls_url or hls_url in format_urls:
                            continue
                        format_urls.add(hls_url)
                        formats.extend(self._extract_m3u8_formats(
                            hls_url, video_id, 'mp4',
                            entry_protocol='m3u8_native',
                            m3u8_id='hls', fatal=False))
                standard_sources = xplayer_sources.get('standard')
                if isinstance(standard_sources, dict):
                    for format_id, formats_list in standard_sources.items():
                        if not isinstance(formats_list, list):
                            continue
                        for standard_format in formats_list:
                            if not isinstance(standard_format, dict):
                                continue
                            for standard_format_key in ('url', 'fallback'):
                                standard_url = standard_format.get(
                                    standard_format_key)
                                if not standard_url:
                                    continue
                                standard_url = urljoin(url, standard_url)
                                if not standard_url or standard_url in format_urls:
                                    continue
                                format_urls.add(standard_url)
                                ext = determine_ext(standard_url, 'mp4')
                                if ext == 'm3u8':
                                    formats.extend(self._extract_m3u8_formats(
                                        standard_url, video_id, 'mp4',
                                        entry_protocol='m3u8_native',
                                        m3u8_id='hls', fatal=False))
                                    continue
                                quality = (str_or_none(
                                    standard_format.get('quality'))
                                           or str_or_none(
                                            standard_format.get('label'))
                                           or '')
                                formats.append({
                                    'format_id': '%s-%s' % (format_id, quality),
                                    'url': standard_url + '&amoysharetype={"headers": {"referer": "%s"}}' % url,
                                    'ext': ext,
                                    'height': get_height(quality),
                                    'filesize': format_sizes.get(quality),
                                    'http_headers': {
                                        'Referer': standard_url,
                                    },
                                })
            self._sort_formats(formats, field_preference=('height', 'width', 'tbr', 'format_id'))
            mp4_group = [x for x in formats if 'mp4-' in x['format_id']]
            m3u8_group = [x for x in formats if 'hls-' in x['format_id']]

            if mp4_group:
                formats = mp4_group
            else:
                formats = m3u8_group

            categories_list = video.get('categories')
            if isinstance(categories_list, list):
                categories = []
                for c in categories_list:
                    if not isinstance(c, dict):
                        continue
                    c_name = c.get('name')
                    if isinstance(c_name, compat_str):
                        categories.append(c_name)
            else:
                categories = None

            return {
                'id': video_id,
                'display_id': display_id,
                'title': title,
                'description': video.get('description'),
                'timestamp': int_or_none(video.get('created')),
                'uploader': try_get(
                    video, lambda x: x['author']['name'], compat_str),
                'thumbnail': video.get('thumbURL'),
                'duration': int_or_none(video.get('duration')),
                'view_count': int_or_none(video.get('views')),
                'like_count': int_or_none(try_get(
                    video, lambda x: x['rating']['likes'], int)),
                'dislike_count': int_or_none(try_get(
                    video, lambda x: x['rating']['dislikes'], int)),
                'comment_count': int_or_none(video.get('views')),
                'age_limit': age_limit,
                'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://xhamster.com/embed/{}"></iframe>'.format(video_id),
                'categories': categories,
                'formats': formats,
            }

        # Old layout fallback

        title = self._html_search_regex(
            [r'<h1[^>]*>([^<]+)</h1>',
             r'<meta[^>]+itemprop=".*?caption.*?"[^>]+content="(.+?)"',
             r'<title[^>]*>(.+?)(?:,\s*[^,]*?\s*Porn\s*[^,]*?:\s*xHamster[^<]*| - xHamster\.com)</title>'],
            webpage, 'title')

        formats = []
        format_urls = set()

        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})\s*,?\s*\n', webpage, 'sources',
                default='{}'),
            video_id, fatal=False)
        for format_id, format_url in sources.items():
            format_url = url_or_none(format_url)
            if not format_url:
                continue
            if format_url in format_urls:
                continue
            format_urls.add(format_url)
            formats.append({
                'format_id': format_id,
                'url': format_url,
                'height': get_height(format_id),
            })

        video_url = self._search_regex(
            [r'''file\s*:\s*(?P<q>["'])(?P<mp4>.+?)(?P=q)''',
             r'''<a\s+href=(?P<q>["'])(?P<mp4>.+?)(?P=q)\s+class=["']mp4Thumb''',
             r'''<video[^>]+file=(?P<q>["'])(?P<mp4>.+?)(?P=q)[^>]*>'''],
            webpage, 'video url', group='mp4', default=None)
        if video_url and video_url not in format_urls:
            formats.append({
                'url': video_url,
            })

        self._sort_formats(formats)

        # Only a few videos have an description
        mobj = re.search(r'<span>Description: </span>([^<]+)', webpage)
        description = mobj.group(1) if mobj else None

        upload_date = unified_strdate(self._search_regex(
            r'hint=["\'](\d{4}-\d{2}-\d{2}) \d{2}:\d{2}:\d{2} [A-Z]{3,4}',
            webpage, 'upload date', fatal=False))

        uploader = self._html_search_regex(
            r'<span[^>]+itemprop=["\']author[^>]+><a[^>]+><span[^>]+>([^<]+)',
            webpage, 'uploader', default='anonymous')

        thumbnail = self._search_regex(
            [r'''["']thumbUrl["']\s*:\s*(?P<q>["'])(?P<thumbnail>.+?)(?P=q)''',
             r'''<video[^>]+"poster"=(?P<q>["'])(?P<thumbnail>.+?)(?P=q)[^>]*>'''],
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        duration = parse_duration(self._search_regex(
            [
                r'<[^<]+\bitemprop=["\']duration["\'][^<]+\bcontent=["\'](.+?)["\']',
                r'Runtime:\s*</span>\s*([\d:]+)'], webpage,
            'duration', fatal=False))

        view_count = int_or_none(self._search_regex(
            r'content=["\']User(?:View|Play)s:(\d+)',
            webpage, 'view count', fatal=False))

        mobj = re.search(
            r'hint=[\'"](?P<likecount>\d+) Likes / (?P<dislikecount>\d+) Dislikes',
            webpage)
        (like_count, dislike_count) = (
        mobj.group('likecount'), mobj.group('dislikecount')) if mobj else (
        None, None)

        mobj = re.search(r'</label>Comments \((?P<commentcount>\d+)\)</div>',
                         webpage)
        comment_count = mobj.group('commentcount') if mobj else 0

        categories_html = self._search_regex(
            r'(?s)<table.+?(<span>Categories:.+?)</table>', webpage,
            'categories', default=None)
        categories = [clean_html(category) for category in re.findall(
            r'<a[^>]+>(.+?)</a>', categories_html)] if categories_html else None

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'publishedAt': upload_date,
            'uploader': uploader,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': int_or_none(like_count),
            'dislike_count': int_or_none(dislike_count),
            'comment_count': int_or_none(comment_count),
            'age_limit': age_limit,
            'categories': categories,
            'formats': formats,
        }


class CustomXHamsterSearchIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xhamster\.com/search/(?P<query>[^&?]+)(?:[?]|$)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)
        webpage = webpage.replace("'", '"')

        items = re.findall(
            r'''<div class="thumb-list__item video-thumb role-pop"(.+?)<div class="video-thumb-info">''',
            webpage,
            re.S
        )

        if not items:
            raise ExtractorError('Can`t get items!')

        entries = []
        for item in items:
            title = self._search_regex(
                r'''alt="(.*?)"''', item,
                'title'
            )
            thumbnail = self._search_regex(
                r'''src="(.*?)"''',
                item,
                'thumbnail'
            )
            publishedAt = ''

            description = ''
            item_url = self._search_regex(
                r'''href="(.*?)"''',
                item,
                'item url'
            )
            vid = item_url.split('-')[-1]
            duration = self._search_regex(
                r'''<span data-role-video-duration>(.*?)</span>''',
                item,
                'duration'
            ) or ''
            if duration:
                duration_parts = duration.split(':')
                if len(duration_parts) == 2:
                    mins, seconds = duration_parts
                    mins, seconds = int(mins) * 60, int(seconds)
                    duration = mins + seconds
                else:
                    hours, mins, seconds = duration_parts
                    hours, mins, seconds = int(hours) * 3600, int(
                        mins) * 60, int(seconds)
                    duration = hours + mins + seconds
            view_count = str_to_int(self._search_regex(
                r'''<span class="metric-text">(.*?)</span>''',
                item,
                'view count',
                default=''
            ))
            entries.append({
                'id': vid,
                'title': title,
                'publishedAt': publishedAt,
                'thumbnail': thumbnail,
                'description': description,
                'url': item_url,
                'duration': duration,
                'view_count': view_count
            })

        ie_result = self.playlist_result(entries, query_id)
        is_next_page = '<li class="next">' in webpage and 'data-page="next"' in webpage
        if is_next_page:
            next_page_str = get_element_by_class('pager-section', webpage)
            next_page_str = re.findall(
                r'<li.*?</li>',
                next_page_str, re.S
            )[-1]
            next_page_str = re.search(r'href="(.*?)"', next_page_str,
                                      re.S).group(1).replace('amp;', '')
            ie_result.update(
                {'next_page': next_page_str})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
