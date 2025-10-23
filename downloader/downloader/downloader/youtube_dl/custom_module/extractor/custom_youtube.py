#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import sys
import re
import socket
import json
import traceback
import os
try:
    # python3
    from urllib import parse
    from urllib.parse import urlencode
except ImportError as ime:
    # python2
    import urlparse as parse
    from urllib import urlencode
import random
import itertools
from youtube_dl.extractor import youtube
from youtube_dl.utils import (
    unescapeHTML,
    orderedSet,
    remove_start,
    GeoUtils,
    uppercase_escape
)
from youtube_dl.compat import (
    compat_parse_qs,
    compat_kwargs,
    compat_HTTPError,
    compat_integer_types,
    compat_urllib_parse_urlparse,
    compat_urllib_parse_unquote_plus,
    compat_urllib_parse_urlencode,
    compat_urllib_parse_unquote,
    compat_urllib_request,
    compat_urllib_error,
    compat_urlparse,
    compat_str,
    compat_chr
)
from youtube_dl.extractor import common
from youtube_dl.utils import (
    parse_count,
    sanitized_Request,
    update_Request,
    update_url_query,
    GeoRestrictedError,
    urlencode_postdata,
    str_to_int,
    # remove_quotes,
    unified_strdate,
    mimetype2ext,
    parse_codecs,
    # get_element_by_id,
    url_or_none,
    try_get,
    clean_html,
    smuggle_url,
    parse_duration,
    unsmuggle_url,
    # GeoRestrictedError,
    ExtractorError,
    compat_http_client,
    error_to_compat_str,
    int_or_none,
    str_or_none,
    qualities,
    float_or_none,
)


class CustomYoutubeEntryListBaseInfoExtractor(youtube.YoutubeBaseInfoExtractor):
    # Extract entries from page with "Load more" button
    def _entries(self, page, playlist_id):
        more_widget_html = content_html = page
        mobj_reg = r'(?:(?:data-uix-load-more-href="[^"]+?;continuation=)|(?:"continuation":"))(?P<more>[^"]+)"'
        for page_num in itertools.count(1):
            for entry in self._process_page(content_html):
                yield entry

            mobj = re.search(mobj_reg, more_widget_html)
            if not mobj:
                break

            count = 0
            retries = 3
            while count <= retries:
                try:
                    # Downloading page may result in intermittent 5xx HTTP error
                    # that is usually worked around with a retry
                    more = self._download_json(
                        'https://www.youtube.com/browse_ajax?ctoken=%s' % mobj.group('more'), playlist_id,
                        'Downloading page #%s%s'
                        % (page_num, ' (retry #%d)' % count if count else ''),
                        transform_source=uppercase_escape,
                        headers=self._YOUTUBE_CLIENT_HEADERS)
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code in (500, 503):
                        count += 1
                        if count <= retries:
                            continue
                    raise

            content_html = more['content_html']
            if not content_html.strip():
                # Some webpages show a "Load more" button but they don't
                # have more videos
                break
            more_widget_html = more['load_more_widget_html']


class CustomYoutubePlaylistBaseInfoExtractor(CustomYoutubeEntryListBaseInfoExtractor):
    # Methods for following #608
    @staticmethod
    def url_result(url, ie=None, video_id=None, video_title=None,
                   video_views=None, video_duration=None,
                   video_description=None, video_publishedAt=None):
        """Returns a URL that points to a page that should be processed"""
        # TODO: ie should be the class used for getting the info
        video_info = {'_type': 'url',
                      'url': url,
                      'ie_key': ie}
        if video_id is not None:
            video_info['id'] = video_id
        if video_title is not None:
            video_info['title'] = video_title
        if video_views is not None:
            video_info['viewCount'] = video_views
        else:
            video_info['viewCount'] = ''
        if video_duration is not None:
            video_info['duration'] = video_duration
        else:
            video_info['duration'] = ''
        if video_description is not None:
            video_info['description'] = video_description
        else:
            video_info['description'] = ''
        if video_publishedAt is not None:
            video_info['publishedAt'] = video_publishedAt
        else:
            video_info['publishedAt'] = ''
        return video_info

    def _process_page(self, content):
        for video_id, video_title, video_views, video_duration,\
                video_description, video_publishedAt in self.extract_videos_from_page(content):
            yield self.url_result(
                video_id, self.ie_key(), video_id,
                video_title, video_views, video_duration,
                video_description, video_publishedAt
            )

    def extract_videos_from_page_impl(
            self, video_re, page,
            ids_in_page, titles_in_page, views_in_page,
            durations_in_page, descriptions_in_page, publishedAts_in_page):
        full_re = r'<h3 class="yt-lockup-title ">(.*?)</div></div></div></div>'
        infos = re.finditer(full_re, page, re.DOTALL)
        for info in infos:
            value = info.group()
            mobj = re.search(video_re, value, re.DOTALL)
            if 'index' in mobj.groupdict() and mobj.group('id') == '0':
                continue
            video_id = mobj.group('id')
            video_title = unescapeHTML(
                mobj.group('title')) if 'title' in mobj.groupdict() else None
            video_views = re.search(r'</li><li>(.+?) views</li>', value)
            if not video_views:
                video_views = None
            else:
                video_views = video_views.group(1).replace(',', '')
            video_duration = re.search(r'Duration: (.*?).</span>', value)
            if not video_duration:
                video_duration = None
            else:
                video_duration = video_duration.group(1)
            video_description = re.search(r'<div class="yt-lockup-description yt-ui-ellipsis yt-ui-ellipsis-2" dir="ltr">(.*?)</div>', value)
            if not video_description:
                video_description = None
            else:
                video_description = video_description.group(1)
            video_publishedAt = re.search(r'<ul class="yt-lockup-meta-info"><li>(.*?)</li>', value)
            if not video_publishedAt:
                video_publishedAt = None
            else:
                video_publishedAt = video_publishedAt.group(1)
            if not video_views:
                continue
            if video_title:
                video_title = video_title.strip()
            if video_title == '► Play all':
                video_title = None
            if not video_title:
                continue
            try:
                idx = ids_in_page.index(video_id)
                if video_title and not titles_in_page[idx]:
                    titles_in_page[idx] = video_title
            except ValueError:
                ids_in_page.append(video_id)
                titles_in_page.append(video_title)
                views_in_page.append(video_views)
                durations_in_page.append(video_duration)
                descriptions_in_page.append(video_description)
                publishedAts_in_page.append(video_publishedAt)

    def extract_videos_from_page(self, page):
        ids_in_page = []
        titles_in_page = []
        views_in_page = []
        durations_in_page = []
        descriptions_in_page = []
        publishedAts_in_page = []
        self.extract_videos_from_page_impl(
            self._VIDEO_RE, page, ids_in_page,
            titles_in_page, views_in_page, durations_in_page,
            descriptions_in_page, publishedAts_in_page
        )
        return zip(
            ids_in_page, titles_in_page, views_in_page,
            durations_in_page, descriptions_in_page, publishedAts_in_page
        )


class CustomYoutubePlaylistsBaseInfoExtractor(CustomYoutubeEntryListBaseInfoExtractor):
    def _process_page(self, content):
        for playlist_id in orderedSet(re.findall(
                r'<h3[^>]+class="[^"]*yt-lockup-title[^"]*"[^>]*><a[^>]+href="/?playlist\?list=([0-9A-Za-z-_]{10,})"',
                content)):
            yield self.url_result(
                'https://www.youtube.com/playlist?list=%s' % playlist_id, 'YoutubePlaylist')

    def _real_extract(self, url):
        playlist_id = self._match_id(url)
        webpage = self._download_webpage(url, playlist_id)
        title = self._og_search_title(webpage, fatal=False)
        return self.playlist_result(self._entries(webpage, playlist_id), playlist_id, title)


class CustomYoutubeSearchBaseInfoExtractor(CustomYoutubePlaylistBaseInfoExtractor):
    _VIDEO_RE = r'href="\s*/watch\?v=(?P<id>[0-9A-Za-z_-]{11})(?:[^"]*"[^>]+\btitle="(?P<title>[^"]+))?'


