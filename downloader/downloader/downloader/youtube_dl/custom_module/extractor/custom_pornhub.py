# coding: utf-8
from __future__ import unicode_literals

import functools
import operator
import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import (
    compat_str,
    compat_urllib_request,
)
from youtube_dl.extractor.openload import PhantomJSwrapper
from youtube_dl.utils import (
    get_elements_by_class,
    get_element_by_id,
    get_element_by_class,
    get_element_by_attribute,
    orderedSet,
    determine_ext,
    ExtractorError,
    int_or_none,
    NO_DEFAULT,
    remove_quotes,
    str_to_int,
    url_or_none,
    merge_dicts
)


class CustomPornHubBaseIE(InfoExtractor):
    @classmethod
    def suitable(cls, url):
        return False

    def _download_webpage_handle(self, *args, **kwargs):
        def dl(*args, **kwargs):
            return super(CustomPornHubBaseIE, self)._download_webpage_handle(*args, **kwargs)

        webpage, urlh = dl(*args, **kwargs)

        if any(re.search(p, webpage) for p in (
                r'<body\b[^>]+\bonload=["\']go\(\)',
                r'document\.cookie\s*=\s*["\']RNKEY=',
                r'document\.location\.reload\(true\)')):
            url_or_request = args[0]
            url = (url_or_request.get_full_url()
                   if isinstance(url_or_request, compat_urllib_request.Request)
                   else url_or_request)
            phantom = PhantomJSwrapper(self, required_version='2.0')
            phantom.get(url, html=webpage)
            webpage, urlh = dl(*args, **kwargs)

        return webpage, urlh


