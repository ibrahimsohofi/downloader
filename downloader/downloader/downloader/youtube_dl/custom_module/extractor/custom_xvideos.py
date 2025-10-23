from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import compat_urllib_parse_unquote
from youtube_dl.utils import (
    get_element_by_attribute,
    clean_html,
    determine_ext,
    ExtractorError,
    int_or_none,
    parse_duration,
    parse_count,
)


class CustomXVideosIE(InfoExtractor):
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?:[^/]+\.)?xvideos2?\.com/video|
                            (?:www\.)?xvideos\.es/video|
                            flashservice\.xvideos\.com/embedframe/|
                            static-hw\.xvideos\.com/swf/xv-player\.swf\?.*?\bid_video=
                        )
                        (?P<id>[0-9]+)
                    '''

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(
            'https://www.xvideos.com/video%s/' % video_id, video_id)

        mobj = re.search(r'<h1 class="inlineError">(.+?)</h1>', webpage)
        if mobj:
            raise ExtractorError('%s said: %s' % (self.IE_NAME, clean_html(mobj.group(1))), expected=True)

        title = self._html_search_regex(
            (r'<title>(?P<title>.+?)\s+-\s+XVID',
             r'setVideoTitle\s*\(\s*(["\'])(?P<title>(?:(?!\1).)+)\1'),
            webpage, 'title', default=None,
            group='title') or self._og_search_title(webpage)
        description = self._html_search_meta(
            'description', webpage, 'description'
        )
        view_count = parse_count(self._html_search_regex(
            r'''<strong id="nb-views-number">(.*?)</strong>''',
            webpage, 'view count', default=None
        ))

        thumbnails = []
        for preference, thumbnail in enumerate(('', '169')):
            thumbnail_url = self._search_regex(
                r'setThumbUrl%s\(\s*(["\'])(?P<thumbnail>(?:(?!\1).)+)\1' % thumbnail,
                webpage, 'thumbnail', default=None, group='thumbnail')
            if thumbnail_url:
                thumbnails.append({
                    'url': thumbnail_url,
                    'preference': preference,
                })

        duration = int_or_none(self._og_search_property(
            'duration', webpage, default=None)) or parse_duration(
            self._search_regex(
                r'<span[^>]+class=["\']duration["\'][^>]*>.*?(\d[^<]+)',
                webpage, 'duration', fatal=False))

        formats = []

        video_url = compat_urllib_parse_unquote(self._search_regex(
            r'flv_url=(.+?)&', webpage, 'video URL', default=''))
        if video_url:
            formats.append({
                'url': video_url,
                'format_id': 'flv',
            })

        for kind, _, format_url in re.findall(
                r'setVideo([^(]+)\((["\'])(http.+?)\2\)', webpage):
            format_id = kind.lower()
            if format_id == 'hls':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4',
                    entry_protocol='m3u8_native', m3u8_id='hls', fatal=False))
            elif format_id in ('urllow', 'urlhigh'):
                formats.append({
                    'url': format_url,
                    'format_id': '%s-%s' % (determine_ext(format_url, 'mp4'), format_id[3:]),
                    'quality': -2 if format_id.endswith('low') else None,
                })

        self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': title,
            'description': description,
            'view_count': view_count,
            'duration': duration,
            'thumbnails': thumbnails,
            'age_limit': 18,
        }


class CustomXVideosSearchIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?xvideos\.com/\?(.*?&)?k=(?P<query>[^&]+)(?:[&]|$)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)

        items = re.findall(
            r'<div id=".*?" data-id=".*?"(.*?)<script>',
            webpage, re.S
        )

        if not items:
            raise

        entries = []
        for item in items:
            vid = self._search_regex(
                r'''data-videoid="(.*?)"''', item,
                'vid'
            )
            title = self._search_regex(
                r'''title="(.*?)"''', item,
                'title'
            )
            thumbnail = self._search_regex(
                r'''data-src="(.*?)"''',
                item,
                'thumbnail'
            )
            publishedAt = ''

            description = re.search(
                r'''class="name">(.*?)</span>''',
                item, re.S
            )
            if description:
                description = description.group(1).strip()
            else:
                description = ''
            uri = re.search(r'href="(.*?)"><img', item, re.S)
            if uri:
                uri = uri.group(1)
                item_url = 'https://www.xvideos.com{}'.format(uri)
            else:
                continue

            duration = re.search(
                r'''<span class="duration">(.*?)</span>''',
                item,
                re.S
            )
            if duration:
                duration = duration.group(1).strip()
            else:
                duration = ''
            view_count = self._search_regex(
                r'''class="sprfluous"> - </span> (.*?) <span''',
                item,
                'view count',
                default=''
            )
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
        is_next_page = 'class="no-page next-page"' in webpage
        if is_next_page:
            next_page_str = get_element_by_attribute('class', 'pagination ',
                                                     webpage)
            next_page_str = re.findall(
                r'<li>.*?</li>',
                next_page_str, re.S
            )[-1]
            next_page_str = re.search(r'href="(.*?)"', next_page_str,
                                      re.S).group(1).replace('amp;', '')
            ie_result.update(
                {'next_page': 'https://www.xvideos.com{}'.format(next_page_str)})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
