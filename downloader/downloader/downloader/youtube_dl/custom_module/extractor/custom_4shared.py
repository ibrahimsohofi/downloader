#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor, SearchInfoExtractor
from youtube_dl.utils import (
    get_element_by_class,
    ExtractorError,
    str_to_int
)
from youtube_dl.compat import compat_urllib_parse_urlencode


class Custom4SharedIE(InfoExtractor):
    IE_NAME = 'custom 4shared'
    IE_DESC = 'custom 4shared'
    _VALID_URL1 = r'https?://(?:www\.)?4shared\.com/(?:mp3|video|music)/(?P<item_id>[^&]+)/(?P<name>[^&]?)'
    _VALID_URL2 = r'https?://(?:www\.)?4shared\.com/(?:mp3|video|music)/(?P<item_id>[^&]+)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or\
             re.match(cls._VALID_URL2, url) is not None
        return rs

    def _real_extract(self, query):
        if '.html' in query:
            mobj = re.match(self._VALID_URL1, query)
        else:
            mobj = re.match(self._VALID_URL2, query)
        if mobj is None:
            raise ExtractorError('Invalid parse query "%s"' % query)
        info = {}
        item_id = mobj.group('item_id')
        info['id'] = item_id
        webpage = self._download_webpage(query, item_id)
        title = re.search(r'<title>(.*?)</title>', webpage, re.S)
        if title:
            title = title.group(1)
        else:
            title = self._html_search_meta('og:title', webpage, 'og:title', default='4shared')
        description = self._html_search_meta('description', webpage, 'description')
        info['description'] = description
        info['view_count'] = ''
        thumbnail = re.search(r'data-default-bg="(.*?)"', webpage, re.S)
        if thumbnail:
            thumbnail = thumbnail.group(1)
        else:
            thumbnail = self._html_search_meta('og:image', webpage, 'og:image', default='https://www.4shared.com/images/social/general.png')
        info['thumbnail'] = thumbnail
        duration = self._html_search_regex(
            r'''<input type="hidden" class="jsD1Duration" value="(.*?)"''',
            webpage, 'duration', default=''
        )
        if duration:
            duration = int(duration) // 1000
        else:
            duration = ''
        info['duration'] = duration
        if '/mp3/' in query or 'music' in query:
            search_condition = r'<input type="hidden" class="jsD1PreviewUrl" value="(.*?)"'
            title = title.split('- MP3 Download')[0]
        else:
            search_condition = r"file: '(.*?)',"
            title = title.split('- Download')[0]

        info['title'] = title

        published_info = get_element_by_class(
            'generalUsername', webpage,
        )
        if published_info:
            publishedAt = self._html_search_regex(
                r'''<span>(.*?)</span>''',
                published_info,
                'publishedAt'
            ).strip()
        else:
            publishedAt = self._html_search_regex(
                r'''<span class="jsUploadTime">(.*?)</span>''',
                webpage,
                'publishedAt',
                default=''
            ).strip()
        info['publishedAt'] = publishedAt

        view_count = str_to_int(self._html_search_regex(
            r'''<input type="hidden" class="jsD1Views" value="(.*?)"''',
            webpage,
            'view_count',
            default=''
        ))
        info['view_count'] = view_count

        media = re.search(
            search_condition,
            webpage,
            re.S
        )
        if media:
            media = media.group(1).strip()
            if '/mp3/' in query or 'music' in query:
                rate = re.search(
                    r'<span>Bit rate</span> (.*?) kbps</div>',
                    webpage,
                    re.S
                )
                if rate:
                    rate = rate.group(1)
                else:
                    rate = '192'
                format_item = {
                    'vcodec': 'none',
                    "protocol": "https",
                    "format": rate,
                    "url": media,
                    "ext": "mp3",
                    "format_id": "",
                    "quality": 0
                }
                info['player'] = '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.4shared.com/web/embed/audio/file/{}"></iframe>'.format(item_id)
            else:
                size = re.search(
                    r'class="jsFileSize">(.*?)</span></div>',
                    webpage,
                    re.S
                )
                if size:
                    size = size.group(1)
                    if 'MB' in size:
                        size = size.split(' ')[0]
                        size = float(size) * 1024 * 1024
                    elif 'KB' in size:
                        size = size.split(' ')[0]
                        size = float(size) * 1024
                    else:
                        size = ''
                else:
                    size = ''
                format_item = {
                    'vcodec': 'hkd.av01',
                    "protocol": "https",
                    "format": '',
                    "url": media,
                    "ext": "mp4",
                    "format_id": "",
                    "quality": 0,
                    'filesize': size,
                }
                info['player'] = '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.4shared.com/web/embed/file/{}"></iframe>'.format(item_id)
            info['formats'] = [format_item]
        else:
            raise ExtractorError('Could not get media')
        # print(json.dumps(info))
        return info