class CustomYoutubeSearchIE(common.SearchInfoExtractor, youtube.YoutubeBaseInfoExtractor):
    IE_DESC = 'custom YouTube.com searches'
    # there doesn't appear to be a real limit, for example if you search for
    # 'python' you get more than 8.000.000 results
    # _MAX_RESULTS = float('inf')
    _VALID_URL1 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)'
    _VALID_URL2 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:gl)=(?P<gl>[^&]+)(?:[&]|$)'
    _VALID_URL3 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:token)=(?P<token>[^&]+)(?:[&]|$)'
    _VALID_URL4 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:gl)=(?P<gl>[^&]+)(?:[&]|$)(?:token)=(?P<token>[^&]+)(?:[&]|$)'
    _VALID_URL5 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:sp)=(?P<sp>[^&]+)(?:[&]|$)'
    _VALID_URL6 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:gl)=(?P<gl>[^&]+)(?:[&]|$)(?:sp)=(?P<sp>[^&]+)(?:[&]|$)'
    _VALID_URL7 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:sp)=(?P<sp>[^&]+)(?:[&]|$)(?:token)=(?P<token>[^&]+)(?:[&]|$)'
    _VALID_URL8 = r'https?://(?:www\.)?youtube\.com/results\?(.*?&)?(?:search_query|q)=(?P<query>.*?)(?:[&]|$)(?:gl)=(?P<gl>[^&]+)(?:[&]|$)(?:sp)=(?P<sp>[^&]+)(?:[&]|$)(?:token)=(?P<token>[^&]+)(?:[&]|$)'
    _MAX_RESULTS = 51
    IE_NAME = 'custom youtube:search'
    _SEARCH_KEY = 'custom ytsearch'
    _SEARCH_PARAMS = None
    _EXTRA_QUERY_ARGS = {}
    _TESTS = []

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or\
             re.match(cls._VALID_URL2, url) is not None or \
             re.match(cls._VALID_URL3, url) is not None or \
             re.match(cls._VALID_URL4, url) is not None or \
             re.match(cls._VALID_URL5, url) is not None or \
             re.match(cls._VALID_URL6, url) is not None or \
             re.match(cls._VALID_URL7, url) is not None or \
             re.match(cls._VALID_URL8, url) is not None
        return rs

    def _download_json_handle(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (JSON object, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        json_string, urlh = res
        try:
            json.loads(json_string)
            return self._parse_json(
                json_string, video_id, transform_source=transform_source,
                fatal=fatal), urlh
        except Exception as e:
            # is a webpage, not a json
            return json_string, urlh

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}, expected_status=None):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            if 'X-Forwarded-For' not in headers:
                headers['X-Forwarded-For'] = self._x_forwarded_for_ip

        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
                url_or_request = compat_urllib_parse_unquote_plus(
                    url_or_request)
            if data is not None or headers:
                url_or_request = compat_urllib_parse_unquote_plus(
                    url_or_request)
                url_or_request = sanitized_Request(url_or_request, data, headers)
        try:
            return self._downloader.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if isinstance(err, compat_urllib_error.HTTPError):
                def __can_accept_status_code(err, expected_status):
                    assert isinstance(err, compat_urllib_error.HTTPError)
                    if expected_status is None:
                        return False
                    if isinstance(expected_status, compat_integer_types):
                        return err.code == expected_status
                    elif isinstance(expected_status, (list, tuple)):
                        return err.code in expected_status
                    elif callable(expected_status):
                        return expected_status(err.code) is True
                    else:
                        assert False
                if __can_accept_status_code(err, expected_status):
                    # Retain reference to error to prevent file object from
                    # being closed before it can be read. Works around the
                    # effects of <https://bugs.python.org/issue15002>
                    # introduced in Python 3.4.1.
                    err.fp._error = err
                    return err.fp

            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self._downloader.report_warning(errmsg)
                return False

    def _real_extract(self, url):
        if 'gl=' not in url and 'sp=' not in url and 'token=' not in url:
            mobj = re.match(self._VALID_URL1, url)
        elif 'gl=' in url and 'sp=' not in url and 'token=' not in url:
            mobj = re.match(self._VALID_URL2, url)
        elif 'gl=' not in url and 'sp=' not in url and 'token=' in url:
            mobj = re.match(self._VALID_URL3, url)
        elif 'gl=' in url and 'sp=' not in url and 'token=' in url:
            mobj = re.match(self._VALID_URL4, url)
        elif 'gl=' not in url and 'sp=' in url and 'token=' not in url:
            mobj = re.match(self._VALID_URL5, url)
        elif 'gl=' in url and 'sp=' in url and 'token=' not in url:
            mobj = re.match(self._VALID_URL6, url)
        elif 'gl=' not in url and 'sp=' in url and 'token=' in url:
            mobj = re.match(self._VALID_URL7, url)
        elif 'gl=' in url and 'sp=' in url and 'token=' in url:
            mobj = re.match(self._VALID_URL8, url)
        else:
            raise ExtractorError('Invalid search query "%s"' % url)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % url)

        try:
            query = mobj.group('query')
        except (IndexError, AttributeError)as _:
            raise ExtractorError(
                "Can`t found query, please pass the query param"
            )
        # try:
        #     gl = mobj.group('gl')
        # except (IndexError, AttributeError) as _:
        #     gl = None
        gl = None
        try:
            sp = mobj.group('sp')
        except (IndexError, AttributeError) as _:
            sp = None
        try:
            token = mobj.group('token')
        except (IndexError, AttributeError, ValueError) as _:
            token = ''
        return self._get_page_results1(url, query, gl, sp, token)
        # return self._get_page_results(query, gl, sp, 1)

    def _get_page_results1(self, url, query, gl, sp, token):
        data = {
            'context': {
                'client': {
                    'clientName': 'WEB',
                    'clientVersion': '2.20201021.03.00',
                }
            },
            'query': query,
        }
        if gl:
            data['context']['client']['gl'] = gl
        if sp:
            data['params'] = compat_urllib_parse_unquote(sp)
        if token:
            data['continuation'] = token
        else:
            return self._get_page_results(url, query, gl, sp, 1)
        search = self._download_json(
            'https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
            video_id='query "%s"' % query,
            note='Downloading token page %s' % token,
            errnote='Unable to download API page', fatal=True,
            data=json.dumps(data).encode('utf8'),
            headers={'content-type': 'application/json'})
        if search:
            slr_contents = try_get(
                search,
                (lambda x: x['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'],
                 lambda x: x['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']),
                list)
            if not slr_contents:
                raise ExtractorError('Can`t get slr_contents')
            isr_contents = try_get(
                slr_contents,
                lambda x: x[0]['itemSectionRenderer']['contents'] if len(slr_contents) == 2 else x[1]['itemSectionRenderer']['contents'],
                list)
            if not isr_contents:
                if 'messageRenderer' in str(slr_contents) and 'No more results' in str(slr_contents):
                    return {
                        '_type': 'playlist',
                        'entries': [],
                        'id': query,
                        'is_next_page': False,
                        'nextPageToken': None,
                        'next_page': None,
                    }
                raise ExtractorError('Can`t get isr_contents')
            videos = []
            for content in isr_contents:
                if not isinstance(content, dict):
                    continue

                video = content.get('videoRenderer')
                if not isinstance(video, dict):
                    continue
                video_id = video.get('videoId')
                if not video_id:
                    continue
                title = try_get(video, lambda x: x['title']['runs'][0]['text'], compat_str)
                description = try_get(video, lambda x: x['descriptionSnippet']['runs'][0]['text'], compat_str)
                duration = try_get(video, lambda x: x['lengthText']['simpleText'], compat_str)
                view_count_text = try_get(video, lambda x: x['viewCountText']['simpleText'], compat_str) or ''
                if 'views' in view_count_text:
                    view_count = str(parse_count(view_count_text.replace('views', '')))
                else:
                    view_count = '0'
                publishedAt = try_get(video, lambda x: x['publishedTimeText']['simpleText'], compat_str) or ''
                info = {
                    '_type': 'url',
                    'url': video_id,
                    'ie_key': self.ie_key(),
                    'id': video_id,
                    'title': title,
                    'viewCount': view_count,
                    'duration': duration,
                    'description': description,
                    'publishedAt': publishedAt,
                }
                videos.append(info)
            token = try_get(
                slr_contents,
                lambda x: x[1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'] if len(slr_contents) == 2 else x[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'],
                compat_str)
            if not token:
                next_page_info = {
                    'is_next_page': False,
                    'nextPageToken': None,
                    'next_page': None,
                }
            else:
                full_token = re.sub(r'token=[^&]+', f'token={token}', url)
                next_page_info = {
                    'is_next_page': True,
                    'nextPageToken': token,
                    'next_page': full_token
                }
            ie_result = self.playlist_result(videos, query)
            ie_result.update(next_page_info)
            return ie_result
            # print(json.dumps(ie_result))
        else:
            raise ExtractorError('Can`t download json result, you can retry it until got result!')

    def _get_page_results(self, url, query, gl, sp, page):
        """Get a specified number of results for a query"""
        videos = []
        url_query = {
            'search_query': query.replace(' ', '%20').encode('utf-8'),
            'page': str(page).encode('utf-8'),
            # 'disable_polymer': b'true',
        }
        if gl:
            url_query.update({'gl': gl})
        if sp:
            url_query.update({'sp': sp})
        url_query.update(self._EXTRA_QUERY_ARGS)
        result_url = 'https://www.youtube.com/results?' + compat_urllib_parse_urlencode(url_query)

        data = self._download_json(
            result_url, video_id='query "%s"' % query,
            note='Downloading page %s' % page,
            errnote='Unable to download API page',
            query={'spf': 'navigate'})
        if isinstance(data, list):
            html_content = data[1]['body']['content']
            if 'class="search-message' in html_content:
                raise ExtractorError(
                    '[youtube] No video results', expected=True)

            new_videos = list(self._process_page(html_content))
            is_next_page = len(new_videos) > 6
            videos += new_videos
            ie_result = self.playlist_result(videos, query)
            ie_result.update({'is_next_page': is_next_page})
            return ie_result
            # print(json.dumps(ie_result))
        elif isinstance(data, compat_str):
            json_data = re.search('var ytInitialData = (.+?)};', data, re.S)
            if not json_data:
                raise ExtractorError(data)
            json_data = json_data.group(1).strip() + '}'
            json_data = json.loads(json_data)
            contents = json_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
            if 'No results found' in str(contents) and 'Try different keywords or remove search filters' in str(contents):
                raise ExtractorError('No results found, Try different keywords or remove search filters')
                # return {
                #     '_type': 'playlist',
                #     'entries': [],
                #     'id': query,
                #     'is_next_page': False,
                #     'nextPageToken': None,
                #     'next_page': None,
                # }
            items = contents[0]['itemSectionRenderer']['contents'] if len(contents) == 2 else contents[1]['itemSectionRenderer']['contents']
            items = [item['videoRenderer'] for item in items if 'videoRenderer' in item]
            for item in items:
                vid = item['videoId']
                title = item['title']['runs'][0]['text']
                if title == '► Play all':
                    continue
                if item.get('viewCountText'):
                    views = item['viewCountText'].get('simpleText', '').replace('views', '')
                    views = str(parse_count(views))
                else:
                    views = ''
                if item.get('lengthText'):
                    if item['lengthText'].get('simpleText'):
                        duration = item['lengthText']['simpleText']
                    else:
                        duration = ''
                else:
                    duration = ''
                if item.get('descriptionSnippet'):
                    description = ' '.join([iw['text'] for iw in item['descriptionSnippet']['runs']])
                else:
                    description = title
                publishedAt = item.get('publishedTimeText', {'simpleText': ''})['simpleText']
                info = {
                    '_type': 'url',
                    'url': vid,
                    'ie_key': self.ie_key(),
                    'id': vid,
                    'title': title,
                    'viewCount': views,
                    'duration': duration,
                    'description': description,
                    'publishedAt': publishedAt,
                }
                videos.append(info)
            try:
                token = contents[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'] or ''
                if len(videos) < 5:
                    token = ''
            except IndexError as ie:
                token = None
            if not token:
                next_page_info = {
                    'is_next_page': False,
                    'nextPageToken': None,
                    'next_page': None,
                }
            else:
                full_token = f'{url}&token={token}'
                next_page_info = {
                    'is_next_page': True,
                    'nextPageToken': token,
                    'next_page': full_token
                }
            ie_result = self.playlist_result(videos, query)
            ie_result.update(next_page_info)
            return ie_result
            # print(json.dumps(ie_result))
        else:
            raise ExtractorError(f'error result, the data is {data}')


class CustomYoutubeMusicSearchIE(common.SearchInfoExtractor, youtube.YoutubeBaseInfoExtractor):
    IE_DESC = 'custom music.youtube.com searches'
    # there doesn't appear to be a real limit, for example if you search for
    # 'python' you get more than 8.000.000 results
    # _MAX_RESULTS = float('inf')
    _VALID_URL = r'https?://music\.youtube\.com/search\?q=(?P<query>.*?)(?:[&]|$)'
    _MAX_RESULTS = 51
    IE_NAME = 'custom youtube music:search'
    _SEARCH_KEY = 'custom ytsearch:music'
    _SEARCH_PARAMS = None
    _EXTRA_QUERY_ARGS = {}
    _TESTS = []

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _download_json_handle(
            self, url_or_request, video_id, note='Downloading JSON metadata',
            errnote='Unable to download JSON metadata', transform_source=None,
            fatal=True, encoding=None, data=None, headers={}, query={},
            expected_status=None):
        """
        Return a tuple (JSON object, URL handle).

        See _download_webpage docstring for arguments specification.
        """
        res = self._download_webpage_handle(
            url_or_request, video_id, note, errnote, fatal=fatal,
            encoding=encoding, data=data, headers=headers, query=query,
            expected_status=expected_status)
        if res is False:
            return res
        json_string, urlh = res
        try:
            json.loads(json_string)
            return self._parse_json(
                json_string, video_id, transform_source=transform_source,
                fatal=fatal), urlh
        except Exception as e:
            # is a webpage, not a json
            return json_string, urlh

    def _request_webpage(self, url_or_request, video_id, note=None, errnote=None, fatal=True, data=None, headers={}, query={}, expected_status=None):
        """
        Return the response handle.

        See _download_webpage docstring for arguments specification.
        """
        if note is None:
            self.report_download_webpage(video_id)
        elif note is not False:
            if video_id is None:
                self.to_screen('%s' % (note,))
            else:
                self.to_screen('%s: %s' % (video_id, note))

        # Some sites check X-Forwarded-For HTTP header in order to figure out
        # the origin of the client behind proxy. This allows bypassing geo
        # restriction by faking this header's value to IP that belongs to some
        # geo unrestricted country. We will do so once we encounter any
        # geo restriction error.
        if self._x_forwarded_for_ip:
            if 'X-Forwarded-For' not in headers:
                headers['X-Forwarded-For'] = self._x_forwarded_for_ip

        if isinstance(url_or_request, compat_urllib_request.Request):
            url_or_request = update_Request(
                url_or_request, data=data, headers=headers, query=query)
        else:
            if query:
                url_or_request = update_url_query(url_or_request, query)
                url_or_request = compat_urllib_parse_unquote_plus(
                    url_or_request)
            if data is not None or headers:
                url_or_request = compat_urllib_parse_unquote_plus(
                    url_or_request)
                url_or_request = sanitized_Request(url_or_request, data, headers)
        try:
            return self._downloader.urlopen(url_or_request)
        except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
            if isinstance(err, compat_urllib_error.HTTPError):
                def __can_accept_status_code(err, expected_status):
                    assert isinstance(err, compat_urllib_error.HTTPError)
                    if expected_status is None:
                        return False
                    if isinstance(expected_status, compat_integer_types):
                        return err.code == expected_status
                    elif isinstance(expected_status, (list, tuple)):
                        return err.code in expected_status
                    elif callable(expected_status):
                        return expected_status(err.code) is True
                    else:
                        assert False
                if __can_accept_status_code(err, expected_status):
                    # Retain reference to error to prevent file object from
                    # being closed before it can be read. Works around the
                    # effects of <https://bugs.python.org/issue15002>
                    # introduced in Python 3.4.1.
                    err.fp._error = err
                    return err.fp

            if errnote is False:
                return False
            if errnote is None:
                errnote = 'Unable to download webpage'

            errmsg = '%s: %s' % (errnote, error_to_compat_str(err))
            if fatal:
                raise ExtractorError(errmsg, sys.exc_info()[2], cause=err)
            else:
                self._downloader.report_warning(errmsg)
                return False

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % url)

        try:
            query = mobj.group('query')
        except (IndexError, AttributeError)as _:
            raise ExtractorError(
                "Can`t found query, please pass the query param"
            )
        # try:
        #     gl = mobj.group('gl')
        # except (IndexError, AttributeError) as _:
        #     gl = None
        gl = None
        try:
            sp = mobj.group('sp')
        except (IndexError, AttributeError) as _:
            sp = None
        try:
            token = mobj.group('token')
        except (IndexError, AttributeError, ValueError) as _:
            token = ''
        return self._get_page_results1(url, query, gl, sp, token)
        # return self._get_page_results(query, gl, sp, 1)

    def _get_page_results1(self, url, query, gl, sp, token):
        data = {"context": {"client": {"clientName": "WEB_REMIX", "clientVersion": "1.20210802.00.00"}}, "query": query, "params": "EgWKAQIIAWoKEAMQBBAFEAkQCg%3D%3D"}
        # data['params'] = 'EgWKAQIIAWoKEAMQBBAFEAkQCg%3D%3D'
        if token:
            data['continuation'] = token
        search = self._download_json(
            'https://music.youtube.com/youtubei/v1/search?key=AIzaSyC9XL3ZjWddXya6X74dJoCTL-WEYFDNX30',
            # 'https://www.youtube.com/youtubei/v1/search?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
            video_id='query "%s"' % query,
            note='Downloading token page %s' % token,
            errnote='Unable to download API page', fatal=True,
            data=json.dumps(data).encode('utf8'),
            headers={'content-type': 'application/json'})
        if search:
            slr_contents = try_get(
                search,
                (lambda x: x['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents'],
                 lambda x: x['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']),
                list)
            if not slr_contents:
                raise ExtractorError('Can`t get slr_contents')
            isr_contents = try_get(
                slr_contents,
                lambda x: x[0]['itemSectionRenderer']['contents'] if len(slr_contents) == 2 else x[1]['itemSectionRenderer']['contents'],
                list)
            if not isr_contents:
                if 'messageRenderer' in str(slr_contents) and 'No more results' in str(slr_contents):
                    return {
                        '_type': 'playlist',
                        'entries': [],
                        'id': query,
                        'is_next_page': False,
                        'nextPageToken': None,
                        'next_page': None,
                    }
                raise ExtractorError('Can`t get isr_contents')
            videos = []
            for content in isr_contents:
                if not isinstance(content, dict):
                    continue

                video = content.get('videoRenderer')
                if not isinstance(video, dict):
                    continue
                video_id = video.get('videoId')
                if not video_id:
                    continue
                title = try_get(video, lambda x: x['title']['runs'][0]['text'], compat_str)
                description = try_get(video, lambda x: x['descriptionSnippet']['runs'][0]['text'], compat_str)
                duration = try_get(video, lambda x: x['lengthText']['simpleText'], compat_str)
                view_count_text = try_get(video, lambda x: x['viewCountText']['simpleText'], compat_str) or ''
                if 'views' in view_count_text:
                    view_count = str(parse_count(view_count_text.replace('views', '')))
                else:
                    view_count = '0'
                publishedAt = try_get(video, lambda x: x['publishedTimeText']['simpleText'], compat_str) or ''
                info = {
                    '_type': 'url',
                    'url': video_id,
                    'ie_key': self.ie_key(),
                    'id': video_id,
                    'title': title,
                    'viewCount': view_count,
                    'duration': duration,
                    'description': description,
                    'publishedAt': publishedAt,
                }
                videos.append(info)
            token = try_get(
                slr_contents,
                lambda x: x[1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'] if len(slr_contents) == 2 else x[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'],
                compat_str)
            if not token:
                next_page_info = {
                    'is_next_page': False,
                    'nextPageToken': None,
                    'next_page': None,
                }
            else:
                full_token = re.sub(r'token=[^&]+', f'token={token}', url)
                next_page_info = {
                    'is_next_page': True,
                    'nextPageToken': token,
                    'next_page': full_token
                }
            ie_result = self.playlist_result(videos, query)
            ie_result.update(next_page_info)
            return ie_result
            # print(json.dumps(ie_result))
        else:
            raise ExtractorError('Can`t download json result, you can retry it until got result!')

    def _get_page_results(self, url, query, gl, sp, page):
        """Get a specified number of results for a query"""
        videos = []
        url_query = {
            'search_query': query.replace(' ', '%20').encode('utf-8'),
            'page': str(page).encode('utf-8'),
            # 'disable_polymer': b'true',
        }
        if gl:
            url_query.update({'gl': gl})
        if sp:
            url_query.update({'sp': sp})
        url_query.update(self._EXTRA_QUERY_ARGS)
        result_url = 'https://www.youtube.com/results?' + compat_urllib_parse_urlencode(url_query)

        data = self._download_json(
            result_url, video_id='query "%s"' % query,
            note='Downloading page %s' % page,
            errnote='Unable to download API page',
            query={'spf': 'navigate'})
        if isinstance(data, list):
            html_content = data[1]['body']['content']
            if 'class="search-message' in html_content:
                raise ExtractorError(
                    '[youtube] No video results', expected=True)

            new_videos = list(self._process_page(html_content))
            is_next_page = len(new_videos) > 6
            videos += new_videos
            ie_result = self.playlist_result(videos, query)
            ie_result.update({'is_next_page': is_next_page})
            return ie_result
            # print(json.dumps(ie_result))
        elif isinstance(data, compat_str):
            json_data = re.search('var ytInitialData = (.+?)};', data, re.S)
            if not json_data:
                raise ExtractorError(data)
            json_data = json_data.group(1).strip() + '}'
            json_data = json.loads(json_data)
            contents = json_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
            if 'No results found' in str(contents) and 'Try different keywords or remove search filters' in str(contents):
                raise ExtractorError('No results found, Try different keywords or remove search filters')
                # return {
                #     '_type': 'playlist',
                #     'entries': [],
                #     'id': query,
                #     'is_next_page': False,
                #     'nextPageToken': None,
                #     'next_page': None,
                # }
            items = contents[0]['itemSectionRenderer']['contents'] if len(contents) == 2 else contents[1]['itemSectionRenderer']['contents']
            items = [item['videoRenderer'] for item in items if 'videoRenderer' in item]
            for item in items:
                vid = item['videoId']
                title = item['title']['runs'][0]['text']
                if title == '► Play all':
                    continue
                if item.get('viewCountText'):
                    views = item['viewCountText'].get('simpleText', '').replace('views', '')
                    views = str(parse_count(views))
                else:
                    views = ''
                if item.get('lengthText'):
                    if item['lengthText'].get('simpleText'):
                        duration = item['lengthText']['simpleText']
                    else:
                        duration = ''
                else:
                    duration = ''
                if item.get('descriptionSnippet'):
                    description = ' '.join([iw['text'] for iw in item['descriptionSnippet']['runs']])
                else:
                    description = title
                publishedAt = item.get('publishedTimeText', {'simpleText': ''})['simpleText']
                info = {
                    '_type': 'url',
                    'url': vid,
                    'ie_key': self.ie_key(),
                    'id': vid,
                    'title': title,
                    'viewCount': views,
                    'duration': duration,
                    'description': description,
                    'publishedAt': publishedAt,
                }
                videos.append(info)
            try:
                token = contents[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token'] or ''
                if len(videos) < 5:
                    token = ''
            except IndexError as ie:
                token = None
            if not token:
                next_page_info = {
                    'is_next_page': False,
                    'nextPageToken': None,
                    'next_page': None,
                }
            else:
                full_token = f'{url}&token={token}'
                next_page_info = {
                    'is_next_page': True,
                    'nextPageToken': token,
                    'next_page': full_token
                }
            ie_result = self.playlist_result(videos, query)
            ie_result.update(next_page_info)
            return ie_result
            # print(json.dumps(ie_result))
        else:
            raise ExtractorError(f'error result, the data is {data}')


class CustomYoutubePlaylistIE(CustomYoutubePlaylistBaseInfoExtractor):
    IE_DESC = 'custom YouTube.com playlists'
    IE_NAME = 'custom youtube:playlist'
    _TEMPLATE_URL = 'https://www.youtube.com/playlist?list=%s'
    _VIDEO_RE_TPL = r'href="\s*/watch\?v=%s(?:&amp;(?:[^"]*?index=(?P<index>\d+))?(?:[^>]+>(?P<title>[^<]+))?)?'
    _VIDEO_RE = _VIDEO_RE_TPL % r'(?P<id>[0-9A-Za-z_-]{11})'
    _VALID_URL = r"""(?x)(?:
                            (?:https?://)?
                            (?:\w+\.)?
                            (?:
                                (?:
                                    youtube(?:kids)?\.com|
                                    invidio\.us
                                )
                                /
                                (?:
                                   (?:course|view_play_list|my_playlists|artist|playlist|watch|embed/(?:videoseries|[0-9A-Za-z_-]{11}))
                                   \? (?:.*?[&;])*? (?:p|a|list)=
                                |  p/
                                )|
                                youtu\.be/[0-9A-Za-z_-]{11}\?.*?\blist=
                            )
                            (
                                (?:PL|LL|EC|UU|FL|RD|UL|TL|PU|OLAK5uy_)?[0-9A-Za-z-_]{10,}
                                # Top tracks, they can also include dots
                                |(?:MC)[\w\.]*
                            )
                            .*
                         |
                            (%(playlist_id)s)
                         )""" % {
        'playlist_id': r'(?:PL|LL|EC|UU|FL|RD|UL|TL|PU|OLAK5uy_)[0-9A-Za-z-_]{10,}'}
    _VALID_URL1 = r'https?://(?:www\.)?youtube\.com/playlist\?token=(?P<token>[^&]+)(?:[&]|$)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None or \
             re.match(cls._VALID_URL1, url) is not None
        return rs

    def _entries_one_page(self, page):
        for entry in self._process_page(page):
            yield entry

    # def _real_initialize(self):
    #     self._login()

    def _process_page(self, content):
        for video_id, video_title, video_views, video_duration in self.extract_videos_from_page(content):
            yield self.url_result(
                video_id, self.ie_key(), video_id,
                video_title, video_views, video_duration
            )

    def extract_videos_from_page(self, items):
        ids_in_page = []
        titles_in_page = []
        views_in_page, durations_in_page = [], []

        for item in items:
            video_id = item['playlistVideoRenderer']['videoId']
            video_title = item['playlistVideoRenderer']['title']['runs'][0]['text']
            if video_title == '[Deleted video]':
                continue
            ids_in_page.append(video_id)
            titles_in_page.append(video_title)
            if item['playlistVideoRenderer'].get('lengthText'):
                duration = item['playlistVideoRenderer']['lengthText'].get('simpleText', '')
            else:
                duration = ''
            durations_in_page.append(duration)
            views_in_page.append('')

        return zip(ids_in_page, titles_in_page, views_in_page, durations_in_page)

    def _extract_playlist(self, playlist_id):
        url = self._TEMPLATE_URL % playlist_id
        page = self._download_webpage(url, playlist_id)

        # the yt-alert-message now has tabindex attribute (see https://github.com/ytdl-org/youtube-dl/issues/11604)
        for match in re.findall(r'<div class="yt-alert-message"[^>]*>([^<]+)</div>', page):
            match = match.strip()
            # Check if the playlist exists or is private
            mobj = re.match(r'[^<]*(?:The|This) playlist (?P<reason>does not exist|is private)[^<]*', match)
            if mobj:
                reason = mobj.group('reason')
                message = 'This playlist %s' % reason
                if 'private' in reason:
                    message += ', use --username or --netrc to access it'
                message += '.'
                raise ExtractorError(message, expected=True)
            elif re.match(r'[^<]*Invalid parameters[^<]*', match):
                raise ExtractorError(
                    'Invalid parameters. Maybe URL is incorrect.',
                    expected=True)
            elif re.match(r'[^<]*Choose your language[^<]*', match):
                continue
            else:
                self.report_warning('Youtube gives an alert message: ' + match)

        playlist_title = self._html_search_meta(
            ('og:title', 'title'),
            page, 'title', default=None)

        has_videos = True

        content = self._html_search_regex(
            (r'ytInitialData\s?=\s?(.*?)}};', r'window\[\"ytInitialData\"\]\s?=\s(.*?)}};'),
            page, 'content', default=dict()
        )
        if content:
            content += '}}'
        content = json.loads(content)
        if 'contents' in content:
            items = content['contents']['twoColumnBrowseResultsRenderer']['tabs'][0]['tabRenderer']['content']['sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents'][0]['playlistVideoListRenderer']['contents']
            if 'continuationItemRenderer' in items[-1]:
                next_page = items[-1]['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
                next_page = f'https://www.youtube.com/playlist?token={next_page}'
                items.pop()
            else:
                next_page = None
            playlist = self.playlist_result(
                self._entries_one_page(items), playlist_id, playlist_title)
            playlist['entries'] = list(playlist['entries'])

            return has_videos, next_page, playlist
        else:
            return False, None, []

    def _check_download_just_video(self, url, playlist_id):
        # Check if it's a video-specific URL
        query_dict = compat_urlparse.parse_qs(compat_urlparse.urlparse(url).query)
        video_id = query_dict.get('v', [None])[0] or self._search_regex(
            r'(?:(?:^|//)youtu\.be/|youtube\.com/embed/(?!videoseries))([0-9A-Za-z_-]{11})', url,
            'video id', default=None)
        if video_id:
            if self._downloader.params.get('noplaylist'):
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
                return video_id, self.url_result(video_id, 'Youtube', video_id=video_id)
            else:
                self.to_screen('Downloading playlist %s - add --no-playlist to just download video %s' % (playlist_id, video_id))
                return video_id, None
        return None, None

    def _real_extract(self, url):
        # Extract playlist id
        if 'youtube.com/playlist?token=' in url:
            mobj = re.match(self._VALID_URL1, url)
            token = mobj.group('token')
            data = {
                'context': {
                    'client': {
                        'clientName': 'WEB',
                        'clientVersion': '2.20201109.05.01',
                        'gl': 'US'
                    }
                },
                'continuation': token
            }
            browse = self._download_json(
                'https://www.youtube.com/youtubei/v1/browse?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8',
                video_id='query playlist api page "%s"' % token,
                note='Downloading token page %s' % token,
                errnote='Unable to download API page', fatal=True,
                data=json.dumps(data).encode('utf8'),
                headers={'content-type': 'application/json'})
            if browse:
                items = try_get(
                    browse,
                    (lambda x: x['contents']['twoColumnSearchResultsRenderer'][
                        'primaryContents']['sectionListRenderer']['contents'],
                     lambda x: x['onResponseReceivedActions'][0][
                         'appendContinuationItemsAction']['continuationItems']),
                    list)
                if not items:
                    raise ExtractorError('Can`t get items')
                if 'continuationItemRenderer' in items[-1]:
                    next_page = items[-1]['continuationItemRenderer'][
                        'continuationEndpoint']['continuationCommand']['token']
                    next_page = f'https://www.youtube.com/playlist?token={next_page}'
                    items.pop()
                else:
                    next_page = None
                playlist = self.playlist_result(
                    self._entries_one_page(items), token, token)
                playlist['entries'] = list(playlist['entries'])
                is_next_page = True if next_page else False
                playlist.update({
                    'is_next_page': is_next_page,
                    'next_page': next_page
                })
                return playlist
                # print(json.dumps(playlist))
            else:
                raise ExtractorError(
                    'Can`t download json result, you can retry it until got result!')
        else:
            mobj = re.match(self._VALID_URL, url)
            if mobj is None:
                raise ExtractorError('Invalid URL: %s' % url)

            playlist_id = mobj.group(1) or mobj.group(2)
            # if playlist_id.startswith(('RD', 'UL', 'PU')):
            #     # Mixes require a custom extraction process
            #     return self._extract_mix(playlist_id)

            has_videos, next_page, playlist = self._extract_playlist(playlist_id)
            if has_videos:
                is_next_page = True if next_page else False
                playlist.update({
                    'is_next_page': is_next_page,
                    'next_page': next_page
                })
                # print(json.dumps(playlist))
                return playlist


class CustomYoutubeIE(youtube.YoutubeIE):
    def __maybe_fake_ip_and_retry(self, countries):
        if (not self._downloader.params.get('geo_bypass_country', None)
                and self._GEO_BYPASS
                and self._downloader.params.get('geo_bypass', True)
                and not self._x_forwarded_for_ip
                and countries):
            country_code = random.choice(countries)
            self._x_forwarded_for_ip = GeoUtils.random_ipv4(country_code)
            if self._x_forwarded_for_ip:
                self.report_warning(
                    'Video is geo restricted. Retrying extraction with fake IP %s (%s) as X-Forwarded-For.'
                    % (self._x_forwarded_for_ip, country_code.upper()))
                return True
        return False

    def extract_subtitles(self, *args, **kwargs):
        if self._downloader.params.get('allsubtitles', False) or \
                self._downloader.params.get('writesubtitles', False) or \
                self._downloader.params.get('listsubtitles'):
            return self._get_subtitles(*args, **kwargs)
        return {}

    def _extract_signature_function(self, video_id, player_url, example_sig):
        player_id = self._extract_player_info(player_url)

        # Read from filesystem cache
        func_id = 'js_%s_%s' % (
            player_id, self._signature_cache_id(example_sig))
        assert os.path.basename(func_id) == func_id

        cache_spec = self._downloader.cache.load('youtube-sigfuncs', func_id)
        if cache_spec is not None:
            return lambda s: ''.join(s[i] for i in cache_spec)

        if player_id not in self._code_cache:
            try:
                self._code_cache[player_id] = self._download_webpage(
                    player_url, video_id,
                    note='Downloading player ' + player_id,
                    errnote='Download of %s failed' % player_url)
            except Exception as e:
                self._code_cache[player_id] = self._download_webpage(
                    player_url, video_id,
                    note='Downloading player ' + player_id,
                    errnote='Download of %s failed' % player_url)
        code = self._code_cache[player_id]
        res = self._parse_sig_js(code)

        test_string = ''.join(map(compat_chr, range(len(example_sig))))
        cache_res = res(test_string)
        cache_spec = [ord(c) for c in cache_res]

        self._downloader.cache.store('youtube-sigfuncs', func_id, cache_spec)
        return res

    def _decrypt_signature(self, s, video_id, player_url, age_gate=False):
        """Turn the encrypted s field into a working signature"""

        if player_url is None:
            raise ExtractorError('Cannot decrypt signature without player_url')

        try:
            player_url = json.loads(player_url)
        except Exception as e:
            pass
        if player_url.startswith('//'):
            player_url = 'https:' + player_url
        elif not re.match(r'https?://', player_url):
            player_url = compat_urlparse.urljoin(
                'https://www.youtube.com', player_url)
        try:
            player_id = (player_url, self._signature_cache_id(s))
            if player_id not in self._player_cache:
                func = self._extract_signature_function(
                    video_id, player_url, s
                )
                self._player_cache[player_id] = func
            func = self._player_cache[player_id]
            if self._downloader.params.get('youtube_print_sig_code'):
                self._print_sig_code(func, s)
            return func(s)
        except Exception as e:
            tb = traceback.format_exc()
            raise ExtractorError(
                'Signature extraction failed: ' + tb, cause=e)

    def extract(self, url, youtube_cookie=''):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url, youtube_cookie)
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except ExtractorError:
            raise
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e,
                                 expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e)

    def _real_extract(self, url, youtube_cookie):
        headers = {'cookie': youtube_cookie}
        url, smuggled_data = unsmuggle_url(url, {})
        video_id = self._match_id(url)
        base_url = self.http_scheme() + '//www.youtube.com/'
        webpage_url = base_url + 'watch?v=' + video_id

        webpage = self._download_webpage(
            webpage_url + '&bpctr=9999999999&has_verified=1', video_id, fatal=False, headers=headers)

        player_response = None
        if webpage:
            player_response = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_PLAYER_RESPONSE_RE,
                video_id, 'initial player response')
        if not player_response:
            player_response = self._call_api(
                'player', {'videoId': video_id}, video_id)

        playability_status = player_response.get('playabilityStatus') or {}
        if playability_status.get('reason') == 'Sign in to confirm your age':
            video_info = self._download_webpage(
                base_url + 'get_video_info', video_id,
                'Refetching age-gated info webpage',
                'unable to download video info webpage', query={
                    'video_id': video_id,
                    'eurl': 'https://youtube.googleapis.com/v/' + video_id,
                    'html5': 1,
                    # See https://github.com/ytdl-org/youtube-dl/issues/29333#issuecomment-864049544
                    'c': 'TVHTML5',
                    'cver': '6.20180913',
                }, fatal=False, headers=headers)
            if video_info:
                pr = self._parse_json(
                    try_get(
                        compat_parse_qs(video_info),
                        lambda x: x['player_response'][0], compat_str) or '{}',
                    video_id, fatal=False)
                if pr and isinstance(pr, dict):
                    player_response = pr

        trailer_video_id = try_get(
            playability_status,
            lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
            compat_str)
        if trailer_video_id:
            return self.url_result(
                trailer_video_id, self.ie_key(), trailer_video_id)

        def get_text(x):
            if not x:
                return
            text = x.get('simpleText')
            if text and isinstance(text, compat_str):
                return text
            runs = x.get('runs')
            if not isinstance(runs, list):
                return
            return ''.join([r['text'] for r in runs if isinstance(r.get('text'), compat_str)])

        search_meta = (
            lambda x: self._html_search_meta(x, webpage, default=None)) \
            if webpage else lambda x: None

        video_details = player_response.get('videoDetails') or {}
        microformat = try_get(
            player_response,
            lambda x: x['microformat']['playerMicroformatRenderer'],
            dict) or {}
        video_title = video_details.get('title') \
            or get_text(microformat.get('title')) \
            or search_meta(['og:title', 'twitter:title', 'title'])
        video_description = video_details.get('shortDescription')

        if not smuggled_data.get('force_singlefeed', False):
            if not self._downloader.params.get('noplaylist'):
                multifeed_metadata_list = try_get(
                    player_response,
                    lambda x: x['multicamera']['playerLegacyMulticameraRenderer']['metadataList'],
                    compat_str)
                if multifeed_metadata_list:
                    entries = []
                    feed_ids = []
                    for feed in multifeed_metadata_list.split(','):
                        # Unquote should take place before split on comma (,) since textual
                        # fields may contain comma as well (see
                        # https://github.com/ytdl-org/youtube-dl/issues/8536)
                        feed_data = compat_parse_qs(
                            compat_urllib_parse_unquote_plus(feed))

                        def feed_entry(name):
                            return try_get(
                                feed_data, lambda x: x[name][0], compat_str)

                        feed_id = feed_entry('id')
                        if not feed_id:
                            continue
                        feed_title = feed_entry('title')
                        title = video_title
                        if feed_title:
                            title += ' (%s)' % feed_title
                        entries.append({
                            '_type': 'url_transparent',
                            'ie_key': 'Youtube',
                            'url': smuggle_url(
                                base_url + 'watch?v=' + feed_data['id'][0],
                                {'force_singlefeed': True}),
                            'title': title,
                        })
                        feed_ids.append(feed_id)
                    self.to_screen(
                        'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
                        % (', '.join(feed_ids), video_id))
                    return self.playlist_result(
                        entries, video_id, video_title, video_description)
            else:
                self.to_screen('Downloading just video %s because of --no-playlist' % video_id)

        formats = []
        itags = []
        itag_qualities = {}
        player_url = None
        q = qualities(['tiny', 'small', 'medium', 'large', 'hd720', 'hd1080', 'hd1440', 'hd2160', 'hd2880', 'highres'])
        streaming_data = player_response.get('streamingData') or {}
        streaming_formats = streaming_data.get('formats') or []
        streaming_formats.extend(streaming_data.get('adaptiveFormats') or [])
        for fmt in streaming_formats:
            if fmt.get('targetDurationSec') or fmt.get('drmFamilies'):
                continue

            itag = str_or_none(fmt.get('itag'))
            quality = fmt.get('quality')
            if itag and quality:
                itag_qualities[itag] = quality
            # FORMAT_STREAM_TYPE_OTF(otf=1) requires downloading the init fragment
            # (adding `&sq=0` to the URL) and parsing emsg box to determine the
            # number of fragment that would subsequently requested with (`&sq=N`)
            if fmt.get('type') == 'FORMAT_STREAM_TYPE_OTF':
                continue

            fmt_url = fmt.get('url')
            if not fmt_url:
                sc = compat_parse_qs(fmt.get('signatureCipher'))
                fmt_url = url_or_none(try_get(sc, lambda x: x['url'][0]))
                encrypted_sig = try_get(sc, lambda x: x['s'][0])
                if not (sc and fmt_url and encrypted_sig):
                    continue
                if not player_url:
                    if not webpage:
                        continue
                    player_url = self._search_regex(
                        r'"(?:PLAYER_JS_URL|jsUrl)"\s*:\s*"([^"]+)"',
                        webpage, 'player URL', fatal=False)
                if not player_url:
                    continue
                signature = self._decrypt_signature(sc['s'][0], video_id, player_url)
                sp = try_get(sc, lambda x: x['sp'][0]) or 'signature'
                fmt_url += '&' + sp + '=' + signature

            if itag:
                itags.append(itag)
            tbr = float_or_none(
                fmt.get('averageBitrate') or fmt.get('bitrate'), 1000)
            dct = {
                'asr': int_or_none(fmt.get('audioSampleRate')),
                'filesize': int_or_none(fmt.get('contentLength')),
                'format_id': itag,
                'format_note': fmt.get('qualityLabel') or quality,
                'fps': int_or_none(fmt.get('fps')),
                'height': int_or_none(fmt.get('height')),
                'quality': q(quality),
                'tbr': tbr,
                'url': fmt_url,
                'width': fmt.get('width'),
            }
            mimetype = fmt.get('mimeType')
            if mimetype:
                mobj = re.match(
                    r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', mimetype)
                if mobj:
                    dct['ext'] = mimetype2ext(mobj.group(1))
                    dct.update(parse_codecs(mobj.group(2)))
            no_audio = dct.get('acodec') == 'none'
            no_video = dct.get('vcodec') == 'none'
            if no_audio:
                dct['vbr'] = tbr
            if no_video:
                dct['abr'] = tbr
            if no_audio or no_video:
                dct['downloader_options'] = {
                    # Youtube throttles chunks >~10M
                    'http_chunk_size': 10485760,
                }
                if dct.get('ext'):
                    dct['container'] = dct['ext'] + '_dash'
            formats.append(dct)

        hls_manifest_url = streaming_data.get('hlsManifestUrl')
        if hls_manifest_url:
            for f in self._extract_m3u8_formats(
                    hls_manifest_url, video_id, 'mp4', fatal=False):
                itag = self._search_regex(
                    r'/itag/(\d+)', f['url'], 'itag', default=None)
                if itag:
                    f['format_id'] = itag
                formats.append(f)

        if self._downloader.params.get('youtube_include_dash_manifest', True):
            dash_manifest_url = streaming_data.get('dashManifestUrl')
            if dash_manifest_url:
                for f in self._extract_mpd_formats(
                        dash_manifest_url, video_id, fatal=False):
                    itag = f['format_id']
                    if itag in itags:
                        continue
                    if itag in itag_qualities:
                        f['quality'] = q(itag_qualities[itag])
                    filesize = int_or_none(self._search_regex(
                        r'/clen/(\d+)', f.get('fragment_base_url')
                        or f['url'], 'file size', default=None))
                    if filesize:
                        f['filesize'] = filesize
                    formats.append(f)

        if not formats:
            if streaming_data.get('licenseInfos'):
                raise ExtractorError(
                    'This video is DRM protected.', expected=True)
            pemr = try_get(
                playability_status,
                lambda x: x['errorScreen']['playerErrorMessageRenderer'],
                dict) or {}
            reason = get_text(pemr.get('reason')) or playability_status.get('reason')
            subreason = pemr.get('subreason')
            if subreason:
                subreason = clean_html(get_text(subreason))
                if subreason == 'The uploader has not made this video available in your country.':
                    countries = microformat.get('availableCountries')
                    if not countries:
                        regions_allowed = search_meta('regionsAllowed')
                        countries = regions_allowed.split(',') if regions_allowed else None
                    self.raise_geo_restricted(
                        subreason, countries)
                reason += '\n' + subreason
            if reason:
                raise ExtractorError(reason, expected=True)

        self._sort_formats(formats)

        keywords = video_details.get('keywords') or []
        if not keywords and webpage:
            keywords = [
                unescapeHTML(m.group('content'))
                for m in re.finditer(self._meta_regex('og:video:tag'), webpage)]
        for keyword in keywords:
            if keyword.startswith('yt:stretch='):
                mobj = re.search(r'(\d+)\s*:\s*(\d+)', keyword)
                if mobj:
                    # NB: float is intentional for forcing float division
                    w, h = (float(v) for v in mobj.groups())
                    if w > 0 and h > 0:
                        ratio = w / h
                        for f in formats:
                            if f.get('vcodec') != 'none':
                                f['stretched_ratio'] = ratio
                        break

        thumbnails = []
        for container in (video_details, microformat):
            for thumbnail in (try_get(
                    container,
                    lambda x: x['thumbnail']['thumbnails'], list) or []):
                thumbnail_url = thumbnail.get('url')
                if not thumbnail_url:
                    continue
                thumbnails.append({
                    'height': int_or_none(thumbnail.get('height')),
                    'url': thumbnail_url,
                    'width': int_or_none(thumbnail.get('width')),
                })
            if thumbnails:
                break
        else:
            thumbnail = search_meta(['og:image', 'twitter:image'])
            if thumbnail:
                thumbnails = [{'url': thumbnail}]

        category = microformat.get('category') or search_meta('genre')
        channel_id = video_details.get('channelId') \
            or microformat.get('externalChannelId') \
            or search_meta('channelId')
        duration = int_or_none(
            video_details.get('lengthSeconds')
            or microformat.get('lengthSeconds')) \
            or parse_duration(search_meta('duration'))
        is_live = video_details.get('isLive')
        owner_profile_url = microformat.get('ownerProfileUrl')

        info = {
            'id': video_id,
            'title': self._live_title(video_title) if is_live else video_title,
            'formats': formats,
            'thumbnails': thumbnails,
            'description': video_description,
            'upload_date': unified_strdate(
                microformat.get('uploadDate')
                or search_meta('uploadDate')),
            'uploader': video_details['author'],
            'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
            'uploader_url': owner_profile_url,
            'channel_id': channel_id,
            'channel_url': 'https://www.youtube.com/channel/' + channel_id if channel_id else None,
            'duration': duration,
            'view_count': int_or_none(
                video_details.get('viewCount')
                or microformat.get('viewCount')
                or search_meta('interactionCount')),
            'average_rating': float_or_none(video_details.get('averageRating')),
            'age_limit': 18 if (
                microformat.get('isFamilySafe') is False
                or search_meta('isFamilyFriendly') == 'false'
                or search_meta('og:restrictions:age') == '18+') else 0,
            'webpage_url': webpage_url,
            'categories': [category] if category else None,
            'tags': keywords,
            'is_live': is_live,
        }

        pctr = try_get(
            player_response,
            lambda x: x['captions']['playerCaptionsTracklistRenderer'], dict)
        if pctr:
            def process_language(container, base_url, lang_code, query):
                lang_subs = []
                for fmt in self._SUBTITLE_FORMATS:
                    query.update({
                        'fmt': fmt,
                    })
                    lang_subs.append({
                        'ext': fmt,
                        'url': update_url_query(base_url, query),
                    })
                container[lang_code] = lang_subs

            subtitles = {}
            for caption_track in (pctr.get('captionTracks') or []):
                base_url = caption_track.get('baseUrl')
                if not base_url:
                    continue
                if caption_track.get('kind') != 'asr':
                    lang_code = caption_track.get('languageCode')
                    if not lang_code:
                        continue
                    process_language(
                        subtitles, base_url, lang_code, {})
                    continue
                automatic_captions = {}
                for translation_language in (pctr.get('translationLanguages') or []):
                    translation_language_code = translation_language.get('languageCode')
                    if not translation_language_code:
                        continue
                    process_language(
                        automatic_captions, base_url, translation_language_code,
                        {'tlang': translation_language_code})
                info['automatic_captions'] = automatic_captions
            info['subtitles'] = subtitles

        parsed_url = compat_urllib_parse_urlparse(url)
        for component in [parsed_url.fragment, parsed_url.query]:
            query = compat_parse_qs(component)
            for k, v in query.items():
                for d_k, s_ks in [('start', ('start', 't')), ('end', ('end',))]:
                    d_k += '_time'
                    if d_k not in info and k in s_ks:
                        info[d_k] = parse_duration(query[k][0])

        if video_description:
            mobj = re.search(r'(?s)(?P<track>[^·\n]+)·(?P<artist>[^\n]+)\n+(?P<album>[^\n]+)(?:.+?℗\s*(?P<release_year>\d{4})(?!\d))?(?:.+?Released on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?(.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+))?.+\nAuto-generated by YouTube\.\s*$', video_description)
            if mobj:
                release_year = mobj.group('release_year')
                release_date = mobj.group('release_date')
                if release_date:
                    release_date = release_date.replace('-', '')
                    if not release_year:
                        release_year = release_date[:4]
                info.update({
                    'album': mobj.group('album'.strip()),
                    'artist': mobj.group('clean_artist') or ', '.join(a.strip() for a in mobj.group('artist').split('·')),
                    'track': mobj.group('track').strip(),
                    'release_date': release_date,
                    'release_year': int_or_none(release_year),
                })

        initial_data = None
        if webpage:
            initial_data = self._extract_yt_initial_variable(
                webpage, self._YT_INITIAL_DATA_RE, video_id,
                'yt initial data')
        if not initial_data:
            initial_data = self._call_api(
                'next', {'videoId': video_id}, video_id, fatal=False)

        if initial_data:
            chapters = self._extract_chapters_from_json(
                initial_data, video_id, duration)
            if not chapters:
                for engagment_pannel in (initial_data.get('engagementPanels') or []):
                    contents = try_get(
                        engagment_pannel, lambda x: x['engagementPanelSectionListRenderer']['content']['macroMarkersListRenderer']['contents'],
                        list)
                    if not contents:
                        continue

                    def chapter_time(mmlir):
                        return parse_duration(
                            get_text(mmlir.get('timeDescription')))

                    chapters = []
                    for next_num, content in enumerate(contents, start=1):
                        mmlir = content.get('macroMarkersListItemRenderer') or {}
                        start_time = chapter_time(mmlir)
                        end_time = chapter_time(try_get(
                            contents, lambda x: x[next_num]['macroMarkersListItemRenderer'])) \
                            if next_num < len(contents) else duration
                        if start_time is None or end_time is None:
                            continue
                        chapters.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'title': get_text(mmlir.get('title')),
                        })
                    if chapters:
                        break
            if chapters:
                info['chapters'] = chapters

            contents = try_get(
                initial_data,
                lambda x: x['contents']['twoColumnWatchNextResults']['results']['results']['contents'],
                list) or []
            for content in contents:
                vpir = content.get('videoPrimaryInfoRenderer')
                if vpir:
                    stl = vpir.get('superTitleLink')
                    if stl:
                        stl = get_text(stl)
                        if try_get(
                                vpir,
                                lambda x: x['superTitleIcon']['iconType']) == 'LOCATION_PIN':
                            info['location'] = stl
                        else:
                            mobj = re.search(r'(.+?)\s*S(\d+)\s*•\s*E(\d+)', stl)
                            if mobj:
                                info.update({
                                    'series': mobj.group(1),
                                    'season_number': int(mobj.group(2)),
                                    'episode_number': int(mobj.group(3)),
                                })
                    for tlb in (try_get(
                            vpir,
                            lambda x: x['videoActions']['menuRenderer']['topLevelButtons'],
                            list) or []):
                        tbr = tlb.get('toggleButtonRenderer') or {}
                        for getter, regex in [(
                                lambda x: x['defaultText']['accessibility']['accessibilityData'],
                                r'(?P<count>[\d,]+)\s*(?P<type>(?:dis)?like)'), ([
                                    lambda x: x['accessibility'],
                                    lambda x: x['accessibilityData']['accessibilityData'],
                                ], r'(?P<type>(?:dis)?like) this video along with (?P<count>[\d,]+) other people')]:
                            label = (try_get(tbr, getter, dict) or {}).get('label')
                            if label:
                                mobj = re.match(regex, label)
                                if mobj:
                                    info[mobj.group('type') + '_count'] = str_to_int(mobj.group('count'))
                                    break
                    sbr_tooltip = try_get(
                        vpir, lambda x: x['sentimentBar']['sentimentBarRenderer']['tooltip'])
                    if sbr_tooltip:
                        like_count, dislike_count = sbr_tooltip.split(' / ')
                        info.update({
                            'like_count': str_to_int(like_count),
                            'dislike_count': str_to_int(dislike_count),
                        })
                vsir = content.get('videoSecondaryInfoRenderer')
                if vsir:
                    info['channel'] = get_text(try_get(
                        vsir,
                        lambda x: x['owner']['videoOwnerRenderer']['title'],
                        dict))
                    rows = try_get(
                        vsir,
                        lambda x: x['metadataRowContainer']['metadataRowContainerRenderer']['rows'],
                        list) or []
                    multiple_songs = False
                    for row in rows:
                        if try_get(row, lambda x: x['metadataRowRenderer']['hasDividerLine']) is True:
                            multiple_songs = True
                            break
                    for row in rows:
                        mrr = row.get('metadataRowRenderer') or {}
                        mrr_title = mrr.get('title')
                        if not mrr_title:
                            continue
                        mrr_title = get_text(mrr['title'])
                        mrr_contents_text = get_text(mrr['contents'][0])
                        if mrr_title == 'License':
                            info['license'] = mrr_contents_text
                        elif not multiple_songs:
                            if mrr_title == 'Album':
                                info['album'] = mrr_contents_text
                            elif mrr_title == 'Artist':
                                info['artist'] = mrr_contents_text
                            elif mrr_title == 'Song':
                                info['track'] = mrr_contents_text

        for s_k, d_k in [('artist', 'creator'), ('track', 'alt_title')]:
            v = info.get(s_k)
            if v:
                info[d_k] = v

        self.mark_watched(video_id, player_response)

        return info

    # def _real_extract(self, url):
    #     url, smuggled_data = unsmuggle_url(url, {})
    #     video_id = self._match_id(url)
    #     base_url = self.http_scheme() + '//www.youtube.com/'
    #     webpage_url = base_url + 'watch?v=' + video_id
    #     webpage = self._download_webpage(webpage_url, video_id, fatal=False)
    #
    #     player_response = None
    #     if webpage:
    #         player_response = self._extract_yt_initial_variable(
    #             webpage, self._YT_INITIAL_PLAYER_RESPONSE_RE,
    #             video_id, 'initial player response')
    #     if not player_response:
    #         player_response = self._call_api(
    #             'player', {'videoId': video_id}, video_id)
    #
    #     playability_status = player_response.get('playabilityStatus') or {}
    #     if playability_status.get('reason') == 'Sign in to confirm your age':
    #         pr = self._parse_json(try_get(compat_parse_qs(
    #             self._download_webpage(
    #                 base_url + 'get_video_info', video_id,
    #                 'Refetching age-gated info webpage',
    #                 'unable to download video info webpage', query={
    #                     'video_id': video_id,
    #                     'eurl': 'https://www.youtube.com/embed/' + video_id,
    #                 }, fatal=False)),
    #             lambda x: x['player_response'][0],
    #             compat_str) or '{}', video_id)
    #         if pr:
    #             player_response = pr
    #
    #     trailer_video_id = try_get(
    #         playability_status,
    #         lambda x: x['errorScreen']['playerLegacyDesktopYpcTrailerRenderer']['trailerVideoId'],
    #         compat_str)
    #     if trailer_video_id:
    #         return self.url_result(
    #             trailer_video_id, self.ie_key(), trailer_video_id)
    #
    #     def get_text(x):
    #         if not x:
    #             return
    #         return x.get('simpleText') or ''.join([r['text'] for r in x['runs']])
    #
    #     search_meta = (
    #         lambda x: self._html_search_meta(x, webpage, default=None)) \
    #         if webpage else lambda x: None
    #
    #     video_details = player_response.get('videoDetails') or {}
    #     microformat = try_get(
    #         player_response,
    #         lambda x: x['microformat']['playerMicroformatRenderer'],
    #         dict) or {}
    #     video_title = video_details.get('title') \
    #         or get_text(microformat.get('title')) \
    #         or search_meta(['og:title', 'twitter:title', 'title'])
    #     video_description = video_details.get('shortDescription')
    #
    #     if not smuggled_data.get('force_singlefeed', False):
    #         if not self._downloader.params.get('noplaylist'):
    #             multifeed_metadata_list = try_get(
    #                 player_response,
    #                 lambda x: x['multicamera']['playerLegacyMulticameraRenderer']['metadataList'],
    #                 compat_str)
    #             if multifeed_metadata_list:
    #                 entries = []
    #                 feed_ids = []
    #                 for feed in multifeed_metadata_list.split(','):
    #                     # Unquote should take place before split on comma (,) since textual
    #                     # fields may contain comma as well (see
    #                     # https://github.com/ytdl-org/youtube-dl/issues/8536)
    #                     feed_data = compat_parse_qs(
    #                         compat_urllib_parse_unquote_plus(feed))
    #
    #                     def feed_entry(name):
    #                         return try_get(
    #                             feed_data, lambda x: x[name][0], compat_str)
    #
    #                     feed_id = feed_entry('id')
    #                     if not feed_id:
    #                         continue
    #                     feed_title = feed_entry('title')
    #                     title = video_title
    #                     if feed_title:
    #                         title += ' (%s)' % feed_title
    #                     entries.append({
    #                         '_type': 'url_transparent',
    #                         'ie_key': 'Youtube',
    #                         'url': smuggle_url(
    #                             base_url + 'watch?v=' + feed_data['id'][0],
    #                             {'force_singlefeed': True}),
    #                         'title': title,
    #                     })
    #                     feed_ids.append(feed_id)
    #                 self.to_screen(
    #                     'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
    #                     % (', '.join(feed_ids), video_id))
    #                 return self.playlist_result(
    #                     entries, video_id, video_title, video_description)
    #         else:
    #             self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
    #
    #     formats = []
    #     itags = []
    #     player_url = None
    #     q = qualities(['tiny', 'small', 'medium', 'large', 'hd720', 'hd1080', 'hd1440', 'hd2160', 'hd2880', 'highres'])
    #     streaming_data = player_response.get('streamingData') or {}
    #     streaming_formats = streaming_data.get('formats') or []
    #     streaming_formats.extend(streaming_data.get('adaptiveFormats') or [])
    #     for fmt in streaming_formats:
    #         if fmt.get('targetDurationSec') or fmt.get('drmFamilies'):
    #             continue
    #
    #         fmt_url = fmt.get('url')
    #         if not fmt_url:
    #             sc = compat_parse_qs(fmt.get('signatureCipher'))
    #             fmt_url = url_or_none(try_get(sc, lambda x: x['url'][0]))
    #             encrypted_sig = try_get(sc, lambda x: x['s'][0])
    #             if not (sc and fmt_url and encrypted_sig):
    #                 continue
    #             if not player_url:
    #                 if not webpage:
    #                     continue
    #                 player_url = self._search_regex(
    #                     r'"(?:PLAYER_JS_URL|jsUrl)"\s*:\s*"([^"]+)"',
    #                     webpage, 'player URL', fatal=False)
    #             if not player_url:
    #                 continue
    #             signature = self._decrypt_signature(sc['s'][0], video_id, player_url)
    #             sp = try_get(sc, lambda x: x['sp'][0]) or 'signature'
    #             fmt_url += '&' + sp + '=' + signature
    #
    #         itag = str_or_none(fmt.get('itag'))
    #         if itag:
    #             itags.append(itag)
    #         quality = fmt.get('quality')
    #         dct = {
    #             'asr': int_or_none(fmt.get('audioSampleRate')),
    #             'filesize': int_or_none(fmt.get('contentLength')),
    #             'format_id': itag,
    #             'format_note': fmt.get('qualityLabel') or quality,
    #             'fps': int_or_none(fmt.get('fps')),
    #             'height': int_or_none(fmt.get('height')),
    #             'quality': q(quality),
    #             'tbr': float_or_none(fmt.get(
    #                 'averageBitrate') or fmt.get('bitrate'), 1000),
    #             'url': fmt_url,
    #             'width': fmt.get('width'),
    #         }
    #         mimetype = fmt.get('mimeType')
    #         if mimetype:
    #             mobj = re.match(
    #                 r'((?:[^/]+)/(?:[^;]+))(?:;\s*codecs="([^"]+)")?', mimetype)
    #             if mobj:
    #                 dct['ext'] = mimetype2ext(mobj.group(1))
    #                 dct.update(parse_codecs(mobj.group(2)))
    #         if dct.get('acodec') == 'none' or dct.get('vcodec') == 'none':
    #             dct['downloader_options'] = {
    #                 # Youtube throttles chunks >~10M
    #                 'http_chunk_size': 10485760,
    #             }
    #         formats.append(dct)
    #
    #     hls_manifest_url = streaming_data.get('hlsManifestUrl')
    #     if hls_manifest_url:
    #         for f in self._extract_m3u8_formats(
    #                 hls_manifest_url, video_id, 'mp4', fatal=False):
    #             itag = self._search_regex(
    #                 r'/itag/(\d+)', f['url'], 'itag', default=None)
    #             if itag:
    #                 f['format_id'] = itag
    #             formats.append(f)
    #
    #     if self._downloader.params.get('youtube_include_dash_manifest'):
    #         dash_manifest_url = streaming_data.get('dashManifestUrl')
    #         if dash_manifest_url:
    #             for f in self._extract_mpd_formats(
    #                     dash_manifest_url, video_id, fatal=False):
    #                 if f['format_id'] in itags:
    #                     continue
    #                 filesize = int_or_none(self._search_regex(
    #                     r'/clen/(\d+)', f.get('fragment_base_url')
    #                     or f['url'], 'file size', default=None))
    #                 if filesize:
    #                     f['filesize'] = filesize
    #                 formats.append(f)
    #
    #     if not formats:
    #         if streaming_data.get('licenseInfos'):
    #             raise ExtractorError(
    #                 'This video is DRM protected.', expected=True)
    #         pemr = try_get(
    #             playability_status,
    #             lambda x: x['errorScreen']['playerErrorMessageRenderer'],
    #             dict) or {}
    #         reason = get_text(pemr.get('reason')) or playability_status.get('reason')
    #         subreason = pemr.get('subreason')
    #         if subreason:
    #             subreason = clean_html(get_text(subreason))
    #             if subreason == 'The uploader has not made this video available in your country.':
    #                 countries = microformat.get('availableCountries')
    #                 if not countries:
    #                     regions_allowed = search_meta('regionsAllowed')
    #                     countries = regions_allowed.split(',') if regions_allowed else None
    #                 self.raise_geo_restricted(
    #                     subreason, countries)
    #             reason += '\n' + subreason
    #         if reason:
    #             raise ExtractorError(reason, expected=True)
    #
    #     self._sort_formats(formats)
    #
    #     keywords = video_details.get('keywords') or []
    #     if not keywords and webpage:
    #         keywords = [
    #             unescapeHTML(m.group('content'))
    #             for m in re.finditer(self._meta_regex('og:video:tag'), webpage)]
    #     for keyword in keywords:
    #         if keyword.startswith('yt:stretch='):
    #             w, h = keyword.split('=')[1].split(':')
    #             w, h = int(w), int(h)
    #             if w > 0 and h > 0:
    #                 ratio = w / h
    #                 for f in formats:
    #                     if f.get('vcodec') != 'none':
    #                         f['stretched_ratio'] = ratio
    #
    #     thumbnails = []
    #     for container in (video_details, microformat):
    #         for thumbnail in (try_get(
    #                 container,
    #                 lambda x: x['thumbnail']['thumbnails'], list) or []):
    #             thumbnail_url = thumbnail.get('url')
    #             if not thumbnail_url:
    #                 continue
    #             thumbnails.append({
    #                 'height': int_or_none(thumbnail.get('height')),
    #                 'url': thumbnail_url,
    #                 'width': int_or_none(thumbnail.get('width')),
    #             })
    #         if thumbnails:
    #             break
    #     else:
    #         thumbnail = search_meta(['og:image', 'twitter:image'])
    #         if thumbnail:
    #             thumbnails = [{'url': thumbnail}]
    #
    #     category = microformat.get('category') or search_meta('genre')
    #     channel_id = video_details.get('channelId') \
    #         or microformat.get('externalChannelId') \
    #         or search_meta('channelId')
    #     duration = int_or_none(
    #         video_details.get('lengthSeconds')
    #         or microformat.get('lengthSeconds')) \
    #         or parse_duration(search_meta('duration'))
    #     is_live = video_details.get('isLive')
    #     owner_profile_url = microformat.get('ownerProfileUrl')
    #
    #     info = {
    #         'id': video_id,
    #         'title': self._live_title(video_title) if is_live else video_title,
    #         'formats': formats,
    #         'thumbnails': thumbnails,
    #         'description': video_description,
    #         'upload_date': unified_strdate(
    #             microformat.get('uploadDate')
    #             or search_meta('uploadDate')),
    #         'uploader': video_details['author'],
    #         'uploader_id': self._search_regex(r'/(?:channel|user)/([^/?&#]+)', owner_profile_url, 'uploader id') if owner_profile_url else None,
    #         'uploader_url': owner_profile_url,
    #         'channel_id': channel_id,
    #         'channel_url': 'https://www.youtube.com/channel/' + channel_id if channel_id else None,
    #         'duration': duration,
    #         'view_count': int_or_none(
    #             video_details.get('viewCount')
    #             or microformat.get('viewCount')
    #             or search_meta('interactionCount')),
    #         'average_rating': float_or_none(video_details.get('averageRating')),
    #         'age_limit': 18 if (
    #             microformat.get('isFamilySafe') is False
    #             or search_meta('isFamilyFriendly') == 'false'
    #             or search_meta('og:restrictions:age') == '18+') else 0,
    #         'webpage_url': webpage_url,
    #         'categories': [category] if category else None,
    #         'tags': keywords,
    #         'is_live': is_live,
    #     }
    #
    #     pctr = try_get(
    #         player_response,
    #         lambda x: x['captions']['playerCaptionsTracklistRenderer'], dict)
    #     if pctr:
    #         def process_language(container, base_url, lang_code, query):
    #             lang_subs = []
    #             for fmt in self._SUBTITLE_FORMATS:
    #                 query.update({
    #                     'fmt': fmt,
    #                 })
    #                 lang_subs.append({
    #                     'ext': fmt,
    #                     'url': update_url_query(base_url, query),
    #                 })
    #             container[lang_code] = lang_subs
    #
    #         subtitles = {}
    #         for caption_track in (pctr.get('captionTracks') or []):
    #             base_url = caption_track.get('baseUrl')
    #             if not base_url:
    #                 continue
    #             if caption_track.get('kind') != 'asr':
    #                 lang_code = caption_track.get('languageCode')
    #                 if not lang_code:
    #                     continue
    #                 process_language(
    #                     subtitles, base_url, lang_code, {})
    #                 continue
    #             automatic_captions = {}
    #             for translation_language in (pctr.get('translationLanguages') or []):
    #                 translation_language_code = translation_language.get('languageCode')
    #                 if not translation_language_code:
    #                     continue
    #                 process_language(
    #                     automatic_captions, base_url, translation_language_code,
    #                     {'tlang': translation_language_code})
    #             info['automatic_captions'] = automatic_captions
    #         info['subtitles'] = subtitles
    #
    #     parsed_url = compat_urllib_parse_urlparse(url)
    #     for component in [parsed_url.fragment, parsed_url.query]:
    #         query = compat_parse_qs(component)
    #         for k, v in query.items():
    #             for d_k, s_ks in [('start', ('start', 't')), ('end', ('end',))]:
    #                 d_k += '_time'
    #                 if d_k not in info and k in s_ks:
    #                     info[d_k] = parse_duration(query[k][0])
    #
    #     if video_description:
    #         mobj = re.search(r'(?s)(?P<track>[^·\n]+)·(?P<artist>[^\n]+)\n+(?P<album>[^\n]+)(?:.+?℗\s*(?P<release_year>\d{4})(?!\d))?(?:.+?Released on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?(.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+))?.+\nAuto-generated by YouTube\.\s*$', video_description)
    #         if mobj:
    #             release_year = mobj.group('release_year')
    #             release_date = mobj.group('release_date')
    #             if release_date:
    #                 release_date = release_date.replace('-', '')
    #                 if not release_year:
    #                     release_year = release_date[:4]
    #             info.update({
    #                 'album': mobj.group('album'.strip()),
    #                 'artist': mobj.group('clean_artist') or ', '.join(a.strip() for a in mobj.group('artist').split('·')),
    #                 'track': mobj.group('track').strip(),
    #                 'release_date': release_date,
    #                 'release_year': int(release_year),
    #             })
    #
    #     initial_data = None
    #     if webpage:
    #         initial_data = self._extract_yt_initial_variable(
    #             webpage, self._YT_INITIAL_DATA_RE, video_id,
    #             'yt initial data')
    #     if not initial_data:
    #         initial_data = self._call_api(
    #             'next', {'videoId': video_id}, video_id, fatal=False)
    #
    #     if initial_data:
    #         chapters = self._extract_chapters_from_json(
    #             initial_data, video_id, duration)
    #         if not chapters:
    #             for engagment_pannel in (initial_data.get('engagementPanels') or []):
    #                 contents = try_get(
    #                     engagment_pannel, lambda x: x['engagementPanelSectionListRenderer']['content']['macroMarkersListRenderer']['contents'],
    #                     list)
    #                 if not contents:
    #                     continue
    #
    #                 def chapter_time(mmlir):
    #                     return parse_duration(
    #                         get_text(mmlir.get('timeDescription')))
    #
    #                 chapters = []
    #                 for next_num, content in enumerate(contents, start=1):
    #                     mmlir = content.get('macroMarkersListItemRenderer') or {}
    #                     start_time = chapter_time(mmlir)
    #                     end_time = chapter_time(try_get(
    #                         contents, lambda x: x[next_num]['macroMarkersListItemRenderer'])) \
    #                         if next_num < len(contents) else duration
    #                     if start_time is None or end_time is None:
    #                         continue
    #                     chapters.append({
    #                         'start_time': start_time,
    #                         'end_time': end_time,
    #                         'title': get_text(mmlir.get('title')),
    #                     })
    #                 if chapters:
    #                     break
    #         if chapters:
    #             info['chapters'] = chapters
    #
    #         contents = try_get(
    #             initial_data,
    #             lambda x: x['contents']['twoColumnWatchNextResults']['results']['results']['contents'],
    #             list) or []
    #         for content in contents:
    #             vpir = content.get('videoPrimaryInfoRenderer')
    #             if vpir:
    #                 stl = vpir.get('superTitleLink')
    #                 if stl:
    #                     stl = get_text(stl)
    #                     if try_get(
    #                             vpir,
    #                             lambda x: x['superTitleIcon']['iconType']) == 'LOCATION_PIN':
    #                         info['location'] = stl
    #                     else:
    #                         mobj = re.search(r'(.+?)\s*S(\d+)\s*•\s*E(\d+)', stl)
    #                         if mobj:
    #                             info.update({
    #                                 'series': mobj.group(1),
    #                                 'season_number': int(mobj.group(2)),
    #                                 'episode_number': int(mobj.group(3)),
    #                             })
    #                 for tlb in (try_get(
    #                         vpir,
    #                         lambda x: x['videoActions']['menuRenderer']['topLevelButtons'],
    #                         list) or []):
    #                     tbr = tlb.get('toggleButtonRenderer') or {}
    #                     for getter, regex in [(
    #                             lambda x: x['defaultText']['accessibility']['accessibilityData'],
    #                             r'(?P<count>[\d,]+)\s*(?P<type>(?:dis)?like)'), ([
    #                                 lambda x: x['accessibility'],
    #                                 lambda x: x['accessibilityData']['accessibilityData'],
    #                             ], r'(?P<type>(?:dis)?like) this video along with (?P<count>[\d,]+) other people')]:
    #                         label = (try_get(tbr, getter, dict) or {}).get('label')
    #                         if label:
    #                             mobj = re.match(regex, label)
    #                             if mobj:
    #                                 info[mobj.group('type') + '_count'] = str_to_int(mobj.group('count'))
    #                                 break
    #                 sbr_tooltip = try_get(
    #                     vpir, lambda x: x['sentimentBar']['sentimentBarRenderer']['tooltip'])
    #                 if sbr_tooltip:
    #                     like_count, dislike_count = sbr_tooltip.split(' / ')
    #                     info.update({
    #                         'like_count': str_to_int(like_count),
    #                         'dislike_count': str_to_int(dislike_count),
    #                     })
    #             vsir = content.get('videoSecondaryInfoRenderer')
    #             if vsir:
    #                 info['channel'] = get_text(try_get(
    #                     vsir,
    #                     lambda x: x['owner']['videoOwnerRenderer']['title'],
    #                     compat_str))
    #                 rows = try_get(
    #                     vsir,
    #                     lambda x: x['metadataRowContainer']['metadataRowContainerRenderer']['rows'],
    #                     list) or []
    #                 multiple_songs = False
    #                 for row in rows:
    #                     if try_get(row, lambda x: x['metadataRowRenderer']['hasDividerLine']) is True:
    #                         multiple_songs = True
    #                         break
    #                 for row in rows:
    #                     mrr = row.get('metadataRowRenderer') or {}
    #                     mrr_title = mrr.get('title')
    #                     if not mrr_title:
    #                         continue
    #                     mrr_title = get_text(mrr['title'])
    #                     mrr_contents_text = get_text(mrr['contents'][0])
    #                     if mrr_title == 'License':
    #                         info['license'] = mrr_contents_text
    #                     elif not multiple_songs:
    #                         if mrr_title == 'Album':
    #                             info['album'] = mrr_contents_text
    #                         elif mrr_title == 'Artist':
    #                             info['artist'] = mrr_contents_text
    #                         elif mrr_title == 'Song':
    #                             info['track'] = mrr_contents_text
    #
    #     for s_k, d_k in [('artist', 'creator'), ('track', 'alt_title')]:
    #         v = info.get(s_k)
    #         if v:
    #             info[d_k] = v
    #
    #     self.mark_watched(video_id, player_response)
    #
    #     return info

    # def _get_ytplayer_config(self, video_id, webpage):
    #     patterns = (
    #         # User data may contain arbitrary character sequences that may affect
    #         # JSON extraction with regex, e.g. when '};' is contained the second
    #         # regex won't capture the whole JSON. Yet working around by trying more
    #         # concrete regex first keeping in mind proper quoted string handling
    #         # to be implemented in future that will replace this workaround (see
    #         # https://github.com/ytdl-org/youtube-dl/issues/7468,
    #         # https://github.com/ytdl-org/youtube-dl/pull/7599)
    #         r';ytplayer\.config\s*=\s*({.+?});ytplayer',
    #         r';ytplayer\.config\s*=\s*({.+?});',
    #         # r'ytInitialData\s?=\s?(.*?);',
    #         r'ytInitialPlayerResponse\s?=\s?(.*?);var meta',
    #         r'window\["ytInitialPlayerResponse"\]\s?=\s?(.*?);\n?.+',
    #         r'window\["ytInitialData"\]\s?=\s?(.*?);\n?',
    #     )
    #     config = self._search_regex(
    #         patterns, webpage, 'ytplayer.config', default=None)
    #     if config:
    #         return self._parse_json(
    #             uppercase_escape(config), video_id, fatal=False)

    # def _real_extract(self, url):
    #     url, smuggled_data = unsmuggle_url(url, {})
    #
    #     proto = (
    #         'http' if self._downloader.params.get('prefer_insecure', False)
    #         else 'https')
    #
    #     start_time = None
    #     end_time = None
    #     parsed_url = compat_urllib_parse_urlparse(url)
    #     for component in [parsed_url.fragment, parsed_url.query]:
    #         query = compat_parse_qs(component)
    #         if start_time is None and 't' in query:
    #             start_time = parse_duration(query['t'][0])
    #         if start_time is None and 'start' in query:
    #             start_time = parse_duration(query['start'][0])
    #         if end_time is None and 'end' in query:
    #             end_time = parse_duration(query['end'][0])
    #
    #     # Extract original video URL from URL with redirection, like age verification, using next_url parameter
    #     mobj = re.search(self._NEXT_URL_RE, url)
    #     if mobj:
    #         url = proto + '://www.youtube.com/' + compat_urllib_parse_unquote(mobj.group(1)).lstrip('/')
    #     video_id = self.extract_id(url)
    #
    #     # Get video webpage
    #     url = proto + '://www.youtube.com/watch?v=%s&gl=US&hl=en&has_verified=1&bpctr=9999999999' % video_id
    #     video_webpage, urlh = self._download_webpage_handle(url, video_id)
    #
    #     qs = compat_parse_qs(compat_urllib_parse_urlparse(urlh.geturl()).query)
    #     video_id = qs.get('v', [None])[0] or video_id
    #
    #     # Attempt to extract SWF player URL
    #     mobj = re.search(r'swfConfig.*?"(https?:\\/\\/.*?watch.*?-.*?\.swf)"', video_webpage)
    #     if mobj is not None:
    #         player_url = re.sub(r'\\(.)', r'\1', mobj.group(1))
    #     else:
    #         player_url = None
    #
    #     dash_mpds = []
    #
    #     def add_dash_mpd(video_info):
    #         dash_mpd = video_info.get('dashmpd')
    #         if dash_mpd and dash_mpd[0] not in dash_mpds:
    #             dash_mpds.append(dash_mpd[0])
    #
    #     def add_dash_mpd_pr(pl_response):
    #         dash_mpd = url_or_none(try_get(
    #             pl_response, lambda x: x['streamingData']['dashManifestUrl'],
    #             compat_str))
    #         if dash_mpd and dash_mpd not in dash_mpds:
    #             dash_mpds.append(dash_mpd)
    #
    #     is_live = None
    #     view_count = None
    #
    #     def extract_view_count(v_info):
    #         return int_or_none(try_get(v_info, lambda x: x['view_count'][0]))
    #
    #     def extract_player_response(player_response, video_id):
    #         pl_response = str_or_none(player_response)
    #         if not pl_response:
    #             return
    #         pl_response = self._parse_json(pl_response, video_id, fatal=False)
    #         if isinstance(pl_response, dict):
    #             add_dash_mpd_pr(pl_response)
    #             return pl_response
    #
    #     player_response = {}
    #
    #     # Get video info
    #     video_info = {}
    #     embed_webpage = None
    #     ytplayer_config = None
    #
    #     if re.search(r'["\']status["\']\s*:\s*["\']LOGIN_REQUIRED', video_webpage) is not None:
    #         age_gate = True
    #         # We simulate the access to the video from www.youtube.com/v/{video_id}
    #         # this can be viewed without login into Youtube
    #         url = proto + '://www.youtube.com/embed/%s' % video_id
    #         embed_webpage = self._download_webpage(url, video_id, 'Downloading embed webpage')
    #         data = compat_urllib_parse_urlencode({
    #             'video_id': video_id,
    #             'eurl': 'https://youtube.googleapis.com/v/' + video_id,
    #             'sts': self._search_regex(
    #                 r'"sts"\s*:\s*(\d+)', embed_webpage, 'sts', default=''),
    #         })
    #         video_info_url = proto + '://www.youtube.com/get_video_info?' + data
    #         try:
    #             video_info_webpage = self._download_webpage(
    #                 video_info_url, video_id,
    #                 note='Refetching age-gated info webpage',
    #                 errnote='unable to download video info webpage')
    #         except ExtractorError:
    #             video_info_webpage = None
    #         if video_info_webpage:
    #             video_info = compat_parse_qs(video_info_webpage)
    #             pl_response = video_info.get('player_response', [None])[0]
    #             player_response = extract_player_response(pl_response, video_id)
    #             add_dash_mpd(video_info)
    #             view_count = extract_view_count(video_info)
    #     else:
    #         age_gate = False
    #         # Try looking directly into the video webpage
    #         ytplayer_config = self._get_ytplayer_config(video_id, video_webpage)
    #         if ytplayer_config:
    #             args = ytplayer_config['args']
    #             if args.get('url_encoded_fmt_stream_map') or args.get('hlsvp'):
    #                 # Convert to the same format returned by compat_parse_qs
    #                 video_info = dict((k, [v]) for k, v in args.items())
    #                 add_dash_mpd(video_info)
    #             # Rental video is not rented but preview is available (e.g.
    #             # https://www.youtube.com/watch?v=yYr8q0y5Jfg,
    #             # https://github.com/ytdl-org/youtube-dl/issues/10532)
    #             if not video_info and args.get('ypc_vid'):
    #                 return self.url_result(
    #                     args['ypc_vid'], CustomYoutubeIE.ie_key(), video_id=args['ypc_vid'])
    #             if args.get('livestream') == '1' or args.get('live_playback') == 1:
    #                 is_live = True
    #             if not player_response:
    #                 player_response = extract_player_response(args.get('player_response'), video_id)
    #         if not video_info or self._downloader.params.get('youtube_include_dash_manifest', True):
    #             add_dash_mpd_pr(player_response)
    #
    #     if not video_info and not player_response:
    #         player_response = extract_player_response(
    #             self._search_regex(
    #                 (r'%s\s*%s' % (self._YT_INITIAL_PLAYER_RESPONSE_RE, self._YT_INITIAL_BOUNDARY_RE),
    #                  self._YT_INITIAL_PLAYER_RESPONSE_RE), video_webpage,
    #                 'initial player response', default='{}'),
    #             video_id)
    #
    #     def extract_unavailable_message():
    #         messages = []
    #         for tag, kind in (('h1', 'message'), ('div', 'submessage')):
    #             msg = self._html_search_regex(
    #                 r'(?s)<{tag}[^>]+id=["\']unavailable-{kind}["\'][^>]*>(.+?)</{tag}>'.format(tag=tag, kind=kind),
    #                 video_webpage, 'unavailable %s' % kind, default=None)
    #             if msg:
    #                 messages.append(msg)
    #         if messages:
    #             return '\n'.join(messages)
    #
    #     if not video_info and not player_response:
    #         unavailable_message = extract_unavailable_message()
    #         if not unavailable_message:
    #             unavailable_message = 'Unable to extract video data'
    #         raise ExtractorError(
    #             'YouTube said: %s' % unavailable_message, expected=True, video_id=video_id)
    #
    #     if not isinstance(video_info, dict):
    #         video_info = {}
    #
    #     video_details = try_get(
    #         player_response, lambda x: x['videoDetails'], dict) or {}
    #
    #     microformat = try_get(
    #         player_response, lambda x: x['microformat']['playerMicroformatRenderer'], dict) or {}
    #
    #     video_title = video_info.get('title', [None])[0] or video_details.get('title')
    #     if not video_title:
    #         self._downloader.report_warning('Unable to extract video title')
    #         video_title = '_'
    #
    #     description_original = video_description = get_element_by_id("eow-description", video_webpage)
    #     if video_description:
    #
    #         def replace_url(m):
    #             redir_url = compat_urlparse.urljoin(url, m.group(1))
    #             parsed_redir_url = compat_urllib_parse_urlparse(redir_url)
    #             if re.search(r'^(?:www\.)?(?:youtube(?:-nocookie)?\.com|youtu\.be)$', parsed_redir_url.netloc) and parsed_redir_url.path == '/redirect':
    #                 qs = compat_parse_qs(parsed_redir_url.query)
    #                 q = qs.get('q')
    #                 if q and q[0]:
    #                     return q[0]
    #             return redir_url
    #
    #         description_original = video_description = re.sub(r'''(?x)
    #             <a\s+
    #                 (?:[a-zA-Z-]+="[^"]*"\s+)*?
    #                 (?:title|href)="([^"]+)"\s+
    #                 (?:[a-zA-Z-]+="[^"]*"\s+)*?
    #                 class="[^"]*"[^>]*>
    #             [^<]+\.{3}\s*
    #             </a>
    #         ''', replace_url, video_description)
    #         video_description = clean_html(video_description)
    #     else:
    #         video_description = video_details.get('shortDescription')
    #         if video_description is None:
    #             video_description = self._html_search_meta('description', video_webpage)
    #
    #     if not smuggled_data.get('force_singlefeed', False):
    #         if not self._downloader.params.get('noplaylist'):
    #             multifeed_metadata_list = try_get(
    #                 player_response,
    #                 lambda x: x['multicamera']['playerLegacyMulticameraRenderer']['metadataList'],
    #                 compat_str) or try_get(
    #                 video_info, lambda x: x['multifeed_metadata_list'][0], compat_str)
    #             if multifeed_metadata_list:
    #                 entries = []
    #                 feed_ids = []
    #                 for feed in multifeed_metadata_list.split(','):
    #                     # Unquote should take place before split on comma (,) since textual
    #                     # fields may contain comma as well (see
    #                     # https://github.com/ytdl-org/youtube-dl/issues/8536)
    #                     feed_data = compat_parse_qs(compat_urllib_parse_unquote_plus(feed))
    #
    #                     def feed_entry(name):
    #                         return try_get(feed_data, lambda x: x[name][0], compat_str)
    #
    #                     feed_id = feed_entry('id')
    #                     if not feed_id:
    #                         continue
    #                     feed_title = feed_entry('title')
    #                     title = video_title
    #                     if feed_title:
    #                         title += ' (%s)' % feed_title
    #                     entries.append({
    #                         '_type': 'url_transparent',
    #                         'ie_key': 'Youtube',
    #                         'url': smuggle_url(
    #                             '%s://www.youtube.com/watch?v=%s' % (proto, feed_data['id'][0]),
    #                             {'force_singlefeed': True}),
    #                         'title': title,
    #                     })
    #                     feed_ids.append(feed_id)
    #                 self.to_screen(
    #                     'Downloading multifeed video (%s) - add --no-playlist to just download video %s'
    #                     % (', '.join(feed_ids), video_id))
    #                 return self.playlist_result(entries, video_id, video_title, video_description)
    #         else:
    #             self.to_screen('Downloading just video %s because of --no-playlist' % video_id)
    #
    #     if view_count is None:
    #         view_count = extract_view_count(video_info)
    #     if view_count is None and video_details:
    #         view_count = int_or_none(video_details.get('viewCount'))
    #     if view_count is None and microformat:
    #         view_count = int_or_none(microformat.get('viewCount'))
    #
    #     if is_live is None:
    #         is_live = bool_or_none(video_details.get('isLive'))
    #
    #     # Check for "rental" videos
    #     if 'ypc_video_rental_bar_text' in video_info and 'author' not in video_info:
    #         raise ExtractorError('"rental" videos not supported. See https://github.com/ytdl-org/youtube-dl/issues/359 for more information.', expected=True)
    #
    #     def _extract_filesize(media_url):
    #         return int_or_none(self._search_regex(
    #             r'\bclen[=/](\d+)', media_url, 'filesize', default=None))
    #
    #     streaming_formats = try_get(player_response, lambda x: x['streamingData']['formats'], list) or []
    #     streaming_formats.extend(try_get(player_response, lambda x: x['streamingData']['adaptiveFormats'], list) or [])
    #
    #     formats_spec = {}
    #     if 'conn' in video_info and video_info['conn'][0].startswith('rtmp'):
    #         self.report_rtmp_download()
    #         formats = [{
    #             'format_id': '_rtmp',
    #             'protocol': 'rtmp',
    #             'url': video_info['conn'][0],
    #             'player_url': player_url,
    #         }]
    #     elif not is_live and (streaming_formats or len(video_info.get('url_encoded_fmt_stream_map', [''])[0]) >= 1 or len(video_info.get('adaptive_fmts', [''])[0]) >= 1):
    #         encoded_url_map = video_info.get('url_encoded_fmt_stream_map', [''])[0] + ',' + video_info.get('adaptive_fmts', [''])[0]
    #         if 'rtmpe%3Dyes' in encoded_url_map:
    #             raise ExtractorError('rtmpe downloads are not supported, see https://github.com/ytdl-org/youtube-dl/issues/343 for more information.', expected=True)
    #         formats = []
    #         # formats_spec = {}
    #         fmt_list = video_info.get('fmt_list', [''])[0]
    #         if fmt_list:
    #             for fmt in fmt_list.split(','):
    #                 spec = fmt.split('/')
    #                 if len(spec) > 1:
    #                     width_height = spec[1].split('x')
    #                     if len(width_height) == 2:
    #                         formats_spec[spec[0]] = {
    #                             'resolution': spec[1],
    #                             'width': int_or_none(width_height[0]),
    #                             'height': int_or_none(width_height[1]),
    #                         }
    #         for fmt in streaming_formats:
    #             itag = str_or_none(fmt.get('itag'))
    #             if not itag:
    #                 continue
    #             quality = fmt.get('quality')
    #             quality_label = fmt.get('qualityLabel') or quality
    #             formats_spec[itag] = {
    #                 'asr': int_or_none(fmt.get('audioSampleRate')),
    #                 'filesize': int_or_none(fmt.get('contentLength')),
    #                 'format_note': quality_label,
    #                 'fps': int_or_none(fmt.get('fps')),
    #                 'height': int_or_none(fmt.get('height')),
    #                 # bitrate for itag 43 is always 2147483647
    #                 'tbr': float_or_none(fmt.get('averageBitrate') or fmt.get('bitrate'), 1000) if itag != '43' else None,
    #                 'width': int_or_none(fmt.get('width')),
    #             }
    #
    #         for fmt in streaming_formats:
    #             if fmt.get('drmFamilies') or fmt.get('drm_families'):
    #                 continue
    #             url = url_or_none(fmt.get('url'))
    #
    #             if not url:
    #                 cipher = fmt.get('cipher') or fmt.get('signatureCipher')
    #                 if not cipher:
    #                     continue
    #                 url_data = compat_parse_qs(cipher)
    #                 url = url_or_none(try_get(url_data, lambda x: x['url'][0], compat_str))
    #                 if not url:
    #                     continue
    #             else:
    #                 cipher = None
    #                 url_data = compat_parse_qs(compat_urllib_parse_urlparse(url).query)
    #
    #             stream_type = int_or_none(try_get(url_data, lambda x: x['stream_type'][0]))
    #             # Unsupported FORMAT_STREAM_TYPE_OTF
    #             if stream_type == 3:
    #                 continue
    #
    #             format_id = fmt.get('itag') or url_data['itag'][0]
    #             if not format_id:
    #                 continue
    #             format_id = compat_str(format_id)
    #
    #             if cipher:
    #                 if 's' in url_data or self._downloader.params.get('youtube_include_dash_manifest', True):
    #                     ASSETS_RE = (
    #                         r'<script[^>]+\bsrc=("[^"]+")[^>]+\bname=["\']player_ias/base',
    #                         r'"jsUrl"\s*:\s*("[^"]+")',
    #                         r'"assets":.+?"js":\s*("[^"]+")')
    #                     jsplayer_url_json = self._search_regex(
    #                         ASSETS_RE,
    #                         embed_webpage if age_gate else video_webpage,
    #                         'JS player URL (1)', default=None)
    #                     if not jsplayer_url_json:# and not age_gate:
    #                         # We need the embed website after all
    #                         if embed_webpage is None:
    #                             embed_url = proto + '://www.youtube.com/embed/%s' % video_id
    #                             embed_webpage = self._download_webpage(
    #                                 embed_url, video_id, 'Downloading embed webpage')
    #                         jsplayer_url_json = self._search_regex(
    #                             ASSETS_RE, embed_webpage, 'JS player URL')
    #
    #                     if r'\\' in jsplayer_url_json:
    #                         player_url = json.loads(jsplayer_url_json)
    #                     else:
    #                         player_url = jsplayer_url_json
    #                     if player_url is None:
    #                         player_url_json = self._search_regex(
    #                             r'ytplayer\.config.*?"url"\s*:\s*("[^"]+")',
    #                             video_webpage, 'age gate player URL')
    #                         player_url = json.loads(player_url_json)
    #
    #                 if 'sig' in url_data:
    #                     url += '&signature=' + url_data['sig'][0]
    #                 elif 's' in url_data:
    #                     encrypted_sig = url_data['s'][0]
    #
    #                     if self._downloader.params.get('verbose'):
    #                         if player_url is None:
    #                             player_desc = 'unknown'
    #                         else:
    #                             player_type, player_version = self._extract_player_info(player_url)
    #                             player_desc = '%s player %s' % ('flash' if player_type == 'swf' else 'html5', player_version)
    #                         parts_sizes = self._signature_cache_id(encrypted_sig)
    #                         self.to_screen('{%s} signature length %s, %s' %
    #                                        (format_id, parts_sizes, player_desc))
    #
    #                     signature = self._decrypt_signature(
    #                         encrypted_sig, video_id, player_url, age_gate)
    #                     sp = try_get(url_data, lambda x: x['sp'][0], compat_str) or 'signature'
    #                     url += '&%s=%s' % (sp, signature)
    #             if 'ratebypass' not in url:
    #                 url += '&ratebypass=yes'
    #
    #             dct = {
    #                 'format_id': format_id,
    #                 'url': url,
    #                 'player_url': player_url,
    #             }
    #             if format_id in self._formats:
    #                 dct.update(self._formats[format_id])
    #             if format_id in formats_spec:
    #                 dct.update(formats_spec[format_id])
    #
    #             # Some itags are not included in DASH manifest thus corresponding formats will
    #             # lack metadata (see https://github.com/ytdl-org/youtube-dl/pull/5993).
    #             # Trying to extract metadata from url_encoded_fmt_stream_map entry.
    #             mobj = re.search(r'^(?P<width>\d+)[xX](?P<height>\d+)$', url_data.get('size', [''])[0])
    #             width, height = (int(mobj.group('width')), int(mobj.group('height'))) if mobj else (None, None)
    #
    #             if width is None:
    #                 width = int_or_none(fmt.get('width'))
    #             if height is None:
    #                 height = int_or_none(fmt.get('height'))
    #
    #             filesize = int_or_none(url_data.get(
    #                 'clen', [None])[0]) or _extract_filesize(url)
    #
    #             quality = url_data.get('quality', [None])[0] or fmt.get('quality')
    #             quality_label = url_data.get('quality_label', [None])[0] or fmt.get('qualityLabel')
    #
    #             tbr = (float_or_none(url_data.get('bitrate', [None])[0], 1000)
    #                    or float_or_none(fmt.get('bitrate'), 1000)) if format_id != '43' else None
    #             fps = int_or_none(url_data.get('fps', [None])[0]) or int_or_none(fmt.get('fps'))
    #
    #             more_fields = {
    #                 'filesize': filesize,
    #                 'tbr': tbr,
    #                 'width': width,
    #                 'height': height,
    #                 'fps': fps,
    #                 'format_note': quality_label or quality,
    #             }
    #             for key, value in more_fields.items():
    #                 if value:
    #                     dct[key] = value
    #             type_ = url_data.get('type', [None])[0] or fmt.get('mimeType')
    #             if type_:
    #                 type_split = type_.split(';')
    #                 kind_ext = type_split[0].split('/')
    #                 if len(kind_ext) == 2:
    #                     kind, _ = kind_ext
    #                     dct['ext'] = mimetype2ext(type_split[0])
    #                     if kind in ('audio', 'video'):
    #                         codecs = None
    #                         for mobj in re.finditer(
    #                                 r'(?P<key>[a-zA-Z_-]+)=(?P<quote>["\']?)(?P<val>.+?)(?P=quote)(?:;|$)', type_):
    #                             if mobj.group('key') == 'codecs':
    #                                 codecs = mobj.group('val')
    #                                 break
    #                         if codecs:
    #                             dct.update(parse_codecs(codecs))
    #             if dct.get('acodec') == 'none' or dct.get('vcodec') == 'none':
    #                 dct['downloader_options'] = {
    #                     # Youtube throttles chunks >~10M
    #                     'http_chunk_size': 10485760,
    #                 }
    #             formats.append(dct)
    #     else:
    #         manifest_url = (
    #             url_or_none(try_get(
    #                 player_response,
    #                 lambda x: x['streamingData']['hlsManifestUrl'],
    #                 compat_str))
    #             or url_or_none(try_get(
    #                 video_info, lambda x: x['hlsvp'][0], compat_str)))
    #         if manifest_url:
    #             formats = []
    #             m3u8_formats = self._extract_m3u8_formats(
    #                 manifest_url, video_id, 'mp4', fatal=False)
    #             for a_format in m3u8_formats:
    #                 itag = self._search_regex(
    #                     r'/itag/(\d+)/', a_format['url'], 'itag', default=None)
    #                 if itag:
    #                     a_format['format_id'] = itag
    #                     if itag in self._formats:
    #                         dct = self._formats[itag].copy()
    #                         dct.update(a_format)
    #                         a_format = dct
    #                 a_format['player_url'] = player_url
    #                 # Accept-Encoding header causes failures in live streams on Youtube and Youtube Gaming
    #                 a_format.setdefault('http_headers', {})['Youtubedl-no-compression'] = 'True'
    #                 formats.append(a_format)
    #         else:
    #             error_message = extract_unavailable_message()
    #             if not error_message:
    #                 reason_list = try_get(
    #                     player_response,
    #                     lambda x: x['playabilityStatus']['errorScreen']['playerErrorMessageRenderer']['subreason']['runs'],
    #                     list) or []
    #                 for reason in reason_list:
    #                     if not isinstance(reason, dict):
    #                         continue
    #                     reason_text = try_get(reason, lambda x: x['text'], compat_str)
    #                     if reason_text:
    #                         if not error_message:
    #                             error_message = ''
    #                         error_message += reason_text
    #                 if error_message:
    #                     error_message = clean_html(error_message)
    #             if not error_message:
    #                 error_message = clean_html(try_get(
    #                     player_response, lambda x: x['playabilityStatus']['reason'],
    #                     compat_str))
    #             if not error_message:
    #                 error_message = clean_html(
    #                     try_get(video_info, lambda x: x['reason'][0], compat_str))
    #             if error_message:
    #                 raise ExtractorError(error_message, expected=True)
    #             raise ExtractorError('no conn, hlsvp, hlsManifestUrl or url_encoded_fmt_stream_map information found in video info')
    #
    #     # uploader
    #     video_uploader = try_get(
    #         video_info, lambda x: x['author'][0],
    #         compat_str) or str_or_none(video_details.get('author'))
    #     if video_uploader:
    #         video_uploader = compat_urllib_parse_unquote_plus(video_uploader)
    #     else:
    #         self._downloader.report_warning('unable to extract uploader name')
    #
    #     # uploader_id
    #     video_uploader_id = None
    #     video_uploader_url = None
    #     mobj = re.search(
    #         r'<link itemprop="url" href="(?P<uploader_url>https?://www\.youtube\.com/(?:user|channel)/(?P<uploader_id>[^"]+))">',
    #         video_webpage)
    #     if mobj is not None:
    #         video_uploader_id = mobj.group('uploader_id')
    #         video_uploader_url = mobj.group('uploader_url')
    #     else:
    #         owner_profile_url = url_or_none(microformat.get('ownerProfileUrl'))
    #         if owner_profile_url:
    #             video_uploader_id = self._search_regex(
    #                 r'(?:user|channel)/([^/]+)', owner_profile_url, 'uploader id',
    #                 default=None)
    #             video_uploader_url = owner_profile_url
    #
    #     channel_id = (
    #         str_or_none(video_details.get('channelId'))
    #         or self._html_search_meta(
    #             'channelId', video_webpage, 'channel id', default=None)
    #         or self._search_regex(
    #             r'data-channel-external-id=(["\'])(?P<id>(?:(?!\1).)+)\1',
    #             video_webpage, 'channel id', default=None, group='id'))
    #     channel_url = 'http://www.youtube.com/channel/%s' % channel_id if channel_id else None
    #
    #     thumbnails = []
    #     thumbnails_list = try_get(
    #         video_details, lambda x: x['thumbnail']['thumbnails'], list) or []
    #     for t in thumbnails_list:
    #         if not isinstance(t, dict):
    #             continue
    #         thumbnail_url = url_or_none(t.get('url'))
    #         if not thumbnail_url:
    #             continue
    #         thumbnails.append({
    #             'url': thumbnail_url,
    #             'width': int_or_none(t.get('width')),
    #             'height': int_or_none(t.get('height')),
    #         })
    #
    #     if not thumbnails:
    #         video_thumbnail = None
    #         # We try first to get a high quality image:
    #         m_thumb = re.search(r'<span itemprop="thumbnail".*?href="(.*?)">',
    #                             video_webpage, re.DOTALL)
    #         if m_thumb is not None:
    #             video_thumbnail = m_thumb.group(1)
    #         thumbnail_url = try_get(video_info, lambda x: x['thumbnail_url'][0], compat_str)
    #         if thumbnail_url:
    #             video_thumbnail = compat_urllib_parse_unquote_plus(thumbnail_url)
    #         if video_thumbnail:
    #             thumbnails.append({'url': video_thumbnail})
    #
    #     # upload date
    #     upload_date = self._html_search_meta(
    #         'datePublished', video_webpage, 'upload date', default=None)
    #     if not upload_date:
    #         upload_date = self._search_regex(
    #             [r'(?s)id="eow-date.*?>(.*?)</span>',
    #              r'(?:id="watch-uploader-info".*?>.*?|["\']simpleText["\']\s*:\s*["\'])(?:Published|Uploaded|Streamed live|Started) on (.+?)[<"\']'],
    #             video_webpage, 'upload date', default=None)
    #     if not upload_date:
    #         upload_date = microformat.get('publishDate') or microformat.get('uploadDate')
    #     upload_date = unified_strdate(upload_date)
    #
    #     video_license = self._html_search_regex(
    #         r'<h4[^>]+class="title"[^>]*>\s*License\s*</h4>\s*<ul[^>]*>\s*<li>(.+?)</li',
    #         video_webpage, 'license', default=None)
    #
    #     m_music = re.search(
    #         r'''(?x)
    #             <h4[^>]+class="title"[^>]*>\s*Music\s*</h4>\s*
    #             <ul[^>]*>\s*
    #             <li>(?P<title>.+?)
    #             by (?P<creator>.+?)
    #             (?:
    #                 \(.+?\)|
    #                 <a[^>]*
    #                     (?:
    #                         \bhref=["\']/red[^>]*>|             # drop possible
    #                         >\s*Listen ad-free with YouTube Red # YouTube Red ad
    #                     )
    #                 .*?
    #             )?</li
    #         ''',
    #         video_webpage)
    #     if m_music:
    #         video_alt_title = remove_quotes(unescapeHTML(m_music.group('title')))
    #         video_creator = clean_html(m_music.group('creator'))
    #     else:
    #         video_alt_title = video_creator = None
    #
    #     def extract_meta(field):
    #         return self._html_search_regex(
    #             r'<h4[^>]+class="title"[^>]*>\s*%s\s*</h4>\s*<ul[^>]*>\s*<li>(.+?)</li>\s*' % field,
    #             video_webpage, field, default=None)
    #
    #     track = extract_meta('Song')
    #     artist = extract_meta('Artist')
    #     album = extract_meta('Album')
    #
    #     # Youtube Music Auto-generated description
    #     release_date = release_year = None
    #     if video_description:
    #         mobj = re.search(r'(?s)(?P<track>[^·\n]+)·(?P<artist>[^\n]+)\n+(?P<album>[^\n]+)(?:.+?℗\s*(?P<release_year>\d{4})(?!\d))?(?:.+?Released on\s*:\s*(?P<release_date>\d{4}-\d{2}-\d{2}))?(.+?\nArtist\s*:\s*(?P<clean_artist>[^\n]+))?.+\nAuto-generated by YouTube\.\s*$', video_description)
    #         if mobj:
    #             if not track:
    #                 track = mobj.group('track').strip()
    #             if not artist:
    #                 artist = mobj.group('clean_artist') or ', '.join(a.strip() for a in mobj.group('artist').split('·'))
    #             if not album:
    #                 album = mobj.group('album'.strip())
    #             release_year = mobj.group('release_year')
    #             release_date = mobj.group('release_date')
    #             if release_date:
    #                 release_date = release_date.replace('-', '')
    #                 if not release_year:
    #                     release_year = int(release_date[:4])
    #             if release_year:
    #                 release_year = int(release_year)
    #
    #     yt_initial_data = self._extract_yt_initial_data(video_id, video_webpage)
    #     contents = try_get(yt_initial_data, lambda x: x['contents']['twoColumnWatchNextResults']['results']['results']['contents'], list) or []
    #     for content in contents:
    #         rows = try_get(content, lambda x: x['videoSecondaryInfoRenderer']['metadataRowContainer']['metadataRowContainerRenderer']['rows'], list) or []
    #         multiple_songs = False
    #         for row in rows:
    #             if try_get(row, lambda x: x['metadataRowRenderer']['hasDividerLine']) is True:
    #                 multiple_songs = True
    #                 break
    #         for row in rows:
    #             mrr = row.get('metadataRowRenderer') or {}
    #             mrr_title = try_get(
    #                 mrr, lambda x: x['title']['simpleText'], compat_str)
    #             mrr_contents = try_get(
    #                 mrr, lambda x: x['contents'][0], dict) or {}
    #             mrr_contents_text = try_get(mrr_contents, [lambda x: x['simpleText'], lambda x: x['runs'][0]['text']], compat_str)
    #             if not (mrr_title and mrr_contents_text):
    #                 continue
    #             if mrr_title == 'License':
    #                 video_license = mrr_contents_text
    #             elif not multiple_songs:
    #                 if mrr_title == 'Album':
    #                     album = mrr_contents_text
    #                 elif mrr_title == 'Artist':
    #                     artist = mrr_contents_text
    #                 elif mrr_title == 'Song':
    #                     track = mrr_contents_text
    #
    #     m_episode = re.search(
    #         r'<div[^>]+id="watch7-headline"[^>]*>\s*<span[^>]*>.*?>(?P<series>[^<]+)</a></b>\s*S(?P<season>\d+)\s*•\s*E(?P<episode>\d+)</span>',
    #         video_webpage)
    #     if m_episode:
    #         series = unescapeHTML(m_episode.group('series'))
    #         season_number = int(m_episode.group('season'))
    #         episode_number = int(m_episode.group('episode'))
    #     else:
    #         series = season_number = episode_number = None
    #
    #     m_cat_container = self._search_regex(
    #         r'(?s)<h4[^>]*>\s*Category\s*</h4>\s*<ul[^>]*>(.*?)</ul>',
    #         video_webpage, 'categories', default=None)
    #     category = None
    #     if m_cat_container:
    #         category = self._html_search_regex(
    #             r'(?s)<a[^<]+>(.*?)</a>', m_cat_container, 'category',
    #             default=None)
    #     if not category:
    #         category = try_get(
    #             microformat, lambda x: x['category'], compat_str)
    #     video_categories = None if category is None else [category]
    #
    #     video_tags = [
    #         unescapeHTML(m.group('content'))
    #         for m in re.finditer(self._meta_regex('og:video:tag'), video_webpage)]
    #     if not video_tags:
    #         video_tags = try_get(video_details, lambda x: x['keywords'], list)
    #
    #     def _extract_count(count_name):
    #         return str_to_int(self._search_regex(
    #             (r'-%s-button[^>]+><span[^>]+class="yt-uix-button-content"[^>]*>([\d,]+)</span>' % re.escape(count_name),
    #              r'["\']label["\']\s*:\s*["\']([\d,.]+)\s+%ss["\']' % re.escape(count_name)),
    #             video_webpage, count_name, default=None))
    #
    #     like_count = _extract_count('like')
    #     dislike_count = _extract_count('dislike')
    #
    #     if view_count is None:
    #         view_count = str_to_int(self._search_regex(
    #             r'<[^>]+class=["\']watch-view-count[^>]+>\s*([\d,\s]+)', video_webpage,
    #             'view count', default=None))
    #
    #     average_rating = (
    #         float_or_none(video_details.get('averageRating'))
    #         or try_get(video_info, lambda x: float_or_none(x['avg_rating'][0])))
    #
    #     # subtitles
    #     video_subtitles = self.extract_subtitles(video_id, video_webpage)
    #     automatic_captions = self.extract_automatic_captions(video_id, player_response, ytplayer_config)
    #
    #     video_duration = try_get(
    #         video_info, lambda x: int_or_none(x['length_seconds'][0]))
    #     if not video_duration:
    #         video_duration = int_or_none(video_details.get('lengthSeconds'))
    #     if not video_duration:
    #         video_duration = parse_duration(self._html_search_meta(
    #             'duration', video_webpage, 'video duration'))
    #
    #     # annotations
    #     video_annotations = None
    #     if self._downloader.params.get('writeannotations', False):
    #         xsrf_token = None
    #         ytcfg = self._extract_ytcfg(video_id, video_webpage)
    #         if ytcfg:
    #             xsrf_token = try_get(ytcfg, lambda x: x['XSRF_TOKEN'], compat_str)
    #         if not xsrf_token:
    #             xsrf_token = self._search_regex(
    #                 r'([\'"])XSRF_TOKEN\1\s*:\s*([\'"])(?P<xsrf_token>(?:(?!\2).)+)\2',
    #                 video_webpage, 'xsrf token', group='xsrf_token', fatal=False)
    #         invideo_url = try_get(
    #             player_response, lambda x: x['annotations'][0]['playerAnnotationsUrlsRenderer']['invideoUrl'], compat_str)
    #         if xsrf_token and invideo_url:
    #             xsrf_field_name = None
    #             if ytcfg:
    #                 xsrf_field_name = try_get(ytcfg, lambda x: x['XSRF_FIELD_NAME'], compat_str)
    #             if not xsrf_field_name:
    #                 xsrf_field_name = self._search_regex(
    #                     r'([\'"])XSRF_FIELD_NAME\1\s*:\s*([\'"])(?P<xsrf_field_name>\w+)\2',
    #                     video_webpage, 'xsrf field name',
    #                     group='xsrf_field_name', default='session_token')
    #             video_annotations = self._download_webpage(
    #                 self._proto_relative_url(invideo_url),
    #                 video_id, note='Downloading annotations',
    #                 errnote='Unable to download video annotations', fatal=False,
    #                 data=urlencode_postdata({xsrf_field_name: xsrf_token}))
    #
    #     chapters = self._extract_chapters(video_webpage, description_original, video_id, video_duration)
    #
    #     # Look for the DASH manifest
    #     if self._downloader.params.get('youtube_include_dash_manifest', True):
    #         dash_mpd_fatal = True
    #         for mpd_url in dash_mpds:
    #             dash_formats = {}
    #             try:
    #                 def decrypt_sig(mobj):
    #                     s = mobj.group(1)
    #                     dec_s = self._decrypt_signature(s, video_id, player_url, age_gate)
    #                     return '/signature/%s' % dec_s
    #
    #                 mpd_url = re.sub(r'/s/([a-fA-F0-9\.]+)', decrypt_sig, mpd_url)
    #
    #                 for df in self._extract_mpd_formats(
    #                         mpd_url, video_id, fatal=dash_mpd_fatal,
    #                         formats_dict=self._formats):
    #                     if not df.get('filesize'):
    #                         df['filesize'] = _extract_filesize(df['url'])
    #                     # Do not overwrite DASH format found in some previous DASH manifest
    #                     if df['format_id'] not in dash_formats:
    #                         dash_formats[df['format_id']] = df
    #                     # Additional DASH manifests may end up in HTTP Error 403 therefore
    #                     # allow them to fail without bug report message if we already have
    #                     # some DASH manifest succeeded. This is temporary workaround to reduce
    #                     # burst of bug reports until we figure out the reason and whether it
    #                     # can be fixed at all.
    #                     dash_mpd_fatal = False
    #             except (ExtractorError, KeyError) as e:
    #                 self.report_warning(
    #                     'Skipping DASH manifest: %r' % e, video_id)
    #             if dash_formats:
    #                 # Remove the formats we found through non-DASH, they
    #                 # contain less info and it can be wrong, because we use
    #                 # fixed values (for example the resolution). See
    #                 # https://github.com/ytdl-org/youtube-dl/issues/5774 for an
    #                 # example.
    #                 formats = [f for f in formats if f['format_id'] not in dash_formats.keys()]
    #                 formats.extend(dash_formats.values())
    #
    #     # Check for malformed aspect ratio
    #     stretched_m = re.search(
    #         r'<meta\s+property="og:video:tag".*?content="yt:stretch=(?P<w>[0-9]+):(?P<h>[0-9]+)">',
    #         video_webpage)
    #     if stretched_m:
    #         w = float(stretched_m.group('w'))
    #         h = float(stretched_m.group('h'))
    #         # yt:stretch may hold invalid ratio data (e.g. for Q39EVAstoRM ratio is 17:0).
    #         # We will only process correct ratios.
    #         if w > 0 and h > 0:
    #             ratio = w / h
    #             for f in formats:
    #                 if f.get('vcodec') != 'none':
    #                     f['stretched_ratio'] = ratio
    #
    #     if not formats:
    #         if 'reason' in video_info:
    #             if 'The uploader has not made this video available in your country.' in video_info['reason']:
    #                 regions_allowed = self._html_search_meta(
    #                     'regionsAllowed', video_webpage, default=None)
    #                 countries = regions_allowed.split(',') if regions_allowed else None
    #                 self.raise_geo_restricted(
    #                     msg=video_info['reason'][0], countries=countries)
    #             reason = video_info['reason'][0]
    #             if 'Invalid parameters' in reason:
    #                 unavailable_message = extract_unavailable_message()
    #                 if unavailable_message:
    #                     reason = unavailable_message
    #             raise ExtractorError(
    #                 'YouTube said: %s' % reason,
    #                 expected=True, video_id=video_id)
    #         if video_info.get('license_info') or try_get(player_response, lambda x: x['streamingData']['licenseInfos']):
    #             raise ExtractorError('This video is DRM protected.', expected=True)
    #
    #     '''we edit filesize and tbr value'''
    #     for fmt in formats:
    #         fmt_id = fmt['format_id']
    #         if formats_spec.get(fmt_id):
    #             fmt['tbr'] = formats_spec[fmt_id]['tbr']
    #             fmt['filesize'] = formats_spec[fmt_id]['filesize']
    #
    #     self._sort_formats(formats)
    #
    #     self.mark_watched(video_id, video_info, player_response)
    #
    #     return {
    #         'id': video_id,
    #         'uploader': video_uploader,
    #         'uploader_id': video_uploader_id,
    #         'uploader_url': video_uploader_url,
    #         'channel_id': channel_id,
    #         'channel_url': channel_url,
    #         'upload_date': upload_date,
    #         'license': video_license,
    #         'creator': video_creator or artist,
    #         'title': video_title,
    #         'alt_title': video_alt_title or track,
    #         'thumbnails': thumbnails,
    #         'description': video_description,
    #         'categories': video_categories,
    #         'tags': video_tags,
    #         'subtitles': video_subtitles,
    #         'automatic_captions': automatic_captions,
    #         'duration': video_duration,
    #         'age_limit': 18 if age_gate else 0,
    #         'annotations': video_annotations,
    #         'chapters': chapters,
    #         'webpage_url': proto + '://www.youtube.com/watch?v=%s' % video_id,
    #         'view_count': view_count,
    #         'like_count': like_count,
    #         'dislike_count': dislike_count,
    #         'average_rating': average_rating,
    #         'formats': formats,
    #         'is_live': is_live,
    #         'start_time': start_time,
    #         'end_time': end_time,
    #         'series': series,
    #         'season_number': season_number,
    #         'episode_number': episode_number,
    #         'track': track,
    #         'artist': artist,
    #         'album': album,
    #         'release_date': release_date,
    #         'release_year': release_year,
    #     }


