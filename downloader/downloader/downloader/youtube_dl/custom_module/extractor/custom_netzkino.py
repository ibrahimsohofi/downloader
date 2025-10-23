# coding: utf-8
from __future__ import unicode_literals

import re
import datetime
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    clean_html,
    int_or_none,
    js_to_json,
    parse_iso8601,
)


class CustomNetzkinoIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?netzkino\.de/\#!/(?P<category>[^/]+)/(?P<id>[^/]+)'

    _TEST = {
        'url': 'http://www.netzkino.de/#!/scifikino/rakete-zum-mond',
        'md5': '92a3f8b76f8d7220acce5377ea5d4873',
        'info_dict': {
            'id': 'rakete-zum-mond',
            'ext': 'mp4',
            'title': 'Rakete zum Mond (Endstation Mond, Destination Moon)',
            'comments': 'mincount:3',
            'description': 'md5:1eddeacc7e62d5a25a2d1a7290c64a28',
            'upload_date': '20120813',
            'thumbnail': r're:https?://.*\.jpg$',
            'timestamp': 1344858571,
            'age_limit': 12,
        },
        'params': {
            'skip_download': 'Download only works from Germany',
        }
    }

    id_mapping = {

    }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        # category_id = mobj.group('category')
        video_id = mobj.group('id')

        search_api = f'https://api.netzkino.de.simplecache.net/capi-2.0a/search?q={video_id.replace("-", " ")}&d=www&l=de-DE&v=v1.1.1&sliderTypes[]=sliderDefaultVertical&sliderTypes[]=sliderDoubleRow&cnt=0&slug=suche&title=Suche&id=search&page=0&loading=0&ytAllowed=false'
        search_info = self._download_json(search_api, video_id)
        info = next(
            post for post in search_info['posts'] if post['slug'] == video_id)
        custom_fields = info['custom_fields']

        production_js = self._download_webpage(
            'http://www.netzkino.de/beta/dist/production.min.js', video_id,
            note='Downloading player code')
        avo_js = self._search_regex(
            r'var urlTemplate=(\{.*?"\})',
            production_js, 'URL templates')
        templates = self._parse_json(
            avo_js, video_id, transform_source=js_to_json)

        suffix = {
            'hds': '.mp4/manifest.f4m',
            'hls': '.mp4/master.m3u8',
            'pmd': '.mp4',
        }
        film_fn = custom_fields['Streaming'][0]
        formats = [{
            'format_id': key,
            'ext': 'mp4',
            'url': tpl.replace('{}', film_fn) + suffix[key],
        } for key, tpl in templates.items()]
        formats = list(f for f in formats if f['format_id'] == 'pmd')
        # self._sort_formats(formats)

        return {
            'id': video_id,
            'formats': formats,
            'title': info['title'],
            'age_limit': int_or_none(custom_fields.get('FSK')[0]),
            'publishedAt': info.get('date', ''),
            'description': clean_html(info.get('content')),
            'thumbnail': info.get('thumbnail')
        }
