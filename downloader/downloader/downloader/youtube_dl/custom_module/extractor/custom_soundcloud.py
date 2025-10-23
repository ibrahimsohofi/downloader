#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import re
import json
import itertools
from youtube_dl.extractor.common import (
    InfoExtractor,
    SearchInfoExtractor
)
from youtube_dl.compat import (
    compat_HTTPError,
    compat_kwargs,
    compat_str,
    compat_urlparse
)
from youtube_dl.utils import (
    error_to_compat_str,
    ExtractorError,
    float_or_none,
    HEADRequest,
    int_or_none,
    KNOWN_EXTENSIONS,
    mimetype2ext,
    str_or_none,
    try_get,
    unified_timestamp,
    update_url_query,
    url_or_none,
    urlhandle_detect_ext,
)


class CustomSoundcloudIE(InfoExtractor):
    """Information extractor for soundcloud.com
       To access the media, the uid of the song and a stream token
       must be extracted from the page source and the script must make
       a request to media.soundcloud.com/crossdomain.xml. Then
       the media can be grabbed by requesting from an url composed
       of the stream token and uid
     """

    _VALID_URL = r'''(?x)^(?:https?://)?
                    (?:(?:(?:www\.|m\.)?soundcloud\.com/
                            (?!stations/track)
                            (?P<uploader>[\w\d-]+)/
                            (?!(?:tracks|albums|sets(?:/.+?)?|reposts|likes|spotlight)/?(?:$|[?#]))
                            (?P<title>[\w\d-]+)/?
                            (?P<token>[^?]+?)?(?:[?].*)?$)
                       |(?:api(?:-v2)?\.soundcloud\.com/tracks/(?P<track_id>\d+)
                          (?:/?\?secret_token=(?P<secret_token>[^&]+))?)
                    )
                    '''
    IE_NAME = 'custom soundcloud'

    _API_V2_BASE = 'https://api-v2.soundcloud.com/'
    _BASE_URL = 'https://soundcloud.com/'
    _IMAGE_REPL_RE = r'-([0-9a-z]+)\.jpg'

    _ARTWORK_MAP = {
        'mini': 16,
        'tiny': 20,
        'small': 32,
        'badge': 47,
        't67x67': 67,
        'large': 100,
        't300x300': 300,
        'crop': 400,
        't500x500': 500,
        'original': 0,
    }

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) and '/popular-tracks' not in url
        return rs

    def _store_client_id(self, client_id):
        self._downloader.cache.store('soundcloud', 'client_id', client_id)

    def _update_client_id(self):
        webpage = self._download_webpage('https://soundcloud.com/', None)
        for src in reversed(re.findall(r'<script[^>]+src="([^"]+)"', webpage)):
            script = self._download_webpage(src, None, fatal=False)
            if script:
                client_id = self._search_regex(
                    r'client_id\s*:\s*"([0-9a-zA-Z]{32})"',
                    script, 'client id', default=None)
                if client_id:
                    self._CLIENT_ID = client_id
                    self._store_client_id(client_id)
                    return
        raise ExtractorError('Unable to extract client id')

    def _download_json(self, *args, **kwargs):
        non_fatal = kwargs.get('fatal') is False
        if non_fatal:
            del kwargs['fatal']
        query = kwargs.get('query', {}).copy()
        for _ in range(2):
            query['client_id'] = self._CLIENT_ID
            kwargs['query'] = query
            try:
                return super(CustomSoundcloudIE, self)._download_json(*args, **compat_kwargs(kwargs))
            except ExtractorError as e:
                if isinstance(e.cause, compat_HTTPError) and e.cause.code == 401:
                    self._store_client_id(None)
                    self._update_client_id()
                    continue
                elif non_fatal:
                    self._downloader.report_warning(error_to_compat_str(e))
                    return False
                raise

    def _real_initialize(self):
        self._CLIENT_ID = self._downloader.cache.load('soundcloud', 'client_id') or 'YUKXoArFcqrlQn9tfNHvvyfnDISj04zk'

    @classmethod
    def _resolv_url(cls, url):
        return CustomSoundcloudIE._API_V2_BASE + 'resolve?url=' + url

    def _extract_info_dict(self, info, full_title=None, secret_token=None):
        track_id = compat_str(info['id'])
        title = info['title']

        publishedAt = info.get('created_at') or info.get('last_modified') or info.get('display_date') or ''
        publishedAt = publishedAt.split('T')[0]
        format_urls = set()
        formats = []
        query = {'client_id': self._CLIENT_ID}
        if secret_token:
            query['secret_token'] = secret_token

        if info.get('downloadable') and info.get('has_downloads_left'):
            download_url = update_url_query(
                self._API_V2_BASE + 'tracks/' + track_id + '/download', query)
            redirect_url = (self._download_json(download_url, track_id, fatal=False) or {}).get('redirectUri')
            if redirect_url:
                urlh = self._request_webpage(
                    HEADRequest(redirect_url), track_id, fatal=False)
                if urlh:
                    format_url = urlh.geturl()
                    format_urls.add(format_url)
                    formats.append({
                        'format_id': 'download',
                        'ext': urlhandle_detect_ext(urlh) or 'mp3',
                        'filesize': int_or_none(urlh.headers.get('Content-Length')),
                        'url': format_url,
                        'preference': 10,
                    })

        def invalid_url(url):
            return not url or url in format_urls

        def add_format(f, protocol, is_preview=False):
            mobj = re.search(r'\.(?P<abr>\d+)\.(?P<ext>[0-9a-z]{3,4})(?=[/?])', stream_url)
            if mobj:
                for k, v in mobj.groupdict().items():
                    if not f.get(k):
                        f[k] = v
            format_id_list = []
            if protocol:
                format_id_list.append(protocol)
            for k in ('ext', 'abr'):
                v = f.get(k)
                if v:
                    format_id_list.append(v)
            preview = is_preview or re.search(r'/(?:preview|playlist)/0/30/', f['url'])
            if preview:
                format_id_list.append('preview')
            abr = f.get('abr')
            if abr:
                f['abr'] = int(abr)
            f.update({
                'format_id': '_'.join(format_id_list),
                'protocol': 'm3u8_native' if protocol == 'hls' else 'http',
                'preference': -10 if preview else None,
            })
            formats.append(f)

        # New API
        transcodings = try_get(
            info, lambda x: x['media']['transcodings'], list) or []
        for t in transcodings:
            if not isinstance(t, dict):
                continue
            format_url = url_or_none(t.get('url'))
            if not format_url:
                continue
            stream = self._download_json(
                format_url, track_id, query=query, fatal=False)
            if not isinstance(stream, dict):
                continue
            stream_url = url_or_none(stream.get('url'))
            if invalid_url(stream_url):
                continue
            format_urls.add(stream_url)
            stream_format = t.get('format') or {}
            protocol = stream_format.get('protocol')
            if protocol != 'hls' and '/hls' in format_url:
                protocol = 'hls'
            ext = None
            preset = str_or_none(t.get('preset'))
            if preset:
                ext = preset.split('_')[0]
            if ext not in KNOWN_EXTENSIONS:
                ext = mimetype2ext(stream_format.get('mime_type'))
            add_format({
                'url': stream_url,
                'ext': ext,
            }, 'http' if protocol == 'progressive' else protocol,
                t.get('snipped') or '/preview/' in format_url)

        for f in formats:
            f['vcodec'] = 'none'

        if not formats and info.get('policy') == 'BLOCK':
            self.raise_geo_restricted()
        self._sort_formats(formats)

        user = info.get('user') or {}

        thumbnails = []
        artwork_url = info.get('artwork_url')
        thumbnail = artwork_url or user.get('avatar_url')
        if isinstance(thumbnail, compat_str):
            if re.search(self._IMAGE_REPL_RE, thumbnail):
                for image_id, size in self._ARTWORK_MAP.items():
                    i = {
                        'id': image_id,
                        'url': re.sub(self._IMAGE_REPL_RE, '-%s.jpg' % image_id, thumbnail),
                    }
                    if image_id == 'tiny' and not artwork_url:
                        size = 18
                    elif image_id == 'original':
                        i['preference'] = 10
                    if size:
                        i.update({
                            'width': size,
                            'height': size,
                        })
                    thumbnails.append(i)
            else:
                thumbnails = [{'url': thumbnail}]

        def extract_count(key):
            return int_or_none(info.get('%s_count' % key))

        player = '<iframe width="100%" height="100%" scrolling="no"'\
                 ' frameborder="no" allow="autoplay"'\
                 ' src="https://w.soundcloud.com/player/?'\
                 'url=https%3A//api.soundcloud.com/tracks/{0}'\
                 '&color=%23ff5500&auto_play=false&'\
                 'hide_related=false&show_comments=true&'\
                 'show_user=true&show_reposts=false&'\
                 'show_teaser=true&visual=true"></iframe>'.format(track_id)

        return {
            'id': track_id,
            'uploader': user.get('username'),
            'uploader_id': str_or_none(user.get('id')) or user.get('permalink'),
            'uploader_url': user.get('permalink_url'),
            'player': player,
            'publishedAt': publishedAt,
            'title': title,
            'description': info.get('description'),
            'thumbnails': thumbnails,
            'duration': float_or_none(info.get('duration'), 1000),
            'webpage_url': info.get('permalink_url'),
            'license': info.get('license'),
            'view_count': extract_count('playback'),
            'like_count': extract_count('favoritings') or extract_count('likes'),
            'comment_count': extract_count('comment'),
            'repost_count': extract_count('reposts'),
            'genre': info.get('genre'),
            'formats': formats
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        track_id = mobj.group('track_id')

        query = {}
        if track_id:
            info_json_url = self._API_V2_BASE + 'tracks/' + track_id
            full_title = track_id
            token = mobj.group('secret_token')
            if token:
                query['secret_token'] = token
        else:
            full_title = resolve_title = '%s/%s' % mobj.group('uploader',
                                                              'title')
            token = mobj.group('token')
            if token:
                resolve_title += '/%s' % token

            info_json_url = self._resolv_url(self._BASE_URL + resolve_title)
        # else:
        #     mobj = re.match(self._VALID_URL2, url)
        #     token = None
        #     full_title = resolve_title = '%s/sets/%s' % mobj.group('uploader', 'title')
        #     info_json_url = self._resolv_url(self._BASE_URL + resolve_title)
        #     query = {}
        info = self._download_json(
            info_json_url, full_title, 'Downloading info JSON', query=query)

        return self._extract_info_dict(info, full_title, token)


class CustomSoundcloudSearchIE(SearchInfoExtractor, CustomSoundcloudIE):
    '''https://www.soundcloud.com/search?q=hello
       https://soundcloud.com/search/sounds?q=hello'''
    _VALID_URL1 = r'https?://(?:www\.|m\.)?soundcloud\.com/search\?(.*?&)?(?:q)=(?P<query>[^&]+)(?:[&]|$)'
    _VALID_URL2 = r'https?://(?:www\.|m\.)?soundcloud\.com/search\?(.*?&)?(?:q)=(?P<query>[^&]+)(?:[&]|$)(?:page)=(?P<page>[^&]+)'
    IE_NAME = 'custom soundcloud:search'
    IE_DESC = 'custom Soundcloud search'
    _MAX_RESULTS = float('inf')
    _TESTS = [{
        'url': 'scsearch15:post-avant jazzcore',
        'info_dict': {
            'title': 'post-avant jazzcore',
        },
        'playlist_count': 15,
    }]

    _SEARCH_KEY = 'custom scsearch'
    _MAX_PAGE = 10
    _MAX_RESULTS_PER_PAGE = 50
    _DEFAULT_RESULTS_PER_PAGE = 20

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or re.match(cls._VALID_URL2, url) is not None
        return rs

    # Methods for following #608
    @staticmethod
    def url_result(info):
        """Returns a URL that points to a page that should be processed"""
        # TODO: ie should be the class used for getting the info
        info.pop('uri')
        video_info = {'_type': 'url',
                      'url': info["permalink_url"],
                      'ie_key': CustomSoundcloudSearchIE.ie_key()}
        video_info.update(info)
        return video_info

    def _real_extract(self, query):
        if 'page=' in query:
            mobj = re.match(self._VALID_URL2, query)
        else:
            mobj = re.match(self._VALID_URL1, query)
        if mobj is None:
            raise ExtractorError('Invalid search query "%s"' % query)
        try:
            page = int(mobj.group('page'))
        except IndexError as _:
            page = 1
        if page >= self._MAX_PAGE:
            page = self._MAX_PAGE
        query = mobj.group('query')
        return self._get_page_results(query, page)

    def _get_collection(self, endpoint, collection_id, **query):
        limit = min(
            query.get('limit', self._DEFAULT_RESULTS_PER_PAGE),
            self._MAX_RESULTS_PER_PAGE)
        page = query.get('page')
        query.update({
            'limit': limit,
            'linked_partitioning': 1,
            'offset': (page - 1) * limit,
        })
        next_url = update_url_query(self._API_V2_BASE + endpoint, query)

        response = self._download_json(
            next_url, collection_id, 'Downloading page {0}'.format(page),
            'Unable to download API page')

        collection = response.get('collection', [])
        if not collection:
            return

        collection = list(filter(bool, collection))

        collection = list(map(self.url_result, collection))
        is_next_page = len(collection) == 20
        if is_next_page:
            next_page = f'https://soundcloud.com/search?q={query["q"]}&page={page + 1}'
        else:
            next_page = None
        ie_result = self.playlist_result(collection, query['q'])
        ie_result.update({'is_next_page': is_next_page, 'next_page': next_page})
        # print(json.dumps(ie_result))
        return ie_result

    def _get_page_results(self, query, page):
        return self._get_collection('search/tracks', query, page=page, q=query)


class CustomSoundcloudPlaylistBaseIE(CustomSoundcloudIE):
    def _extract_set(self, playlist, token=None):
        playlist_id = compat_str(playlist['id'])
        tracks = playlist.get('tracks') or []
        if not all([t.get('permalink_url') for t in tracks]) and not token:
            tracks = self._download_json(
                self._API_V2_BASE + 'tracks', playlist_id,
                'Downloading tracks', query={
                    'ids': ','.join([compat_str(t['id']) for t in tracks]),
                    'playlistId': playlist_id,
                    'playlistSecretToken': token,
                })
        entries = []
        for track in tracks:
            track_id = str_or_none(track.get('id'))
            url = track.get('permalink_url')
            if not url:
                if not track_id:
                    continue
                url = self._API_V2_BASE + 'tracks/' + track_id
                if token:
                    url += '?secret_token=' + token
            info = dict()
            info['id'] = track_id
            info['url'] = url
            info['title'] = track.get('title', '')
            info['artwork_url'] = track.get('artwork_url') or playlist['artwork_url']
            info['playback_count'] = track.get('playback_count', '')
            info['duration'] = track.get('duration', 0)
            info['description'] = track.get('description') or track.get('tag_list', '')
            info['created_at'] = track.get('created_at', '')
            entries.append(info)
        ie_result = self.playlist_result(
            entries, playlist_id,
            playlist.get('title'),
            playlist.get('description'))
        ie_result.update({'is_next_page': False})
        # print(json.dumps(ie_result))
        return ie_result


class CustomSoundcloudSetIE(CustomSoundcloudPlaylistBaseIE):
    _VALID_URL = r'https?://(?:(?:www|m)\.)?soundcloud\.com/(?P<uploader>[\w\d-]+)/sets/(?P<slug_title>[\w\d-]+)(?:/(?P<token>[^?/]+))?'
    IE_NAME = 'custom soundcloud:set'
    _TESTS = [{
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep',
        'info_dict': {
            'id': '2284613',
            'title': 'The Royal Concept EP',
            'description': 'md5:71d07087c7a449e8941a70a29e34671e',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/the-concept-band/sets/the-royal-concept-ep/token',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)

        full_title = '%s/sets/%s' % mobj.group('uploader', 'slug_title')
        token = mobj.group('token')
        if token:
            full_title += '/' + token

        info = self._download_json(self._resolv_url(
            self._BASE_URL + full_title), full_title)

        if 'errors' in info:
            msgs = (compat_str(err['error_message']) for err in info['errors'])
            raise ExtractorError('unable to download video webpage: %s' % ','.join(msgs))

        return self._extract_set(info, token)


class CustomSoundcloudPagedPlaylistBaseIE(CustomSoundcloudIE):
    def _extract_playlist(self, base_url, playlist_id, playlist_title):
        COMMON_QUERY = {
            'limit': 80000,
            'linked_partitioning': '1',
        }

        query = COMMON_QUERY.copy()
        query['offset'] = 0

        next_href = base_url

        entries = []
        for i in itertools.count():
            response = self._download_json(
                next_href, playlist_id,
                'Downloading track page %s' % (i + 1), query=query)

            collection = response['collection']

            # if '/playlist' in next_href:
            #     tracks = collection[0]['tracks']
            #     ids = ','.join([track['id'] for track in tracks])
            #     dt = {'ids': ids, 'client_id': self.client_id}

            if not isinstance(collection, list):
                collection = []

            # Empty collection may be returned, in this case we proceed
            # straight to next_href

            def custom_url_result(url, cand):
                video_info = {}
                video_info.update({'_type': 'url', 'url': url, 'ie_key': CustomSoundcloudIE.ie_key()})
                video_info['id'] = cand['id']
                video_info['title'] = cand['title']
                video_info['created_at'] = cand.get('created_at', '').split('T')[0]
                video_info['artwork_url'] = cand['artwork_url']
                video_info['description'] = cand.get('description')
                video_info['url'] = cand['permalink_url']
                video_info['duration'] = cand.get('duration')
                video_info['playback_count'] = cand.get('playback_count')

                return video_info

            def resolve_entry(candidates):
                for cand in candidates:
                    if not isinstance(cand, dict):
                        continue
                    permalink_url = url_or_none(cand.get('permalink_url'))
                    if not permalink_url:
                        continue
                    if cand.get('kind') != 'playlist':
                        return custom_url_result(permalink_url, cand)
                    else:
                        infos = []
                        inner_cand = cand['tracks']
                        for c in inner_cand:
                            inner_permalink_url = url_or_none(c.get('permalink_url'))
                            if not inner_permalink_url:
                                continue
                            info = custom_url_result(inner_permalink_url, c)
                            infos.append(info)
                        return infos

            for e in collection:
                entry = resolve_entry((e, e.get('track'), e.get('playlist')))
                if entry:
                    if isinstance(entry, dict):
                        entries.append(entry)
                    elif isinstance(entry, list):
                        entries.extend(entry)

            break
            # next_href = response.get('next_href')
            # if not next_href:
            #     break

            # next_href = response['next_href']
            # parsed_next_href = compat_urlparse.urlparse(next_href)
            # query = compat_urlparse.parse_qs(parsed_next_href.query)
            # query.update(COMMON_QUERY)

        return {
            '_type': 'playlist',
            'id': playlist_id,
            'title': playlist_title,
            'entries': entries,
            'is_next_page': False
        }


class CustomSoundcloudUserIE(CustomSoundcloudPagedPlaylistBaseIE):
    _VALID_URL = r'''(?x)
                        https?://
                            (?:(?:www|m)\.)?soundcloud\.com/
                            (?P<user>[^/]+)
                            (?:/
                                (?P<rsrc>tracks|albums|sets|reposts|likes|spotlight|popular-tracks)
                            )?
                            /?(?:[?#].*)?$
                    '''
    IE_NAME = 'custom soundcloud:user'
    _TESTS = [{
        'url': 'https://soundcloud.com/soft-cell-official',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (All)',
        },
        'playlist_mincount': 28,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/tracks',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Tracks)',
        },
        'playlist_mincount': 27,
    }, {
        'url': 'https://soundcloud.com/soft-cell-official/albums',
        'info_dict': {
            'id': '207965082',
            'title': 'Soft Cell (Albums)',
        },
        'playlist_mincount': 1,
    }, {
        'url': 'https://soundcloud.com/jcv246/sets',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Sets)',
        },
        'playlist_mincount': 2,
    }, {
        'url': 'https://soundcloud.com/jcv246/reposts',
        'info_dict': {
            'id': '12982173',
            'title': 'Jordi / cv (Reposts)',
        },
        'playlist_mincount': 6,
    }, {
        'url': 'https://soundcloud.com/clalberg/likes',
        'info_dict': {
            'id': '11817582',
            'title': 'clalberg (Likes)',
        },
        'playlist_mincount': 5,
    }, {
        'url': 'https://soundcloud.com/grynpyret/spotlight',
        'info_dict': {
            'id': '7098329',
            'title': 'Grynpyret (Spotlight)',
        },
        'playlist_mincount': 1,
    }]

    _BASE_URL_MAP = {
        'all': 'stream/users/%s',
        'tracks': 'users/%s/tracks',
        'albums': 'users/%s/albums',
        'sets': 'users/%s/playlists',
        'reposts': 'stream/users/%s/reposts',
        'likes': 'users/%s/likes',
        'spotlight': 'users/%s/spotlight',
        'popular-tracks': 'users/%s/toptracks'
    }

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url)
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        uploader = mobj.group('user')

        user = self._download_json(
            self._resolv_url(self._BASE_URL + uploader),
            uploader, 'Downloading user info')

        resource = mobj.group('rsrc') or 'all'

        return self._extract_playlist(
            self._API_V2_BASE + self._BASE_URL_MAP[resource] % user['id'],
            str_or_none(user.get('id')),
            '%s (%s)' % (user['username'], resource.capitalize()))