class CustomPornHubIE(CustomPornHubBaseIE):
    IE_DESC = 'PornHub and Thumbzilla'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?(?P<host>pornhub(?:premium)?\.(?:com|net))/(?:(?:view_video\.php|video/show)\?viewkey=|embed/)|
                            (?:www\.)?thumbzilla\.com/video/
                        )
                        (?P<id>[\da-z]+)
                    '''

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//(?:www\.)?pornhub\.(?:com|net|org)/embed/[\da-z]+)',
            webpage)

    def _extract_count(self, pattern, webpage, name):
        return str_to_int(self._search_regex(
            pattern, webpage, '%s count' % name, fatal=False))

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host') or 'pornhub.com'
        video_id = mobj.group('id')

        if 'premium' in host:
            if not self._downloader.params.get('cookiefile'):
                raise ExtractorError(
                    'PornHub Premium requires authentication.'
                    ' You may want to use --cookies.',
                    expected=True)

        self._set_cookie(host, 'age_verified', '1')

        def dl_webpage(platform):
            self._set_cookie(host, 'platform', platform)
            return self._download_webpage(
                'https://www.%s/view_video.php?viewkey=%s' % (host, video_id),
                video_id, 'Downloading %s webpage' % platform)

        webpage = dl_webpage('pc')

        error_msg = self._html_search_regex(
            r'(?s)<div[^>]+class=(["\'])(?:(?!\1).)*\b(?:removed|userMessageSection)\b(?:(?!\1).)*\1[^>]*>(?P<error>.+?)</div>',
            webpage, 'error message', default=None, group='error')
        if error_msg:
            error_msg = re.sub(r'\s+', ' ', error_msg)
            raise ExtractorError(
                'PornHub said: %s' % error_msg,
                expected=True, video_id=video_id)

        # video_title from flashvars contains whitespace instead of non-ASCII (see
        # http://www.pornhub.com/view_video.php?viewkey=1331683002), not relying
        # on that anymore.
        title = self._html_search_meta(
            'twitter:title', webpage, default=None) or self._html_search_regex(
            (r'(?s)<h1[^>]+class=["\']title["\'][^>]*>(?P<title>.+?)</h1>',
             r'<div[^>]+data-video-title=(["\'])(?P<title>(?:(?!\1).)+)\1',
             r'shareTitle["\']\s*[=:]\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', group='title')

        video_urls = []
        video_urls_set = set()
        subtitles = {}

        flashvars = self._parse_json(
            self._search_regex(
                r'var\s+flashvars_\d+\s*=\s*({.+?});', webpage, 'flashvars',
                default='{}'),
            video_id)
        if flashvars:
            subtitle_url = url_or_none(flashvars.get('closedCaptionsFile'))
            if subtitle_url:
                subtitles.setdefault('en', []).append({
                    'url': subtitle_url,
                    'ext': 'srt',
                })
            thumbnail = flashvars.get('image_url')
            duration = int_or_none(flashvars.get('video_duration'))
            media_definitions = flashvars.get('mediaDefinitions')
            if isinstance(media_definitions, list):
                for definition in media_definitions:
                    if not isinstance(definition, dict):
                        continue
                    video_url = definition.get('videoUrl')
                    if not video_url or not isinstance(video_url, compat_str):
                        continue
                    if video_url in video_urls_set:
                        continue
                    video_urls_set.add(video_url)
                    video_urls.append(
                        (video_url, int_or_none(definition.get('quality'))))
        else:
            thumbnail, duration = [None] * 2

        def extract_js_vars(webpage, pattern, default=NO_DEFAULT):
            assignments = self._search_regex(
                pattern, webpage, 'encoded url', default=default)
            if not assignments:
                return {}

            assignments = assignments.split(';')

            js_vars = {}

            def parse_js_value(inp):
                inp = re.sub(r'/\*(?:(?!\*/).)*?\*/', '', inp)
                if '+' in inp:
                    inps = inp.split('+')
                    return functools.reduce(
                        operator.concat, map(parse_js_value, inps))
                inp = inp.strip()
                if inp in js_vars:
                    return js_vars[inp]
                return remove_quotes(inp)

            for assn in assignments:
                assn = assn.strip()
                if not assn:
                    continue
                assn = re.sub(r'var\s+', '', assn)
                vname, value = assn.split('=', 1)
                js_vars[vname] = parse_js_value(value)
            return js_vars

        def add_video_url(video_url):
            v_url = url_or_none(video_url)
            if not v_url:
                return
            if v_url in video_urls_set:
                return
            video_urls.append((v_url, None))
            video_urls_set.add(v_url)

        def parse_quality_items(quality_items):
            q_items = self._parse_json(quality_items, video_id, fatal=False)
            if not isinstance(q_items, list):
                return
            for item in q_items:
                if isinstance(item, dict):
                    add_video_url(item.get('url'))

        if not video_urls:
            FORMAT_PREFIXES = ('media', 'quality', 'qualityItems')
            js_vars = extract_js_vars(
                webpage, r'(var\s+(?:%s)_.+)' % '|'.join(FORMAT_PREFIXES),
                default=None)
            if js_vars:
                for key, format_url in js_vars.items():
                    if key.startswith(FORMAT_PREFIXES[-1]):
                        parse_quality_items(format_url)
                    elif any(key.startswith(p) for p in FORMAT_PREFIXES[:2]):
                        add_video_url(format_url)
            if not video_urls and re.search(
                    r'<[^>]+\bid=["\']lockedPlayer', webpage):
                raise ExtractorError(
                    'Video %s is locked' % video_id, expected=True)

        if not video_urls:
            js_vars = extract_js_vars(
                dl_webpage('tv'), r'(var.+?mediastring.+?)</script>')
            add_video_url(js_vars['mediastring'])

        for mobj in re.finditer(
                r'<a[^>]+\bclass=["\']downloadBtn\b[^>]+\bhref=(["\'])(?P<url>(?:(?!\1).)+)\1',
                webpage):
            video_url = mobj.group('url')
            if video_url not in video_urls_set:
                video_urls.append((video_url, None))
                video_urls_set.add(video_url)

        upload_date = None
        formats = []
        for video_url, height in video_urls:
            if not upload_date:
                upload_date = self._search_regex(
                    r'/(\d{6}/\d{2})/', video_url, 'upload data', default=None)
                if upload_date:
                    upload_date = upload_date.replace('/', '')
            ext = determine_ext(video_url)
            if ext == 'mpd':
                formats.extend(self._extract_mpd_formats(
                    video_url, video_id, mpd_id='dash', fatal=False))
                continue
            elif ext == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    video_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    m3u8_id='hls', fatal=False))
                continue
            tbr = None
            mobj = re.search(r'(?P<height>\d+)[pP]?_(?P<tbr>\d+)[kK]',
                             video_url)
            if mobj:
                if not height:
                    height = int(mobj.group('height'))
                tbr = int(mobj.group('tbr'))
            formats.append({
                'url': video_url,
                'format_id': '%dp' % height if height else None,
                'height': height,
                'tbr': tbr,
            })
        self._sort_formats(formats)

        video_uploader = self._html_search_regex(
            r'(?s)From:&nbsp;.+?<(?:a\b[^>]+\bhref=["\']/(?:(?:user|channel)s|model|pornstar)/|span\b[^>]+\bclass=["\']username)[^>]+>(.+?)<',
            webpage, 'uploader', default=None)

        def extract_vote_count(kind, name):
            return self._extract_count(
                (r'<span[^>]+\bclass="votes%s"[^>]*>([\d,\.]+)</span>' % kind,
                 r'<span[^>]+\bclass=["\']votes%s["\'][^>]*\bdata-rating=["\'](\d+)' % kind),
                webpage, name)

        view_count = self._extract_count(
            r'<span class="count">([\d,\.]+)</span> [Vv]iews', webpage, 'view')
        like_count = extract_vote_count('Up', 'like')
        dislike_count = extract_vote_count('Down', 'dislike')
        comment_count = self._extract_count(
            r'All Comments\s*<span>\(([\d,.]+)\)', webpage, 'comment')

        def extract_list(meta_key):
            div = self._search_regex(
                r'(?s)<div[^>]+\bclass=["\'].*?\b%sWrapper[^>]*>(.+?)</div>'
                % meta_key, webpage, meta_key, default=None)
            if div:
                return re.findall(r'<a[^>]+\bhref=[^>]+>([^<]+)', div)

        info = self._search_json_ld(webpage, video_id, default={})
        # description provided in JSON-LD is irrelevant
        info['description'] = None

        return merge_dicts({
            'id': video_id,
            'uploader': video_uploader,
            'upload_date': upload_date,
            'title': title,
            'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.pornhub.com/embed/{}"></iframe>'.format(video_id),
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'like_count': like_count,
            'dislike_count': dislike_count,
            'comment_count': comment_count,
            'formats': formats,
            'age_limit': 18,
            'tags': extract_list('tags'),
            'categories': extract_list('categories'),
            'subtitles': subtitles,
        }, info)


class CustomPornHubPlaylistBaseIE(CustomPornHubBaseIE):
    def _extract_entries(self, webpage, host):
        # Only process container div with main playlist content skipping
        # drop-down menu that uses similar pattern for videos (see
        # https://github.com/ytdl-org/youtube-dl/issues/11594).
        container = self._search_regex(
            r'(?s)(<div[^>]+class=["\']container.+)', webpage,
            'container', default=webpage)

        return [
            self.url_result(
                'http://www.%s/%s' % (host, video_url),
                CustomPornHubIE.ie_key(), video_title=title)
            for video_url, title in orderedSet(re.findall(
                r'href="/?(view_video\.php\?.*\bviewkey=[\da-z]+[^"]*)"[^>]*\s+title="([^"]+)"',
                container))
        ]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        host = mobj.group('host')
        playlist_id = mobj.group('id')

        webpage = self._download_webpage(url, playlist_id)

        entries = self._extract_entries(webpage, host)

        playlist = self._parse_json(
            self._search_regex(
                r'(?:playlistObject|PLAYLIST_VIEW)\s*=\s*({.+?});', webpage,
                'playlist', default='{}'),
            playlist_id, fatal=False)
        title = playlist.get('title') or self._search_regex(
            r'>Videos\s+in\s+(.+?)\s+[Pp]laylist<', webpage, 'title', fatal=False)

        return self.playlist_result(
            entries, playlist_id, title, playlist.get('description'))


class CustomPornHubSearchIE(CustomPornHubPlaylistBaseIE):
    'https://cn.pornhub.com/video/search?search=my+home&o=mv&hd=1&t=m&page=2'
    _VALID_URL = r'''https?://(?:de\.|fr\.|es\.|it\.|pt\.|pl\.|rt\.|jp\.|nl\.|www\.|cn\.|cz\.)?pornhub.com/video/search\?(.*?&)?search=(?P<query>[^&]+)(?:[&]|$)'''

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)

        items_body = get_element_by_id('videoSearchResult', webpage)
        items = get_elements_by_class('pcVideoListItem', items_body)
        items = list(map(lambda x: x.strip(), items))

        entries = []
        for item in items:
            vid = self._search_regex(
                r'''vkey=(.*?)"''', item, 'vid'
            )
            title = self._search_regex(
                r'''alt="(.*?)"''', item, 'title'
            )
            publishedAt = self._search_regex(
                r'''<var class="added">(.*?)</var>''',
                item,
                'publishedAt'
            )
            thumbnail = self._search_regex(
                r'''data-mediumthumb="(.*?)"''',
                item,
                'thumbnail'
            )
            description = None
            url = 'https://www.pornhub.com/view_video.php?viewkey={}'.format(vid)
            duration = self._search_regex(
                r'''<var class="duration">(.*?)</var>''',
                item,
                'duration'
            ) or ''
            view_count = self._search_regex(
                r'''<var>(.*?)</var>''',
                get_element_by_class('views', item),
                'view count'
            )
            entries.append({
                'id': vid,
                'title': title,
                'publishedAt': publishedAt,
                'thumbnail': thumbnail,
                'description': description,
                'url': url,
                'duration': duration,
                'view_count': view_count
            })

        ie_result = self.playlist_result(entries, query_id)
        is_next_page = len(entries) == 20
        if is_next_page:
            next_page_str = get_element_by_attribute('class', 'pagination3',
                                                     webpage)
            next_page_str = re.findall(
                r'<li class.*?</li>',
                next_page_str, re.S
            )[-1]
            next_page_str = re.search(r'href="(.*?)"', next_page_str,
                                      re.S).group(1).replace('amp;', '')
            ie_result.update(
                {'next_page': 'https://www.pornhub.com{}'.format(next_page_str)})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