class CustomYoutubeChannelIE(CustomYoutubePlaylistBaseInfoExtractor):
    IE_DESC = 'custom YouTube.com channels'
    _VALID_URL = r'https?://(?:youtu\.be|(?:\w+\.)?youtube(?:-nocookie|kids)?\.com|(?:www\.)?invidio\.us)/channel/(?P<id>[0-9A-Za-z_-]+)'
    _TEMPLATE_URL = 'https://www.youtube.com/channel/%s/videos'
    _VIDEO_RE = r'(?:title="(?P<title>[^"]+)"[^>]+)?href="/watch\?v=(?P<id>[0-9A-Za-z_-]+)&?'
    IE_NAME = 'custom youtube:channel'
    _TESTS = [{
        'note': 'paginated channel',
        'url': 'https://www.youtube.com/channel/UCKfVa3S1e4PHvxWcwyMMg8w',
        'playlist_mincount': 91,
        'info_dict': {
            'id': 'UUKfVa3S1e4PHvxWcwyMMg8w',
            'title': 'Uploads from lex will',
            'uploader': 'lex will',
            'uploader_id': 'UCKfVa3S1e4PHvxWcwyMMg8w',
        }
    }, {
        'note': 'Age restricted channel',
        # from https://www.youtube.com/user/DeusExOfficial
        'url': 'https://www.youtube.com/channel/UCs0ifCMCm1icqRbqhUINa0w',
        'playlist_mincount': 64,
        'info_dict': {
            'id': 'UUs0ifCMCm1icqRbqhUINa0w',
            'title': 'Uploads from Deus Ex',
            'uploader': 'Deus Ex',
            'uploader_id': 'DeusExOfficial',
        },
    }, {
        'url': 'https://invidio.us/channel/UC23qupoDRn9YOAVzeoxjOQA',
        'only_matching': True,
    }, {
        'url': 'https://www.youtubekids.com/channel/UCyu8StPfZWapR6rfW_JgqcA',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        if 'channel/' in url:
            rs = (False if CustomYoutubePlaylistsIE.suitable(url) or CustomYoutubeLiveIE.suitable(url)
                    else super(CustomYoutubeChannelIE, cls).suitable(url))
        else:
            rs = False
        return rs

    def _build_template_url(self, url, channel_id):
        return self._TEMPLATE_URL % channel_id

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        if 'music.youtube' in url:
            pass
        else:
            url = self._build_template_url(url, channel_id)

        # Channel by page listing is restricted to 35 pages of 30 items, i.e. 1050 videos total (see #5778)
        # Workaround by extracting as a playlist if managed to obtain channel playlist URL
        # otherwise fallback on channel by page extraction
        channel_page = self._download_webpage(
            url + '?view=57', channel_id,
            'Downloading channel page', fatal=False)
        if channel_page is False:
            channel_playlist_id = False
        else:
            channel_page = channel_page.replace(r'\x22', '"')
            channel_playlist_id = self._html_search_regex(
                    r'"playlistId":"PL(.*?)"', channel_page, 'channel id', default=None
                )
            if not channel_playlist_id:
                channel_playlist_id = self._html_search_meta(
                    'channelId', channel_page, 'channel id', default=None) or \
                    self._html_search_regex(
                        r'"channelId":"(.*?)",', channel_page, 'channel id', default=None
                    )
            else:
                playlist_id = 'PL' + channel_playlist_id
                return self.url_result(
                    compat_urlparse.urljoin(url, '/playlist?list=%s' % playlist_id), 'CustomYoutubePlaylist')
            if not channel_playlist_id:
                channel_url = self._html_search_meta(
                    ('al:ios:url', 'twitter:app:url:iphone', 'twitter:app:url:ipad'),
                    channel_page, 'channel url', default=None)
                if channel_url:
                    channel_playlist_id = self._search_regex(
                        r'vnd\.youtube://user/([0-9A-Za-z_-]+)',
                        channel_url, 'channel id', default=None)
        if channel_playlist_id and channel_playlist_id.startswith('UC'):
            playlist_id = 'UU' + channel_playlist_id[2:]
            return self.url_result(
                compat_urlparse.urljoin(url, '/playlist?list=%s' % playlist_id), 'CustomYoutubePlaylist')

        channel_page = self._download_webpage(url, channel_id, 'Downloading page #1')
        autogenerated = re.search(r'''(?x)
                class="[^"]*?(?:
                    channel-header-autogenerated-label|
                    yt-channel-title-autogenerated
                )[^"]*"''', channel_page) is not None

        if autogenerated:
            # The videos are contained in a single page
            # the ajax pages can't be used, they are empty
            entries = [
                self.url_result(
                    video_id, 'Youtube', video_id=video_id,
                    video_title=video_title)
                for video_id, video_title in self.extract_videos_from_page(channel_page)]
            return self.playlist_result(entries, channel_id)

        try:
            next(self._entries(channel_page, channel_id))
        except StopIteration:
            alert_message = self._html_search_regex(
                r'(?s)<div[^>]+class=(["\']).*?\byt-alert-message\b.*?\1[^>]*>(?P<alert>[^<]+)</div>',
                channel_page, 'alert', default=None, group='alert')
            if alert_message:
                raise ExtractorError('Youtube said: %s' % alert_message, expected=True)

        return self.playlist_result(self._entries(channel_page, channel_id), channel_id)


class CustomYoutubeUserIE(CustomYoutubeChannelIE):
    IE_DESC = 'custom YouTube.com user videos (URL or "ytuser" keyword)'
    _VALID_URL = r'(?:(?:https?://(?:\w+\.)?youtube\.com/(?:(?P<user>user|c)/)?(?!(?:attribution_link|watch|results|shared)(?:$|[^a-z_A-Z0-9-])))|ytuser:)(?!feed/)(?P<id>[A-Za-z0-9_-]+)'
    _TEMPLATE_URL = 'https://www.youtube.com/%s/%s/videos'
    IE_NAME = 'custom youtube:user'

    _TESTS = [{
        'url': 'https://www.youtube.com/user/TheLinuxFoundation',
        'playlist_mincount': 320,
        'info_dict': {
            'id': 'UUfX55Sx5hEFjoC3cNs6mCUQ',
            'title': 'Uploads from The Linux Foundation',
            'uploader': 'The Linux Foundation',
            'uploader_id': 'TheLinuxFoundation',
        }
    }, {
        # Only available via https://www.youtube.com/c/12minuteathlete/videos
        # but not https://www.youtube.com/user/12minuteathlete/videos
        'url': 'https://www.youtube.com/c/12minuteathlete/videos',
        'playlist_mincount': 249,
        'info_dict': {
            'id': 'UUVjM-zV6_opMDx7WYxnjZiQ',
            'title': 'Uploads from 12 Minute Athlete',
            'uploader': '12 Minute Athlete',
            'uploader_id': 'the12minuteathlete',
        }
    }, {
        'url': 'ytuser:phihag',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/c/gametrailers',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/gametrailers',
        'only_matching': True,
    }, {
        # This channel is not available, geo restricted to JP
        'url': 'https://www.youtube.com/user/kananishinoSMEJ/videos',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        # Don't return True if the url can be extracted with other youtube
        # extractor, the regex would is too permissive and it would match.
        if 'channel/' not in url:
            other_yt_ies = iter(klass for (name, klass) in globals().items() if name.startswith('Youtube') and name.endswith('IE') and klass is not cls)
            if any(ie.suitable(url) for ie in other_yt_ies):
                return False
            else:
                # return super(CustomYoutubeUserIE, cls).suitable(url)
                return (False if CustomYoutubePlaylistsIE.suitable(url) or CustomYoutubeLiveIE.suitable(url) else super(CustomYoutubeChannelIE, cls).suitable(url))

    def _build_template_url(self, url, channel_id):
        mobj = re.match(self._VALID_URL, url)
        return self._TEMPLATE_URL % (mobj.group('user') or 'user', mobj.group('id'))

    def _real_extract(self, url):
        channel_id = self._match_id(url)

        url = self._build_template_url(url, channel_id)

        # Channel by page listing is restricted to 35 pages of 30 items, i.e. 1050 videos total (see #5778)
        # Workaround by extracting as a playlist if managed to obtain channel playlist URL
        # otherwise fallback on channel by page extraction
        channel_page = self._download_webpage(
            url + '?view=57', channel_id,
            'Downloading channel page', fatal=False)
        if channel_page is False:
            channel_playlist_id = False
        else:
            channel_playlist_id = self._html_search_meta(
                'channelId', channel_page, 'channel id', default=None)
            if not channel_playlist_id:
                channel_url = self._html_search_meta(
                    ('al:ios:url', 'twitter:app:url:iphone', 'twitter:app:url:ipad'),
                    channel_page, 'channel url', default=None)
                if channel_url:
                    channel_playlist_id = self._search_regex(
                        r'vnd\.youtube://user/([0-9A-Za-z_-]+)',
                        channel_url, 'channel id', default=None)
        if channel_playlist_id and channel_playlist_id.startswith('UC'):
            playlist_id = 'UU' + channel_playlist_id[2:]
            return self.url_result(
                compat_urlparse.urljoin(url, '/playlist?list=%s' % playlist_id), 'CustomYoutubePlaylist')

        channel_page = self._download_webpage(url, channel_id, 'Downloading page #1')
        autogenerated = re.search(r'''(?x)
                class="[^"]*?(?:
                    channel-header-autogenerated-label|
                    yt-channel-title-autogenerated
                )[^"]*"''', channel_page) is not None

        if autogenerated:
            # The videos are contained in a single page
            # the ajax pages can't be used, they are empty
            entries = [
                self.url_result(
                    video_id, 'Youtube', video_id=video_id,
                    video_title=video_title)
                for video_id, video_title in self.extract_videos_from_page(channel_page)]
            return self.playlist_result(entries, channel_id)

        try:
            next(self._entries(channel_page, channel_id))
        except StopIteration:
            alert_message = self._html_search_regex(
                r'(?s)<div[^>]+class=(["\']).*?\byt-alert-message\b.*?\1[^>]*>(?P<alert>[^<]+)</div>',
                channel_page, 'alert', default=None, group='alert')
            if alert_message:
                raise ExtractorError('Youtube said: %s' % alert_message, expected=True)

        return self.playlist_result(self._entries(channel_page, channel_id), channel_id)


class CustomYoutubePlaylistsIE(CustomYoutubePlaylistsBaseInfoExtractor):
    IE_DESC = 'custom YouTube.com user/channel playlists'
    _VALID_URL = r'https?://(?:\w+\.)?youtube\.com/(?:user|channel|c)/(?P<id>[^/]+)/playlists'
    IE_NAME = 'custom youtube:playlists'


class CustomYoutubeLiveIE(youtube.YoutubeBaseInfoExtractor):
    IE_DESC = 'custom YouTube.com live streams'
    _VALID_URL = r'(?P<base_url>https?://(?:\w+\.)?youtube\.com/(?:(?:user|channel|c)/)?(?P<id>[^/]+))/live'
    IE_NAME = 'custom youtube:live'

    _TESTS = [{
        'url': 'https://www.youtube.com/user/TheYoungTurks/live',
        'info_dict': {
            'id': 'a48o2S1cPoo',
            'ext': 'mp4',
            'title': 'The Young Turks - Live Main Show',
            'uploader': 'The Young Turks',
            'uploader_id': 'TheYoungTurks',
            'uploader_url': r're:https?://(?:www\.)?youtube\.com/user/TheYoungTurks',
            'upload_date': '20150715',
            'license': 'Standard YouTube License',
            'description': 'md5:438179573adcdff3c97ebb1ee632b891',
            'categories': ['News & Politics'],
            'tags': ['Cenk Uygur (TV Program Creator)', 'The Young Turks (Award-Winning Work)', 'Talk Show (TV Genre)'],
            'like_count': int,
            'dislike_count': int,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        'url': 'https://www.youtube.com/channel/UC1yBKRuGpC1tSM73A0ZjYjQ/live',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/c/CommanderVideoHq/live',
        'only_matching': True,
    }, {
        'url': 'https://www.youtube.com/TheYoungTurks/live',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        channel_id = mobj.group('id')
        base_url = mobj.group('base_url')
        webpage = self._download_webpage(url, channel_id, fatal=False)
        if webpage:
            page_type = self._og_search_property(
                'type', webpage, 'page type', default='')
            video_id = self._html_search_meta(
                'videoId', webpage, 'video id', default=None)
            if page_type.startswith('video') and video_id and re.match(
                    r'^[0-9A-Za-z_-]{11}$', video_id):
                return self.url_result(video_id, CustomYoutubeIE.ie_key())
        return self.url_result(base_url)
