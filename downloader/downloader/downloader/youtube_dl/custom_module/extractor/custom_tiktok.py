# coding: utf-8
from __future__ import unicode_literals

import re, json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    compat_str,
    ExtractorError,
    float_or_none,
    int_or_none,
    str_or_none,
    try_get,
    url_or_none,
    GeoRestrictedError
)
from youtube_dl.compat import compat_http_client


class CustomTikTokBaseIE(InfoExtractor):
    @classmethod
    def suitable(cls, url):
        return False

    def _extract_video(self, data, wid, csrf_token, video_id=None):
        video = data['video']
        description = str_or_none(try_get(data, lambda x: x['desc']))
        width = int_or_none(try_get(data, lambda x: video['width']))
        height = int_or_none(try_get(data, lambda x: video['height']))

        format_urls = set()
        formats = []
        for format_id in ('download', 'play'):
            format_url = url_or_none(video.get('%sAddr' % format_id))
            if not format_url:
                continue
            if format_url in format_urls:
                continue
            format_urls.add(format_url)
            formats.append({
                'url': format_url + '&amoysharetype={"headers": {"Referer": "https://www.tiktok.com/", "Cookie": "tt_webid_v2=%s; tt_webid=%s; tt_csrf_token=%s"}}' % (wid, wid, csrf_token),
                'ext': 'mp4',
                'height': height,
                'width': width,
                'http_headers': {
                    'Referer': 'https://www.tiktok.com/',
                }
            })
        self._sort_formats(formats)

        thumbnail = url_or_none(video.get('cover'))
        duration = float_or_none(video.get('duration'))

        uploader = try_get(data, lambda x: x['author']['nickname'], compat_str)
        uploader_id = try_get(data, lambda x: x['author']['id'], compat_str)

        timestamp = int_or_none(data.get('createTime'))

        def stats(key):
            return int_or_none(try_get(
                data, lambda x: x['stats']['%sCount' % key]))

        view_count = stats('play')
        like_count = stats('digg')
        comment_count = stats('comment')
        repost_count = stats('share')

        aweme_id = data.get('id') or video_id

        return {
            'id': aweme_id,
            'title': uploader or aweme_id,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'uploader_id': uploader_id,
            'timestamp': timestamp,
            'view_count': view_count,
            'like_count': like_count,
            'comment_count': comment_count,
            'repost_count': repost_count,
            'formats': formats,
        }

    # def _extract_aweme(self, data):
    #     video_info = data['props']['pageProps']['itemInfo']
    #     title = video_info['shareMeta']['title']
    #     description = video_info['shareMeta']['desc']
    #     width = video_info['itemStruct']['video']['width']
    #     height = video_info['itemStruct']['video']['height']
    #
    #     csrf_token = data['query']['$initialProps']['$csrfToken']
    #     if not csrf_token:
    #         raise ExtractorError('not found csrf token, can`t build cookie')
    #
    #     wid = data['query']['$initialProps']['$wid']
    #     if not wid:
    #         raise ExtractorError('not found wid, can`t build cookie')
    #
    #     format_url = video_info['itemStruct']['video'].get('downloadAddr') or video_info['itemStruct']['video']['playAddr']
    #     format_url += '&amoysharetype={"headers": {"Referer": "https://www.tiktok.com/", "Host": "v16-web.tiktok.com", "Cookie": "tt_webid_v2=%s; tt_webid=%s; tt_csrf_token=%s"}}' % (wid, wid, csrf_token)
    #     formats = [
    #         {
    #             'url': format_url,
    #             'ext': 'mp4',
    #             'height': height,
    #             'width': width,
    #         }
    #     ]
    #
    #     thumbnail = video_info['itemStruct']['video']['cover']
    #     timestamp = video_info['itemStruct']['createTime']
    #     view_count = video_info['itemStruct']['stats']['playCount']
    #     duration = video_info['itemStruct']['video']['duration']
    #     aweme_id = video_info['itemStruct']['video']['id']
    #
    #     return {
    #         'id': aweme_id,
    #         'title': title or description,
    #         'description': description,
    #         'thumbnail': thumbnail,
    #         'timestamp': timestamp,
    #         'view_count': view_count,
    #         'duration': duration,
    #         'formats': formats,
    #     }


class CustomTikTokIE(CustomTikTokBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:
                                (?:m\.)?tiktok\.com/v|
                                (?:www\.)?tiktok\.com/share/video|
                                (?:www\.|m\.)?tiktok\.com/\@[^/]+/video
                            )
                            /(?P<id>\d+)
                    '''
    _TESTS = [{
        'url': 'https://m.tiktok.com/v/6606727368545406213.html',
        'md5': 'd584b572e92fcd48888051f238022420',
        'info_dict': {
            'id': '6606727368545406213',
            'ext': 'mp4',
            'title': 'Zureeal',
            'description': '#bowsette#mario#cosplay#uk#lgbt#gaming#asian#bowsettecosplay',
            'thumbnail': r're:^https?://.*~noop.image',
            'uploader': 'Zureeal',
            'timestamp': 1538248586,
            'upload_date': '20180929',
            'comment_count': int,
            'repost_count': int,
        }
    }, {
        'url': 'https://www.tiktok.com/share/video/6606727368545406213',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_initialize(self):
        # Setup session (will set necessary cookies)
        self._request_webpage(
            'https://www.tiktok.com/', None, note='Setting up session')

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(f'https://www.tiktok.com/share/video/{video_id}', video_id)
        data_info = self._parse_json(self._search_regex(
            r'<script[^>]+\bid=["\']__NEXT_DATA__[^>]+>\s*({.+?})\s*</script',
            webpage, 'data'), video_id)
        video_data = data_info['props']['pageProps']['itemInfo']['itemStruct']
        wid = data_info['query']['$initialProps']['$wid']
        csrf_token = data_info['query']['$initialProps']['$csrfToken']
        return self._extract_video(video_data, wid, csrf_token, video_id)


class CustomTikTokLiveIE(CustomTikTokBaseIE):
    _VALID_URL = r'https://(?:www\.)?tiktok\.com/@(?P<id>[^/?#&]+)/live'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url, cookie_str=''):
        """Real extraction process. Redefine in subclasses."""
        JSON_DATA_RE = r'(?is)<script[^>]+id="__NEXT_DATA__"[^>]*>(?P<json_data>.+?)</script>'
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        headers = {'cookie': cookie_str}
        webpage = self._download_webpage(url, video_id, headers=headers)
        data = json.loads(self._search_regex(JSON_DATA_RE, webpage, 'JSON-DATA', default='{}'))
        if not data:
            raise ExtractorError('Can`t found json data, maybe it change webpage?')
        item_info = data['props']['pageProps']
        title = item_info['liveProps']['title']
        description = item_info['seoProps']['metaParams']['description']
        thumbnail = item_info['liveProps']['covers'][0]
        live_url = item_info['liveProps']['liveUrl']
        formats = [
            {
                'url': live_url,
                'ext': 'mp4',
                'protocol': 'm3u8_protocol'
            }
        ]

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': '',
            'publishedAt': '',
            'view_count': '',
            'formats': formats,
        }

    def extract(self, url, cookie_str=''):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url, cookie_str)
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


class CustomTikTokMainIE(CustomTikTokBaseIE):
    _VALID_URL = r'https://(?:www\.)?tiktok\.com/foryou(?P<id>[^/?#&]+)'

