from __future__ import unicode_literals

import itertools
import hashlib
import json
import re
import datetime
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import (
    compat_str,
    compat_HTTPError,
)
from youtube_dl.utils import (
    ExtractorError,
    get_element_by_attribute,
    int_or_none,
    GeoRestrictedError,
    std_headers,
    try_get,
    float_or_none,
    lowercase_escape
)
from youtube_dl.compat import compat_http_client


class CustomInstagramInfoExtractor(InfoExtractor):
    _IS_CALL_API = False

    def _call_api(self, media_id):
        pass

    def _real_extract(self, url, instagram_cookie):
        """Real extraction process. Redefine in subclasses."""
        pass

    def extract(self, url, instagram_cookie=''):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url, instagram_cookie)
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


class CustomInstagramIE(CustomInstagramInfoExtractor):
    _VALID_URL = r'(?P<url>https?://(?:www\.)?instagram\.com/(?:p|tv|reel)/(?P<id>[^/?#&]+))'
    _TESTS = [{
        'url': 'https://instagram.com/p/aye83DjauH/?foo=bar#abc',
        'md5': '0d2da106a9d2631273e192b372806516',
        'info_dict': {
            'id': 'aye83DjauH',
            'ext': 'mp4',
            'title': 'Video by naomipq',
            'description': 'md5:1f17f0ab29bd6fe2bfad705f58de3cb8',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1371748545,
            'upload_date': '20130620',
            'uploader_id': 'naomipq',
            'uploader': 'Naomi Leonor Phan-Quang',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
    }, {
        # missing description
        'url': 'https://www.instagram.com/p/BA-pQFBG8HZ/?taken-by=britneyspears',
        'info_dict': {
            'id': 'BA-pQFBG8HZ',
            'ext': 'mp4',
            'title': 'Video by britneyspears',
            'thumbnail': r're:^https?://.*\.jpg',
            'timestamp': 1453760977,
            'upload_date': '20160125',
            'uploader_id': 'britneyspears',
            'uploader': 'Britney Spears',
            'like_count': int,
            'comment_count': int,
            'comments': list,
        },
        'params': {
            'skip_download': True,
        },
    }, {
        # multi video post
        'url': 'https://www.instagram.com/p/BQ0eAlwhDrw/',
        'playlist': [{
            'info_dict': {
                'id': 'BQ0dSaohpPW',
                'ext': 'mp4',
                'title': 'Video 1',
            },
        }, {
            'info_dict': {
                'id': 'BQ0dTpOhuHT',
                'ext': 'mp4',
                'title': 'Video 2',
            },
        }, {
            'info_dict': {
                'id': 'BQ0dT7RBFeF',
                'ext': 'mp4',
                'title': 'Video 3',
            },
        }],
        'info_dict': {
            'id': 'BQ0eAlwhDrw',
            'title': 'Post by instagram',
            'description': 'md5:0f9203fc6a2ce4d228da5754bcf54957',
        },
    }, {
        'url': 'https://instagram.com/p/-Cmh1cukG2/',
        'only_matching': True,
    }, {
        'url': 'http://instagram.com/p/9o6LshA7zy/embed/',
        'only_matching': True,
    }, {
        'url': 'https://www.instagram.com/tv/aye83DjauH/',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_embed_url(webpage):
        mobj = re.search(
            r'<iframe[^>]+src=(["\'])(?P<url>(?:https?:)?//(?:www\.)?instagram\.com/p/[^/]+/embed.*?)\1',
            webpage)
        if mobj:
            return mobj.group('url')

        blockquote_el = get_element_by_attribute(
            'class', 'instagram-media', webpage)
        if blockquote_el is None:
            return

        mobj = re.search(
            r'<a[^>]+href=([\'"])(?P<link>[^\'"]+)\1', blockquote_el)
        if mobj:
            return mobj.group('link')

    def _call_api(self, video_id):
        self._IS_CALL_API = True
        endpoint_url = f"https://instagram85.p.rapidapi.com/media/{video_id}"

        querystring = {"by": "code"}

        headers = {
            'x-rapidapi-key': "xxxxxxxxxxxxxxxxxxxxxxxx",
            'x-rapidapi-host': "xxxxxxxxxxxxxxxxxxxxx"
        }

        response = self._download_json(endpoint_url, video_id, headers=headers, query=querystring)
        if response['code'] == 200:
            pass
        else:
            raise ExtractorError(
                f'Api Call On Failure, Endpoint Is https://instagram85.p.rapidapi.com/media/, Message is {response["message"]}, Please Check It!'
            )

    def _real_extract(self, url, instagram_cookie):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if instagram_cookie:
            headers = {'cookie': instagram_cookie}
            url = mobj.group('url')
            webpage = self._download_webpage(url, video_id, headers=headers)
        else:
            # todo online server use
            # if '/tv/' in url or '/reel/' in url:
            #     self._call_api(video_id)
            # else:
            #     url = mobj.group('url') + '/embed/captioned/'
            #     webpage = self._download_webpage(url, video_id)

            url = mobj.group('url') + '/embed/captioned/'
            webpage = self._download_webpage(url, video_id)

        (media, video_url, description, thumbnail, timestamp, uploader,
         uploader_id, like_count, comment_count, comments, height,
         width) = [None] * 12

        shared_data = self._parse_json(
            self._search_regex(
                r'window\._sharedData\s*=\s*({.+?});',
                webpage, 'shared data', default='{}'),
            video_id, fatal=False)
        if shared_data:
            media = try_get(
                shared_data,
                (lambda x: x['entry_data']['PostPage'][0]['graphql']['shortcode_media'],
                 lambda x: x['entry_data']['PostPage'][0]['media']),
                dict)
        # _sharedData.entry_data.PostPage is empty when authenticated (see
        # https://github.com/ytdl-org/youtube-dl/pull/22880)
        if not media:
            additional_data = self._parse_json(
                self._search_regex(
                    r'window\.__additionalDataLoaded\s*\(\s*[^,]+,\s*({.+?})\s*\)\s*;',
                    webpage, 'additional data', default='{}'),
                video_id, fatal=False)
            if additional_data:
                media = try_get(
                    additional_data, lambda x: x.get('shortcode_media', {}) or x['graphql']['shortcode_media'],
                    dict)
        if media:
            video_url = media.get('video_url')
            height = int_or_none(media.get('dimensions', {}).get('height'))
            width = int_or_none(media.get('dimensions', {}).get('width'))
            description = try_get(
                media, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                compat_str) or media.get('caption')
            title = media.get('title') or description
            thumbnail = media.get('display_src') or media.get('thumbnail_src') or media.get('display_url')
            timestamp = int_or_none(media.get('taken_at_timestamp') or media.get('date'))
            publishedAt = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            uploader = media.get('owner', {}).get('full_name', '')
            uploader_id = media.get('owner', {}).get('username')
            view_count = media.get('video_view_count')
            duration = float_or_none(media.get('video_duration'))
            profile_info = {
                'username': media['owner']['username'],
                'profile_pic_url': media['owner']['profile_pic_url'],
                'posts': media['owner']['edge_owner_to_timeline_media']['count'],
                'followers': media['owner']['edge_followed_by']['count']
            }

            def get_count(keys, kind):
                if not isinstance(keys, (list, tuple)):
                    keys = [keys]
                for key in keys:
                    count = int_or_none(try_get(
                        media, (lambda x: x['edge_media_%s' % key]['count'],
                                lambda x: x['%ss' % kind]['count'])))
                    if count is not None:
                        return count
            like_count = get_count('preview_like', 'like')
            comment_count = get_count(
                ('preview_comment', 'to_comment', 'to_parent_comment'), 'comment')

            comments = [{
                'author': comment.get('user', {}).get('username'),
                'author_id': comment.get('user', {}).get('id'),
                'id': comment.get('id'),
                'text': comment.get('text'),
                'timestamp': int_or_none(comment.get('created_at')),
            } for comment in media.get(
                'comments', {}).get('nodes', []) if comment.get('text')]

            if media['__typename'] == 'GraphVideo':
                if not video_url:
                    video_url = self._og_search_video_url(webpage, secure=False)
                formats = [{
                    'type': 'video',
                    'url': video_url,
                    'thumbnail': thumbnail,
                    'width': width,
                    'height': height,
                }]
                result = {
                    'profile_info': profile_info,
                    'type_name': media['__typename'],
                    'id': video_id,
                    'formats': formats,
                    'ext': 'mp4',
                    'title': f'Video by {uploader_id}',
                    'description': description,
                    'thumbnail': thumbnail,
                    'publishedAt': publishedAt,
                    'view_count': view_count,
                    'duration': duration,
                    'uploader_id': uploader_id,
                    'uploader': uploader,
                    'like_count': like_count,
                    'comment_count': comment_count,
                    'comments': comments,
                }
                return result
            elif media['__typename'] == 'GraphImage':
                formats = [
                    {
                        'type': 'image',
                        'url': thumbnail,
                        'height': height,
                        'width': width
                    }
                ]
                result = {
                    'profile_info': profile_info,
                    'type_name': media['__typename'],
                    'id': video_id,
                    'formats': formats,
                    'title': f'Image by {uploader_id}',
                    'description': description,
                    'thumbnail': thumbnail,
                    'publishedAt': publishedAt,
                    'uploader_id': uploader_id,
                    'uploader': uploader,
                    'like_count': like_count,
                    'comment_count': comment_count,
                    'comments': comments,
                }
                return result
            elif media['__typename'] == 'GraphSidecar':
                formats = media.get('edge_sidecar_to_children', [])
                if formats:
                    formats = formats.get('edges', [])
                    infos = []
                    for fmt in formats:
                        if fmt['node']['__typename'] == 'GraphImage':
                            info = {
                                'type': 'image',
                                'url': fmt['node'].get('display_src') or
                                       fmt['node'].get('thumbnail_src') or
                                       fmt['node'].get('display_url'),
                                'width': int_or_none(
                                    fmt['node'].get('dimensions', {}).get('width')),
                                'height': int_or_none(
                                    fmt['node'].get('dimensions', {}).get(
                                        'height')),
                            }
                        elif fmt['node']['__typename'] == 'GraphVideo':
                            info = {
                                'type': 'video',
                                'url': fmt['node']['video_url'],
                                'thumbnail': fmt['node'].get('display_url') or fmt['node']['display_resources'][-1]['src'],
                                'width': int_or_none(
                                    fmt['node'].get('dimensions', {}).get('width')
                                ),
                                'height': int_or_none(
                                    fmt['node'].get('dimensions', {}).get('height')
                                ),
                            }
                        else:
                            continue
                        infos.append(info)
                    result = {
                        'profile_info': profile_info,
                        'type_name': media['__typename'],
                        'id': video_id,
                        'formats': infos,
                        'title': f'Sidecar by {uploader_id}',
                        'description': description,
                        'thumbnail': thumbnail,
                        'publishedAt': publishedAt,
                        'uploader_id': uploader_id,
                        'uploader': uploader,
                        'like_count': like_count,
                        'comment_count': comment_count,
                        'comments': comments,
                    }
                    return result
            else:
                raise

        if 'data-media-type="GraphImage"' in webpage:
            thumbnail_str = re.search(r'<img class="EmbeddedMediaImage".*?>', webpage).group()
            thumbnail = re.search(r'src="(.*?)"', thumbnail_str).group(1)
            size = re.search(r'/[A-Za-z]+(\d+x\d+)/', thumbnail)
            if size:
                width, height = size.group(1).split('x')
            else:
                width, height = 0, 0
            uploader_id = re.search(r'<span class="UsernameText">(.*?)</span>', webpage).group(1)
            description = None
            formats = [
                {
                    'type': 'image',
                    'url': thumbnail,
                    'height': int(height),
                    'width': int(width)
                }
            ]
            username = self._html_search_regex(
                [r'<span class="UsernameText">(.*?)</span>', r'<span class="Username">leomessi</span>'],
                webpage, 'username', default=''
            )
            profile_pic_url = self._html_search_regex(
                r'<img src="(.*?)"', webpage, 'pic', default=''
            )
            profile_info = {
                'username': username,
                'profile_pic_url': profile_pic_url,
                'posts': '',
                'followers': ''
            }

            result = {
                'profile_info': profile_info,
                'type_name': 'GraphImage',
                'id': video_id,
                'formats': formats,
                'title': f'Image by {uploader_id}',
                'description': description,
                'thumbnail': thumbnail,
                'publishedAt': '',
                'uploader_id': uploader_id,
                'uploader': uploader,
            }
            return result

        if not video_url:
            video_url = self._og_search_video_url(webpage, secure=False)

        formats = [{
            'url': video_url,
            'width': width,
            'height': height,
        }]

        if not uploader_id:
            uploader_id = self._search_regex(
                r'"owner"\s*:\s*{\s*"username"\s*:\s*"(.+?)"',
                webpage, 'uploader id', fatal=False)

        if not description:
            description = self._search_regex(
                r'"caption"\s*:\s*"(.+?)"', webpage, 'description', default=None)
            if description is not None:
                description = lowercase_escape(description)

        if not thumbnail:
            thumbnail = self._og_search_thumbnail(webpage)

        return {
            'id': video_id,
            'formats': formats,
            'ext': 'mp4',
            'title': title or 'Video by %s' % uploader_id,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'timestamp': timestamp,
            'uploader_id': uploader_id,
            'uploader': uploader,
            'like_count': like_count,
            'comment_count': comment_count,
            'comments': comments,
        }


class CustomInstagramPlaylistIE(CustomInstagramInfoExtractor):
    # A superclass for handling any kind of query based on GraphQL which
    # results in a playlist.

    _temp_player = '''
        <blockquote class="instagram-media" data-instgrm-captioned
            data-instgrm-permalink="{}?utm_source=ig_embed&utm_campaign=loading"
            data-instgrm-version="12"
            style=" background:#FFF; border:0; border-radius:3px; 
            box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);">
        </blockquote>
        <script async src="https://www.instagram.com/embed.js"></script>
    '''.strip()
    _gis_tmpl = None  # used to cache GIS request type

    @classmethod
    def suitable(cls, url):
        return False

    def _extract_graphql_next_page(self, media):
        pass

    def _parse_additional_data(self, webpage, item_id):
        # Reads a webpage and returns its Profile data
        return self._parse_json(
            self._search_regex(
                r'window\.__additionalDataLoaded\s*\(\s*[^,]+,\s*({.+?})\s*\)\s*;',
                webpage, 'additional data', default='{}'),
            item_id)

    def _parse_graphql(self, webpage, item_id):
        # Reads a webpage and returns its GraphQL data.
        return self._parse_json(
            self._search_regex(
                r'sharedData\s*=\s*({.+?})\s*;\s*[<\n]', webpage, 'data'),
            item_id)

    def _extract_graphql(self, data, url):
        # Parses GraphQL queries containing videos and generates a playlist.
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        uploader_id = self._match_id(url)
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        cursor = ''
        for page_num in itertools.count(1):
            variables = {
                'first': 12,
                'after': cursor,
            }
            variables.update(self._query_vars_for(data))
            variables = json.dumps(variables)

            if self._gis_tmpl:
                gis_tmpls = [self._gis_tmpl]
            else:
                gis_tmpls = [
                    '%s' % rhx_gis,
                    '',
                    '%s:%s' % (rhx_gis, csrf_token),
                    '%s:%s:%s' % (rhx_gis, csrf_token, std_headers['User-Agent']),
                ]

            # try all of the ways to generate a GIS query, and not only use the
            # first one that works, but cache it for future requests
            for gis_tmpl in gis_tmpls:
                try:
                    json_data = self._download_json(
                        'https://www.instagram.com/graphql/query/', uploader_id,
                        'Downloading JSON page %d' % page_num, headers={
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-Instagram-GIS': hashlib.md5(
                                ('%s:%s' % (gis_tmpl, variables)).encode('utf-8')).hexdigest(),
                        }, query={
                            'query_hash': self._QUERY_HASH,
                            'variables': variables,
                        })
                    media = self._parse_timeline_from(json_data)
                    self._gis_tmpl = gis_tmpl
                    break
                except ExtractorError as e:
                    # if it's an error caused by a bad query, and there are
                    # more GIS templates to try, ignore it and keep trying
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if gis_tmpl != gis_tmpls[-1]:
                            continue
                    raise

            edges = media.get('edges')
            if not edges or not isinstance(edges, list):
                break

            for edge in edges:
                node = edge.get('node')
                if not node or not isinstance(node, dict):
                    continue
                if node.get('__typename') != 'GraphVideo' and node.get('is_video') is not True:
                    continue
                video_id = node.get('shortcode')
                if not video_id:
                    continue

                info = self.url_result(
                    'https://instagram.com/p/%s/' % video_id,
                    ie=CustomInstagramIE.ie_key(), video_id=video_id)

                description = try_get(
                    node, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                    compat_str)
                thumbnail = node.get('thumbnail_src') or node.get('display_src')
                timestamp = int_or_none(node.get('taken_at_timestamp'))

                comment_count = get_count('to_comment')
                like_count = get_count('preview_like')
                view_count = int_or_none(node.get('video_view_count'))

                info.update({
                    'description': description,
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'comment_count': comment_count,
                    'like_count': like_count,
                    'view_count': view_count,
                })

                yield info

            page_info = media.get('page_info')
            if not page_info or not isinstance(page_info, dict):
                break

            has_next_page = page_info.get('has_next_page')
            if not has_next_page:
                break

            cursor = page_info.get('end_cursor')
            if not cursor or not isinstance(cursor, compat_str):
                break

    def _real_extract(self, url, instagram_cookie):
        user_or_tag = self._match_id(url)
        webpage = self._download_webpage(url, user_or_tag)
        data = self._parse_graphql(webpage, user_or_tag)

        self._set_cookie('instagram.com', 'ig_pr', '1')

        return self.playlist_result(
            self._extract_graphql(data, url), user_or_tag, user_or_tag)


class CustomInstagramUserIE(CustomInstagramPlaylistIE):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/(?P<id>[^/]{2,})/?(?:$|[?#])?'
    IE_DESC = 'custom Instagram user profile'
    IE_NAME = 'custom instagram:user'
    _TEST = {
        'url': 'https://instagram.com/porsche',
        'info_dict': {
            'id': 'porsche',
            'title': 'porsche',
        },
        'playlist_count': 5,
        'params': {
            'extract_flat': True,
            'skip_download': True,
            'playlistend': 5,
        }
    }

    _QUERY_HASH = '42323d64886122307be10013ad2dcc44'

    @classmethod
    def suitable(cls, url):
        rs = (re.match(cls._VALID_URL, url) is not None and '/stories/' not in url and '/explore/' not in url and '/graphql/query/' not in url) or \
             ('https://www.instagram.com/graphql/query/' in url and 'category=user' in url)
        return rs

    @staticmethod
    def _parse_timeline_from(data):
        # extracts the media timeline data from a GraphQL result
        return data['data']['user']['edge_owner_to_timeline_media']

    @staticmethod
    def _query_vars_for(data):
        # returns a dictionary of variables to add to the timeline query based
        # on the GraphQL of the original page
        return {
            'id': data['entry_data']['ProfilePage'][0]['graphql']['user']['id']
        }

    def _extract_graphql(self, data, url, instagram_cookie):
        # Parses GraphQL queries containing videos and generates a playlist.
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        uploader_id = self._match_id(url)
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        cursor = ''
        for page_num in itertools.count(1):
            variables = {
                'first': 20,
                'after': cursor,
            }
            variables.update(self._query_vars_for(data))
            variables = json.dumps(variables)

            if self._gis_tmpl:
                gis_tmpls = [self._gis_tmpl]
            else:
                gis_tmpls = [
                    '%s' % rhx_gis,
                    '',
                    '%s:%s' % (rhx_gis, csrf_token),
                    '%s:%s:%s' % (rhx_gis, csrf_token, std_headers['User-Agent']),
                ]

            # try all of the ways to generate a GIS query, and not only use the
            # first one that works, but cache it for future requests
            for gis_tmpl in gis_tmpls:
                try:
                    json_data = self._download_json(
                        'https://www.instagram.com/graphql/query/',
                        uploader_id,
                        'Downloading JSON page %d' % page_num,
                        headers={
                            'cookie': instagram_cookie,
                            # 'X-Requested-With': 'XMLHttpRequest',
                            # 'X-Instagram-GIS': hashlib.md5(
                            #     ('%s:%s' % (gis_tmpl, variables)).encode('utf-8')).hexdigest(),
                        },
                        query={
                            'query_hash': self._QUERY_HASH,
                            'variables': variables,
                        })
                    media = self._parse_timeline_from(json_data)
                    self._gis_tmpl = gis_tmpl
                    break
                except ExtractorError as e:
                    # if it's an error caused by a bad query, and there are
                    # more GIS templates to try, ignore it and keep trying
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if gis_tmpl != gis_tmpls[-1]:
                            continue
                    raise

            edges = media.get('edges')
            if not edges or not isinstance(edges, list):
                break

            for edge in edges:
                node = edge.get('node')
                if not node or not isinstance(node, dict):
                    continue
                video_id = node.get('shortcode')
                if not video_id:
                    continue

                info = self.url_result(
                    'https://instagram.com/p/%s/' % video_id,
                    ie=self.ie_key(), video_id=video_id)

                description = try_get(
                    node, lambda x: x['edge_media_to_caption']['edges'][0]['node']['text'],
                    compat_str)
                thumbnail = node.get('thumbnail_src') or node.get('display_url')
                timestamp = int_or_none(node.get('taken_at_timestamp'))

                comment_count = get_count('to_comment')
                like_count = get_count('preview_like')
                view_count = int_or_none(node.get('video_view_count'))
                if 'GraphVideo' == node['__typename']:
                    typename = 'video'
                elif 'GraphImage' == node['__typename']:
                    typename = 'image'
                elif 'GraphSidecar' == node['__typename']:
                    typename = 'sidecar'
                else:
                    continue
                player = self._temp_player.format(info['url'])

                info.update({
                    'title': description or '',
                    'description': description or '',
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'comment_count': comment_count,
                    'like_count': like_count,
                    'view_count': view_count,
                    'player': player,
                    'format': typename
                })

                yield info

            page_info = media.get('page_info')
            if not page_info or not isinstance(page_info, dict):
                break

            cursor = page_info.get('end_cursor')
            # if not cursor or not isinstance(cursor, compat_str):
            #     break

            has_next_page = page_info.get('has_next_page')
            if not has_next_page or page_num == 1:
                variables = {
                    'first': 20,
                    'after': cursor,
                }
                variables.update(self._query_vars_for(data))
                variables = json.dumps(variables)
                next_page = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=user'.format(self._QUERY_HASH, variables)
                yield next_page
                break

    def _extract_graphql_next_page(self, media):
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        edges = media.get('edges')
        if not edges or not isinstance(edges, list):
            raise
        for edge in edges:
            node = edge.get('node')
            if not node or not isinstance(node, dict):
                continue
            video_id = node.get('shortcode')
            if not video_id:
                continue

            info = self.url_result(
                'https://instagram.com/p/%s/' % video_id,
                ie=self.ie_key(), video_id=video_id)

            description = try_get(
                node, lambda x: x['edge_media_to_caption']['edges'][0]['node'][
                    'text'],
                compat_str)
            thumbnail = node.get('thumbnail_src') or node.get('display_url')
            timestamp = int_or_none(node.get('taken_at_timestamp'))

            comment_count = get_count('to_comment')
            like_count = get_count('preview_like')
            view_count = int_or_none(node.get('video_view_count'))
            if 'GraphVideo' == node['__typename']:
                typename = 'video'
            elif 'GraphImage' == node['__typename']:
                typename = 'image'
            elif 'GraphSidecar' == node['__typename']:
                typename = 'sidecar'
            else:
                continue
            player = self._temp_player.format(info['url'])

            info.update({
                'title': description or '',
                'description': description or '',
                'thumbnail': thumbnail,
                'timestamp': timestamp,
                'comment_count': comment_count,
                'like_count': like_count,
                'view_count': view_count,
                'player': player,
                'format': typename
            })

            yield info

        page_info = media.get('page_info')
        if not page_info or not isinstance(page_info, dict):
            raise

        cursor = page_info.get('end_cursor')
        # if not cursor or not isinstance(cursor, compat_str):
        #     raise

        has_next_page = page_info.get('has_next_page')
        if has_next_page:
            variables = {
                'first': 20,
                'after': cursor,
            }
            idd = edges[0]['node']['owner']['id']
            variables.update({'id': '%s' % idd})
            variables = json.dumps(variables)
            next_page = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=user'.format(
                self._QUERY_HASH, variables)
            yield next_page
        else:
            yield None

    def _real_extract(self, url, instagram_cookie):
        if 'category=user' in url:
            for i in range(3):
                try:
                    json_data = self._download_json(
                        url,
                        'user',
                        'Downloading JSON page',
                        headers={
                            'cookie': instagram_cookie
                        }
                    )
                    media = self._parse_timeline_from(json_data)
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if i != 2:
                            continue
                        raise

            ties = []
            results = self._extract_graphql_next_page(media)
            for result in results:
                ties.append(result)

            if isinstance(ties[-1], compat_str):
                next_page = ties.pop()
            else:
                next_page = None
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result
        else:
            user_or_tag = self._match_id(url)
            webpage = self._download_webpage(
                url,
                user_or_tag,
                headers={
                    'cookie': instagram_cookie
                }
            )
            profile_data = self._parse_additional_data(webpage, user_or_tag)
            data = self._parse_graphql(webpage, user_or_tag)
            profile_info = {
                'id': profile_data['graphql']['user']['id'],
                'username': profile_data['graphql']['user']['username'],
                'full_name': profile_data['graphql']['user']['full_name'],
                'description': profile_data['graphql']['user']['biography'],
                'profile_pic_url': profile_data['graphql']['user']['profile_pic_url_hd'] or profile_data['graphql']['user']['profile_pic_url'],
                'followers': profile_data['graphql']['user']['edge_followed_by'],
                'posts': profile_data['graphql']['user']['edge_owner_to_timeline_media']['count'],
                'followings': profile_data['graphql']['user']['edge_follow']['count']
            }
            if not data['entry_data']['ProfilePage'][0]:
                data['entry_data']['ProfilePage'][0]['graphql'] = {'user': profile_info}

            self._set_cookie('instagram.com', 'ig_pr', '1')

            ties = []
            results = self._extract_graphql(data, url, instagram_cookie)
            for result in results:
                ties.append(result)

            if isinstance(ties[-1], compat_str):
                next_page = ties.pop()
            else:
                next_page = None
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    # 'profile_info': profile_info,
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result


class CustomInstagramTagIE(CustomInstagramPlaylistIE):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/explore/tags/(?P<id>[^/]+)'
    IE_DESC = 'custom Instagram hashtag search'
    IE_NAME = 'custom instagram:tag'
    _TEST = {
        'url': 'https://instagram.com/explore/tags/lolcats',
        'info_dict': {
            'id': 'lolcats',
            'title': 'lolcats',
        },
        'playlist_count': 50,
        'params': {
            'extract_flat': True,
            'skip_download': True,
            'playlistend': 50,
        }
    }

    _QUERY_HASH = 'f92f56d47dc7a55b606908374b43a314'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None or \
             ('https://www.instagram.com/graphql/query/' in url and 'category=tag' in url)
        return rs

    @staticmethod
    def _parse_timeline_from(data):
        # extracts the media timeline data from a GraphQL result
        return data['data']['hashtag']['edge_hashtag_to_media']

    @staticmethod
    def _query_vars_for(data):
        # returns a dictionary of variables to add to the timeline query based
        # on the GraphQL of the original page
        return {
            'tag_name':
                data['entry_data']['TagPage'][0]['graphql']['hashtag']['name']
        }

    def _extract_graphql(self, data, url, instagram_cookie):
        # Parses GraphQL queries containing videos and generates a playlist.
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        uploader_id = self._match_id(url)
        csrf_token = data['config']['csrf_token']
        rhx_gis = data.get('rhx_gis') or '3c7ca9dcefcf966d11dacf1f151335e8'

        top_posts = data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_top_posts']['edges']

        cursor = ''
        for page_num in itertools.count(1):
            variables = {
                'first': 20,
                'after': cursor,
            }
            variables.update(self._query_vars_for(data))
            variables = json.dumps(variables)

            if self._gis_tmpl:
                gis_tmpls = [self._gis_tmpl]
            else:
                gis_tmpls = [
                    '%s' % rhx_gis,
                    '',
                    '%s:%s' % (rhx_gis, csrf_token),
                    '%s:%s:%s' % (rhx_gis, csrf_token, std_headers['User-Agent']),
                ]

            # try all of the ways to generate a GIS query, and not only use the
            # first one that works, but cache it for future requests
            for gis_tmpl in gis_tmpls:
                try:
                    json_data = self._download_json(
                        'https://www.instagram.com/graphql/query/',
                        uploader_id,
                        'Downloading JSON page %d' % page_num,
                        headers={
                            'cookie': instagram_cookie,
                            # 'X-Requested-With': 'XMLHttpRequest',
                            # 'X-Instagram-GIS': hashlib.md5(
                            #     ('%s:%s' % (gis_tmpl, variables)).encode('utf-8')).hexdigest(),
                        },
                        query={
                            'query_hash': self._QUERY_HASH,
                            'variables': variables,
                        }
                    )
                    media = self._parse_timeline_from(json_data)
                    self._gis_tmpl = gis_tmpl
                    break
                except ExtractorError as e:
                    # if it's an error caused by a bad query, and there are
                    # more GIS templates to try, ignore it and keep trying
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if gis_tmpl != gis_tmpls[-1]:
                            continue
                    raise

            edges = media.get('edges')
            if not edges or not isinstance(edges, list):
                break
            edges = top_posts + edges
            for edge in edges:
                node = edge.get('node')
                if not node or not isinstance(node, dict):
                    continue
                video_id = node.get('shortcode')
                if not video_id:
                    continue

                info = self.url_result(
                    'https://instagram.com/p/%s/' % video_id,
                    ie=self.ie_key(), video_id=video_id)

                description = try_get(
                    node,
                    lambda x: x['edge_media_to_caption']['edges'][0]['node'][
                        'text'],
                    compat_str)
                thumbnail = node.get('thumbnail_src') or node.get('display_url')
                timestamp = int_or_none(node.get('taken_at_timestamp'))

                comment_count = get_count('to_comment')
                like_count = get_count('preview_like')
                view_count = int_or_none(node.get('video_view_count'))
                if 'GraphVideo' == node['__typename']:
                    typename = 'video'
                elif 'GraphImage' == node['__typename']:
                    typename = 'image'
                elif 'GraphSidecar' == node['__typename']:
                    typename = 'sidecar'
                else:
                    continue
                player = self._temp_player.format(info['url'])

                info.update({
                    'title': description or '',
                    'description': description or '',
                    'thumbnail': thumbnail,
                    'timestamp': timestamp,
                    'comment_count': comment_count,
                    'like_count': like_count,
                    'view_count': view_count,
                    'player': player,
                    'format': typename
                })

                yield info

            page_info = media.get('page_info')
            if not page_info or not isinstance(page_info, dict):
                break

            cursor = page_info.get('end_cursor')
            # if not cursor or not isinstance(cursor, compat_str):
            #     break

            has_next_page = page_info.get('has_next_page')
            if has_next_page:
                variables = {
                    'first': 20,
                    'after': cursor,
                }
                variables.update(self._query_vars_for(data))
                variables = json.dumps(variables)
                next_page = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=tag'.format(
                    self._QUERY_HASH, variables)
                yield next_page
            else:
                yield None
            break

    def _extract_graphql_next_page(self, media, tag):
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        edges = media.get('edges')
        if not edges or not isinstance(edges, list):
            raise
        for edge in edges:
            node = edge.get('node')
            if not node or not isinstance(node, dict):
                continue
            video_id = node.get('shortcode')
            if not video_id:
                continue

            info = self.url_result(
                'https://instagram.com/p/%s/' % video_id,
                ie=self.ie_key(), video_id=video_id)

            description = try_get(
                node, lambda x: x['edge_media_to_caption']['edges'][0]['node'][
                    'text'],
                compat_str)
            thumbnail = node.get('thumbnail_src') or node.get('display_url')
            timestamp = int_or_none(node.get('taken_at_timestamp'))

            comment_count = get_count('to_comment')
            like_count = get_count('preview_like')
            view_count = int_or_none(node.get('video_view_count'))
            if 'GraphVideo' == node['__typename']:
                typename = 'video'
            elif 'GraphImage' == node['__typename']:
                typename = 'image'
            elif 'GraphSidecar' == node['__typename']:
                typename = 'sidecar'
            else:
                continue
            player = self._temp_player.format(info['url'])

            info.update({
                'title': description or '',
                'description': description or '',
                'thumbnail': thumbnail,
                'timestamp': timestamp,
                'comment_count': comment_count,
                'like_count': like_count,
                'view_count': view_count,
                'player': player,
                'format': typename
            })

            yield info

        page_info = media.get('page_info')
        if not page_info or not isinstance(page_info, dict):
            raise

        cursor = page_info.get('end_cursor')
        # if not cursor or not isinstance(cursor, compat_str):
        #     raise

        has_next_page = page_info.get('has_next_page')
        if has_next_page:
            variables = {
                'first': 20,
                'after': cursor,
            }
            variables.update({'tag_name': tag})
            variables = json.dumps(variables)
            next_page = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=tag'.format(
                self._QUERY_HASH, variables)
            yield next_page
        else:
            yield None

    def _real_extract(self, url, instagram_cookie):
        if 'category=tag' in url:
            tag = re.search(r'"tag_name":.*?"(.*?)"', url)
            if tag:
                tag = tag.group(1)
            else:
                raise
            for i in range(3):
                try:
                    json_data = self._download_json(
                        url,
                        'tag',
                        'Downloading JSON page',
                        headers={
                            'cookie': instagram_cookie
                        }
                    )
                    media = self._parse_timeline_from(json_data)
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if i != 2:
                            continue
                        raise

            ties = []
            results = self._extract_graphql_next_page(media, tag)
            for result in results:
                ties.append(result)

            next_page = ties.pop()
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result
        else:
            user_or_tag = self._match_id(url)
            webpage = self._download_webpage(
                url,
                user_or_tag,
                headers={
                    'cookie': instagram_cookie
                }
            )
            data = self._parse_graphql(webpage, user_or_tag)
            profile_info = {
                'name': data['entry_data']['TagPage'][0]['graphql']['hashtag']['name'],
                'thumbnail': data['entry_data']['TagPage'][0]['graphql']['hashtag']['profile_pic_url'],
                'post_num': data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_media']['count'],
                'related_tags': [x['node']['name'] for x in data['entry_data']['TagPage'][0]['graphql']['hashtag']['edge_hashtag_to_related_tags']['edges']]
            }

            self._set_cookie('instagram.com', 'ig_pr', '1')

            ties = []
            results = self._extract_graphql(data, url, instagram_cookie)
            for result in results:
                ties.append(result)
            next_page = ties.pop()
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    'profile_info': profile_info,
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result


class CustomInstagramLocationIE(CustomInstagramPlaylistIE):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/explore/locations/(?P<id>\d+)/(?P<name>[^/]+)'
    _VALID_URL1 = r'https?://(?:www\.)?instagram\.com/explore/locations/(?P<id>\d+)'
    IE_DESC = 'custom Instagram location search'
    IE_NAME = 'custom instagram:location'
    _QUERY_HASH = '36bd0f2bf5911908de389b8ceaa3be6d'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None or \
             re.match(cls._VALID_URL1, url) is not None or \
             ('https://www.instagram.com/graphql/query/' in url and 'category=location' in url)
        return rs

    @staticmethod
    def _parse_timeline_from(data):
        # extracts the media timeline data from a GraphQL result
        return data['data']['location']['edge_location_to_media']

    def _extract_graphql_next_page(self, media, location_id, top_posts=[]):
        def get_count(suffix):
            return int_or_none(try_get(
                node, lambda x: x['edge_media_' + suffix]['count']))

        edges = media.get('edges')
        if not edges or not isinstance(edges, list):
            raise

        edges = top_posts + edges
        for edge in edges:
            node = edge.get('node')
            if not node or not isinstance(node, dict):
                continue
            video_id = node.get('shortcode')
            if not video_id:
                continue

            info = self.url_result(
                'https://instagram.com/p/%s/' % video_id,
                ie=self.ie_key(), video_id=video_id)

            description = try_get(
                node, lambda x: x['edge_media_to_caption']['edges'][0]['node'][
                    'text'],
                compat_str)
            thumbnail = node.get('thumbnail_src') or node.get('display_url')
            timestamp = int_or_none(node.get('taken_at_timestamp'))

            comment_count = get_count('to_comment')
            like_count = get_count('preview_like')
            view_count = int_or_none(node.get('video_view_count'))
            if node['is_video']:
                typename = 'video'
            else:
                typename = 'image'
            player = self._temp_player.format(info['url'])

            info.update({
                'title': description or '',
                'description': description or '',
                'thumbnail': thumbnail,
                'timestamp': timestamp,
                'comment_count': comment_count,
                'like_count': like_count,
                'view_count': view_count,
                'player': player,
                'format': typename
            })

            yield info

        page_info = media.get('page_info')
        if not page_info or not isinstance(page_info, dict):
            raise

        cursor = page_info.get('end_cursor')
        # if not cursor or not isinstance(cursor, compat_str):
        #     raise

        has_next_page = page_info.get('has_next_page')
        if has_next_page:
            variables = {
                'first': 20,
                'after': cursor,
            }
            variables.update({'id': location_id})
            variables = json.dumps(variables)
            next_page = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=location'.format(
                self._QUERY_HASH, variables)
            yield next_page
        else:
            yield None

    @classmethod
    def _match_id(cls, url):
        if '_VALID_URL_RE' not in cls.__dict__:
            cls._VALID_URL_RE = re.compile(cls._VALID_URL)
            m = cls._VALID_URL_RE.match(url)
            if not m:
                cls._VALID_URL_RE = re.compile(cls._VALID_URL1)
                m = cls._VALID_URL_RE.match(url)
        assert m
        return compat_str(m.group('id'))

    def _real_extract(self, url, instagram_cookie):
        if 'category=location' in url:
            location_id = re.search(r'"id":.*?"(.*?)"', url)
            if location_id:
                location_id = location_id.group(1)
            else:
                raise
            for i in range(3):
                try:
                    json_data = self._download_json(
                        url,
                        'location',
                        'Downloading JSON page',
                        headers={
                            'cookie': instagram_cookie
                        }
                    )
                    media = self._parse_timeline_from(json_data)
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if i != 2:
                            continue
                        raise

            ties = []
            results = self._extract_graphql_next_page(media, location_id)
            for result in results:
                ties.append(result)

            if isinstance(ties[-1], compat_str):
                next_page = ties.pop()
            else:
                next_page = None
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result
        else:
            location_id = self._match_id(url)
            webpage = self._download_webpage(
                url,
                location_id,
                headers={
                    'cookie': instagram_cookie
                }
            )
            data = self._parse_graphql(webpage, location_id)
            profile_info = {
                'id': data['entry_data']['LocationsPage'][0]['graphql']['location']['id'],
                'name': data['entry_data']['LocationsPage'][0]['graphql']['location']['name'],
                'profile_pic_url': data['entry_data']['LocationsPage'][0]['graphql']['location']['profile_pic_url'],
                'posts': data['entry_data']['LocationsPage'][0]['graphql']['location']['edge_location_to_media']['count'],
            }

            self._set_cookie('instagram.com', 'ig_pr', '1')

            variables = {
                'first': 20,
                'after': '',
                'id': location_id
            }
            variables = json.dumps(variables)
            url = 'https://www.instagram.com/graphql/query/?query_hash={}&variables={}&category=location'.format(
                self._QUERY_HASH, variables)

            for i in range(3):
                try:
                    json_data = self._download_json(
                        url,
                        'location',
                        'Downloading JSON page',
                        headers={
                            'cookie': instagram_cookie
                        }
                    )
                    media = self._parse_timeline_from(json_data)
                    break
                except ExtractorError as e:
                    if isinstance(e.cause, compat_HTTPError) and e.cause.code == 403:
                        if i != 2:
                            continue
                        raise

            top_posts = data['entry_data']['LocationsPage'][0]['graphql']['location']['edge_location_to_top_posts']['edges']
            ties = []
            results = self._extract_graphql_next_page(media, location_id, top_posts)
            for result in results:
                ties.append(result)
            next_page = ties.pop()
            ie_result = self.playlist_result(ties, url)
            ie_result.update(
                {
                    'profile_info': profile_info,
                    'nextPageToken': next_page,
                    'is_next_page': True if next_page else False,
                    'next_page': next_page
                }
            )
            # print(json.dumps(ie_result))
            return ie_result