class Custom4SharedSearchIE(SearchInfoExtractor, InfoExtractor):
    IE_NAME = 'custom 4shared.com search'
    IE_DESC = 'custom 4shared.com search'
    # '''https://www.4shared.com/web/q/#query=hello&cate_id=1'''
    _VALID_URL1 = r'https?://(?:www\.)?4shared\.com/web/(?:q/|q)#(?:query)=(?P<query>[^&]+)(?:[&]|$)(?:cate_id|category)=(?P<cate_id>\d+)(?:[&]|$)'
    _VALID_URL2 = r'https?://(?:www\.)?4shared\.com/web/(?:q/|q)#(?:query)=(?P<query>[^&]+)(?:[&]|$)(?:cate_id|category)=(?P<cate_id>\d+)(?:[&]|$)(?:page)=(?P<page>[^&]+)'
    _SEARCH_KEY = 'custom 4shared.com search'
    _MAX_PAGE = 10

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or re.match(cls._VALID_URL2, url) is not None
        return rs

    # Methods for following #608
    @staticmethod
    def url_result(item):
        """Returns a URL that points to a page that should be processed"""
        url = item.pop('d1PageUrl')
        video_info = {
            '_type': 'url',
            'url': url,
            'ie_key': Custom4SharedSearchIE.ie_key(),
            'creator': item['user']['userName'] or '',
            'publicdate': item['uploadTime'].split('T')[0],
            'title': item['fileName'],
        }
        video_info.update(item)
        return video_info

    def _real_extract(self, query):
        if 'page=' in query:
            mobj = re.match(self._VALID_URL2, query)
        else:
            mobj = re.match(self._VALID_URL1, query)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % query)
        query = mobj.group('query')
        cate_id = int(mobj.group('cate_id'))
        try:
            page = int(mobj.group('page'))
        except (IndexError, AttributeError) as _:
            page = 1
        if page >= self._MAX_PAGE:
            page = self._MAX_PAGE
        return self._get_page_results(query, cate_id, page)

    def _get_page_results(self, query, cate_id, page):
        '''Get a specifield number of results for a query'''
        if cate_id in (1, 2):
            url_query = {
                'query': query,
                'category': cate_id,
                'view': 'web',
                'offset': (page - 1) * 20,
                'limit': 20,
            }

            param_encode = compat_urllib_parse_urlencode(url_query)
            result_url = 'https://www.4shared.com/web/rest/v1_2/files?{}'\
                .format(param_encode)

            data = self._download_json(
                result_url, video_id='query "%s"' % query,
                note='Downloading page %s' % page,
                errnote='Unable to download API page',
                headers={
                    "Accept": "*/*",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "zh-CN,zh;q=0.9",
                }
            )

            items = data.get('items', [])
            if not items:
                return {
                    '_type': 'playlist',
                    'entries': [],
                    'id': query,
                    'is_next_page': False,
                    'nextPageToken': None,
                    'next_page': None,
                }
                # raise ExtractorError(
                #     '[4shared No item results]', expected=True
                # )

            items = list(map(self.url_result, items))
            is_next_page = len(items) == 20
            ie_result = self.playlist_result(items, query)
            # old
            # ie_result.update({'is_next_page': is_next_page})
            ie_result.update(
                {
                    'is_next_page': is_next_page,
                    'next_page': f'https://www.4shared.com/web/q#query={query}&category={cate_id}&page={page + 1}' if is_next_page else None
                }
            )
            # print(json.dumps(ie_result))
            return ie_result
        else:
            raise ExtractorError('cate_id or category must in range (1, 2)')
