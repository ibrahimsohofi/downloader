# coding: utf-8
from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    determine_ext,
    int_or_none,
    NO_DEFAULT,
    get_element_by_attribute,
    parse_count
)


class CustomXNXXIE(InfoExtractor):
    _VALID_URL = r'https?://(?:video|www)\.xnxx\.com/video-?(?P<id>[0-9a-z]+)/'
    _TESTS = [{
        'url': 'http://www.xnxx.com/video-55awb78/skyrim_test_video',
        'md5': '7583e96c15c0f21e9da3453d9920fbba',
        'info_dict': {
            'id': '55awb78',
            'ext': 'mp4',
            'title': 'Skyrim Test Video',
            'thumbnail': r're:^https?://.*\.jpg',
            'duration': 469,
            'view_count': int,
            'age_limit': 18,
        },
    }, {
        'url': 'http://video.xnxx.com/video1135332/lida_naked_funny_actress_5_',
        'only_matching': True,
    }, {
        'url': 'http://www.xnxx.com/video-55awb78/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        video_id = self._match_id(url)

        webpage = self._download_webpage(url, video_id)

        def get(meta, default=NO_DEFAULT, fatal=True):
            return self._search_regex(
                r'set%s\s*\(\s*(["\'])(?P<value>(?:(?!\1).)+)\1' % meta,
                webpage, meta, default=default, fatal=fatal, group='value')

        title = self._og_search_title(
            webpage, default=None) or get('VideoTitle')
        description = self._html_search_meta(
            'description',
            webpage,
            'description'
        )

        formats = []
        for mobj in re.finditer(
                r'setVideo(?:Url(?P<id>Low|High)|HLS)\s*\(\s*(?P<q>["\'])(?P<url>(?:https?:)?//.+?)(?P=q)', webpage):
            format_url = mobj.group('url')
            if determine_ext(format_url) == 'm3u8':
                formats.extend(self._extract_m3u8_formats(
                    format_url, video_id, 'mp4', entry_protocol='m3u8_native',
                    preference=1, m3u8_id='hls', fatal=False))
            if determine_ext(format_url) != 'm3u8':
                format_id = mobj.group('id')
                if format_id:
                    format_id = format_id.lower()
                formats.append({
                    'url': format_url,
                    'format_id': format_id,
                    'quality': -1 if format_id == 'low' else 0,
                })
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage, default=None) or get(
            'ThumbUrl', fatal=False) or get('ThumbUrl169', fatal=False)
        duration = int_or_none(self._og_search_property('duration', webpage))
        # view_count = str_to_int(self._search_regex(
        #     r'id=["\']nb-views-number[^>]+>([\d,.]+)', webpage, 'view count',
        #     default=None))
        view_count = self._html_search_regex(
            r'''-(.*?)<span class="icon-f icf-eye">''',
            webpage,
            'view count',
            default=None
        )
        if view_count:
            view_count = parse_count(view_count.split('-')[-1])

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'age_limit': 18,
            'formats': formats,
        }


class CustomXNXXSearchIE(InfoExtractor):
    '''https://www.xnxx.com/search/gay/hits/year/10-20min/hd-only/familial_relations'''
    _VALID_URL = r'https?://(?:www)?\.xnxx\.com/search(?:/gay|/shemale)?(?:/hits)?(?:/year|/month)?(?:/0\-10min|/10\-20min|/20min\+)?(?:/hd\-only)?/(?P<query>[^&]+)(?:/\d+)?'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)

        items = re.findall(
            r'<div id=".*?" data-id=".*?"(.*?)<script>xv.thumbs',
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
                r'''title="(.*?)">''', item,
                'title'
            )
            thumbnail = self._search_regex(
                r'''data-src="(.*?)"''',
                item,
                'thumbnail'
            )
            publishedAt = ''

            description = ''
            uri = re.search(r'href="(.*?)"><img', item, re.S)
            if uri:
                uri = uri.group(1)
                item_url = 'https://www.xnxx.com{}'.format(uri)
            else:
                continue

            duration = re.search(
                r'''</span></span>(.*?)<span class="video-hd">''',
                item,
                re.S
            )
            if duration:
                duration = duration.group(1).strip()
            else:
                duration = ''
            view_count = re.search(
                r'''<span class="right">(.*?)<span class="icon-f icf-eye">''',
                item,
                re.S
            )
            if view_count:
                view_count = view_count.group(1).strip()
            else:
                view_count = ''
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
        is_next_page = 'mobile-show-inline icon-f icf-chevron-right' in webpage
        if is_next_page:
            next_page_str = get_element_by_attribute('class', 'pagination ', webpage)
            next_page_str = re.findall(
                r'<li>.*?</li>',
                next_page_str, re.S
            )[-1]
            next_page_str = re.search(r'href="(.*?)"', next_page_str, re.S).group(1).replace('amp;', '')
            ie_result.update({'next_page': 'https://www.xnxx.com{}'.format(next_page_str)})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