class CustomInstagramStoryIE(CustomInstagramInfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/stories/(?:tags/|locations/)?(?P<name>[^/]+)/'
    IE_DESC = 'custom Instagram story'
    IE_NAME = 'custom instagram:story'
    _QUERY_HASH = '90709b530ea0969f002c86a89b4f2b8d'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None and '/highlights/' not in url
        return rs

    def _match_name(self, url):
        self._VALID_URL_RE = re.compile(self._VALID_URL)
        m2 = self._VALID_URL_RE.match(url)
        assert m2
        return compat_str(m2.group('name'))

    def _real_extract(self, url, instagram_cookie):
        name = self._match_name(url)

        if 'stories/tags' in url:
            rs_url = 'https://www.instagram.com/graphql/query/?query_hash=%s&variables={"reel_ids":[],"tag_names":["%s"],"location_ids":[],"highlight_reel_ids":[],"precomposed_overlay":false,"show_story_viewer_list":true,"story_viewer_fetch_count":50,"story_viewer_cursor":"","stories_video_dash_manifest":false}' % (self._QUERY_HASH, name)
        elif 'stories/locations' in url:
            rs_url = 'https://www.instagram.com/graphql/query/?query_hash=%s&variables={"reel_ids":[],"tag_names":[],"location_ids":["%s"],"highlight_reel_ids":[],"precomposed_overlay":false,"show_story_viewer_list":true,"story_viewer_fetch_count":50,"story_viewer_cursor":"","stories_video_dash_manifest":false}' % (self._QUERY_HASH, name)
        else:
            reel_id_url = 'https://www.instagram.com/stories/{}/?__a=1'.format(
                name)
            json_data = self._download_json(
                reel_id_url,
                'user id',
                'Downloading JSON page',
            )
            reel_id = json_data['user']['id']
            rs_url = 'https://www.instagram.com/graphql/query/?query_hash=%s&variables={"reel_ids":["%s"],"tag_names":[],"location_ids":[],"highlight_reel_ids":[],"precomposed_overlay":false,"show_story_viewer_list":true,"story_viewer_fetch_count":50,"story_viewer_cursor":"","stories_video_dash_manifest":false}' % (self._QUERY_HASH, reel_id)

        rs_data = self._download_json(
            rs_url,
            'result',
            'Downloading JSON page',
            headers={
                'cookie': instagram_cookie
            }
        )
        if rs_data['status'] == 'ok':
            media = rs_data['data']['reels_media'][0]
            formats = []
            items = media['items']
            for item in items:
                if item['__typename'] == 'GraphStoryImage':
                    info = {
                        'type': 'image',
                        'url': item.get('display_url') or item['display_resources'][-1]['src'],
                        'height': item['dimensions']['height'],
                        'width': item['dimensions']['width'],
                    }
                    formats.append(info)
                elif item['__typename'] == 'GraphStoryVideo':
                    info = {
                        'type': 'video',
                        'thumbnail': item.get('display_url') or item['display_resources'][-1]['src'],
                        'url': item['video_resources'][-1]['src'],
                        'width': item['video_resources'][-1]['config_width'],
                        'height': item['video_resources'][-1]['config_height'],
                    }
                    formats.append(info)
                else:
                    pass
            thumbnail = formats[0].get('thumbnail') or formats[0]['url']
            videos = [f for f in formats if f['type'] == 'video']
            if videos:
                player = '<video controls="" autoplay="" name="media" ' \
                         'width="100%" height="100%">' \
                         '<source src="{}" type="video/mp4"></video>'.format(videos[0]['url'])
            else:
                player = '<img src="{}">'.format(formats[0]['url'])
            result = {
                'type_name': 'GraphSidecar',
                'id': media['id'],
                'formats': formats,
                'thumbnail': thumbnail,
                'player': player,
                # 'title': f'Story by {media["owner"]["username"]}',
                'title': f'Story by {name}',
                'publishedAt': datetime.datetime.fromtimestamp(media['latest_reel_media']).strftime('%Y-%m-%d %H:%M:%S'),
            }
            # print(json.dumps(result))
            return result


class CustomInstagramStoryHighLightIE(CustomInstagramInfoExtractor):
    '''https://www.instagram.com/stories/highlights/17873230696651027/'''
    '''https://www.instagram.com/s/aGlnaGxpZ2h0OjE3ODYxNzM3MjQzODExNTc2/'''
    _VALID_URL = r'https?://(?:www\.)?instagram\.com/stories/highlights/(?P<id>\d+)/'
    _VALID_URL1 = r'https?://(?:www\.)?instagram\.com/s/(?P<name>[^/?]+)'
    IE_DESC = 'custom Instagram storyhighlight'
    IE_NAME = 'custom instagram:storyhighlight'
    _QUERY_HASH = '90709b530ea0969f002c86a89b4f2b8d'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None or re.match(cls._VALID_URL1, url) is not None
        return rs

    def _match_id(self, url):
        self._VALID_URL_RE = re.compile(self._VALID_URL)
        kk = self._VALID_URL_RE.match(url)
        assert kk
        return compat_str(kk.group('id'))

    def _match_name(self, url):
        self._VALID_URL_RE1 = re.compile(self._VALID_URL1)
        m1 = self._VALID_URL_RE1.match(url)
        assert m1
        return compat_str(m1.group('name'))

    def _real_extract(self, url, instagram_cookie):
        if '/s/' in url:
            name = self._match_name(url)
            redirect_url = f'https://www.instagram.com/s/{name}/'
            redirect_page = self._download_webpage(redirect_url, name, 'to get real url')
            url = self._html_search_meta('og:url', redirect_page, 'redirect_url')
        rid = self._match_id(url)

        rs_url = 'https://www.instagram.com/graphql/query/?query_hash=%s&variables={"reel_ids":[],"tag_names":[],"location_ids":[],"highlight_reel_ids":["%s"],"precomposed_overlay":false,"show_story_viewer_list":true,"story_viewer_fetch_count":50,"story_viewer_cursor":"","stories_video_dash_manifest":false}' % (self._QUERY_HASH, rid)
        rs_data = self._download_json(
            rs_url,
            'result',
            'Downloading JSON page',
            headers={
                'cookie': instagram_cookie
            }
        )
        if rs_data['status'] == 'ok':
            media = rs_data['data']['reels_media'][0]
            formats = []
            items = media['items']
            for item in items:
                if item['__typename'] == 'GraphStoryImage':
                    info = {
                        'type': 'image',
                        'url': item.get('display_url') or
                               item['display_resources'][-1]['src'],
                        'height': item['dimensions']['height'],
                        'width': item['dimensions']['width'],
                    }
                    formats.append(info)
                elif item['__typename'] == 'GraphStoryVideo':
                    info = {
                        'type': 'video',
                        'thumbnail': item.get('display_url') or
                                     item['display_resources'][-1]['src'],
                        'url': item['video_resources'][-1]['src'],
                        'width': item['video_resources'][-1]['config_width'],
                        'height': item['video_resources'][-1]['config_height'],
                    }
                    formats.append(info)
                else:
                    pass
            thumbnail = formats[0].get('thumbnail') or formats[0]['url']
            videos = [f for f in formats if f['type'] == 'video']
            if videos:
                player = '<video controls="" autoplay="" name="media" ' \
                         'width="100%" height="100%">' \
                         '<source src="{}" type="video/mp4"></video>'.format(
                    videos[0]['url'])
            else:
                player = '<img src="{}">'.format(formats[0]['url'])
            result = {
                'type_name': 'GraphSidecar',
                'id': media['id'],
                'formats': formats,
                'thumbnail': thumbnail,
                'player': player,
                'title': f'StoryHighLight by {media["owner"]["username"]}',
                'publishedAt': datetime.datetime.fromtimestamp(
                    items[0]['taken_at_timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            }
            # print(json.dumps(result))
            return result
