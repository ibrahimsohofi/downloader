#!/usr/bin/env python
# coding: utf-8

from __future__ import unicode_literals

import re
import json
try:
    # python3
    from functools import reduce
    from urllib.parse import unquote
except ImportError as ime:
    # python2
    from urllib import unquote
    pass
from youtube_dl.extractor.common import InfoExtractor, SearchInfoExtractor
from youtube_dl.utils import (
    ExtractorError
)
from youtube_dl.compat import compat_urllib_parse_urlencode


class CustomArchiveOrgIE(InfoExtractor):
    IE_NAME = 'custom archive.org'
    IE_DESC = 'custom archive.org videos'
    _VALID_URL = r'https?://(?:www\.)?archive\.org/(?:details|embed)/(?P<id>[^/?#]+)/?(?P<file_name>[^/]+)?'
    _TESTS = [{
        'url': 'http://archive.org/details/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'md5': '8af1d4cf447933ed3c7f4871162602db',
        'info_dict': {
            'id': 'XD300-23_68HighlightsAResearchCntAugHumanIntellect',
            'ext': 'ogg',
            'title': '1968 Demo - FJCC Conference Presentation Reel #1',
            'description': 'md5:da45c349df039f1cc8075268eb1b5c25',
            'upload_date': '19681210',
            'uploader': 'SRI International'
        }
    }, {
        'url': 'https://archive.org/details/Cops1922',
        'md5': '0869000b4ce265e8ca62738b336b268a',
        'info_dict': {
            'id': 'Cops1922',
            'ext': 'mp4',
            'title': 'Buster Keaton\'s "Cops" (1922)',
            'description': 'md5:89e7c77bf5d965dd5c0372cfb49470f6',
        }
    }, {
        'url': 'http://archive.org/embed/XD300-23_68HighlightsAResearchCntAugHumanIntellect',
        'only_matching': True,
    }]

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        video_id = self._match_id(url)
        info = {}
        response = self._download_json(
            'http://archive.org/details/' + video_id, video_id, query={
                'output': 'json',
            })
        info['id'] = video_id
        info['title'] = response['metadata']['title'][0]
        info['thumbnail'] = response['misc']['image']
        info['view_count'] = ''
        collection_title = response['metadata']['mediatype'][0]
        files = response['files']
        condition_str = '.mp3' if collection_title in ('audio', 'etree') else '.mp4'
        items = [(k, v) for k, v in files.items() if k.endswith(condition_str)]
        if items[0][1].get('private', '') == 'true':
            raise ExtractorError('It`s Private Item, Can Not Download!')
        server_name = response['server']
        dir_name = response['dir']
        for (k, v) in items:
            v['file_name'] = k
            v['download_url'] = 'https://{}{}{}'.format(server_name, dir_name, k)
        items = [v for k, v in items]
        rs = re.match(self._VALID_URL, url)
        if 'file_name' in rs.groupdict() and rs.group('file_name'):
            file_name = rs.group('file_name')
            if file_name.endswith('.flac'):
                file_name = file_name.replace('.flac', '.mp3')
            file_name = f"/{file_name}"
            standby_items = [item for item in items if file_name == item['file_name']]
            if standby_items:
                items = standby_items
        if len(items) >= 1:
            formats = []
            for item in items:
                if condition_str == '.mp3':
                    format_item = {
                        'vcodec': 'none',
                        "protocol": "https",
                        "format": item['format'],
                        "url": unquote(item['download_url']),
                        "ext": "mp3",
                        "format_id": "",
                        "quality": 0,
                    }
                    formats.append(format_item)
                else:
                    format_item = {
                        'vcodec': 'hkd.av01',
                        "protocol": "https",
                        "format": item['format'],
                        "url": unquote(item['download_url']),
                        "ext": "mp4",
                        "format_id": "",
                        "quality": 0,
                        'filesize': int(item['size']),
                        'height': int(item['height']),
                        'width': int(item['width']),
                    }
                    formats.append(format_item)
            if 'MP3 Sample' in [x['format'] for x in items]:
                formats = [x for x in formats if x['format'] == 'MP3 Sample']
                duration = [x for x in items if x['format'] == 'MP3 Sample'][0]['length']
                if ':' in duration:
                    info['duration'] = duration
                else:
                    info['duration'] = int(float(duration))
            else:
                if ':' in items[0]['length']:
                    info['duration'] = items[0]['length']
                else:
                    info['duration'] = int(float(items[0]['length']))
        else:
            formats = []
            info['duration'] = ''
        info['formats'] = formats
        return info
        # print(json.dumps(info))


class CustomArchiveOrgSearchIE(SearchInfoExtractor, CustomArchiveOrgIE):
    IE_NAME = 'custom archive.org search'
    IE_DESC = 'custom archive.org search'
    # '''https://archive.org/search.php?query=hello&cate_id=1'''
    _VALID_URL1 = r'https?://(?:www\.)?archive\.org/search\.php\?(.*?&)?(?:query)=(?P<query>[^&]+)(?:[&]|$)(?:cate_id)=(?P<cate_id>\d+)(?:[&]|$)'
    _VALID_URL2 = r'https?://(?:www\.)?archive\.org/search\.php\?(.*?&)?(?:query)=(?P<query>[^&]+)(?:[&]|$)(?:cate_id)=(?P<cate_id>\d+)(?:[&]|$)(?:page)=(?P<page>[^&]+)'
    _SEARCH_KEY = 'custom archive.org search'
    _MAX_PAGE = 10
    _FIELD_PARAMS = '&fl[]=contributor&fl[]=coverage&fl[]=creator&fl[]=date' \
                    '&fl[]=description&fl[]=downloads&fl[]=genre' \
                    '&fl[]=identifier&fl[]=mediatype' \
                    '&fl[]=num_reviews&fl[]=publicdate&fl[]=source' \
                    '&fl[]=title'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL1, url) is not None or re.match(cls._VALID_URL2, url) is not None
        return rs

    # Methods for following #608
    @staticmethod
    def url_result(doc):
        """Returns a URL that points to a page that should be processed"""
        url = 'https://archive.org/details/{}'.format(doc["identifier"])
        doc['publicdate'] = re.sub(r'T|Z', ' ', doc['publicdate']).strip()
        doc['image'] = 'https://archive.org/services/img/{}'.format(doc["identifier"])
        doc['creator'] = doc.get('creator', '')
        doc['creator'] = ','.join(doc['creator']) if isinstance(doc['creator'], list) else doc['creator']
        video_info = {
            '_type': 'url',
            'url': url,
            'ie_key': CustomArchiveOrgSearchIE.ie_key()
        }
        video_info.update({
            'creator': doc['creator'],
            'description': doc.get('description', ''),
            'downloads': doc.get('downloads', '0'),
            'identifier': doc['identifier'],
            'image': doc['image'],
            'mediatype': doc['mediatype'],
            'publicdate': doc['publicdate'],
            'title': doc['title']
        })
        return video_info

    def _extract_videos(self, content):
        items_re = r'<div class="item-ia"(.*?)<!--/.item-ia-->'
        descs_re = r'<div class="details-ia hidden-tiles">(.*?)<div class="C5">'
        items = re.findall(items_re, content, re.S)
        descs = re.findall(descs_re, content, re.S)
        docs = [{} for _ in items]
        for doc, item, desc in zip(docs, items, descs):
            creator = re.search(r'<div class="by C C4">(.*?)</div>', item, re.S)
            if creator:
                creator = creator.group(1).strip()
                if creator:
                    creator = re.search(r'<span class="byv".*?title="(.*?)">', creator, re.S)
                    if creator:
                        doc['creator'] = creator.group(1).strip()
                    else:
                        doc['creator'] = ''
                else:
                    doc['creator'] = ''
            else:
                doc['creator'] = ''
            description = re.search(r'<span>(.*?)</span>', desc, re.S)
            if description:
                doc['description'] = description.group(1).strip()
            else:
                doc['description'] = ''
            downloads = re.search(r'<nobr class="hidden-xs">(.*？)</nobr>', item, re.S)
            if downloads:
                doc['downloads'] = downloads.group(1).replace(',', '')
            else:
                doc['downloads'] = '0'
            identifier = re.search(r'data-id="(.*?)"', item, re.S)
            if identifier:
                doc['identifier'] = identifier.group(1)
                if 'podcast_' in doc['identifier']:
                    continue
            else:
                raise ExtractorError("Can`t found identifier")
            doc['mediatype'] = 'movies'
            publicdate = re.search(r'<div class="hidden-tiles pubdate C C3">(.*?)</div>', item, re.S)
            if publicdate:
                publicdate = publicdate.group(1)
                year = re.search(
                    r'<nobr class="hidden-xs">(.*?)</nobr>',
                    publicdate,
                    re.S)
                year = year.group(1).split(',')[1].strip()
                mon_day = re.search(
                    r'<nobr class="hidden-sm hidden-md hidden-lg">(.*?)</nobr>',
                    publicdate,
                    re.S
                )
                mon_day = mon_day.group(1).replace('/', '-')
                doc['publicdate'] = '{}-{} 00:00:00'.format(year, mon_day)
            else:
                doc['publicdate'] = ''
            title = re.search(r'''<div class="ttl">(.*?)</div>''', item, re.S)
            if title:
                doc['title'] = title.group(1).strip()
            else:
                raise ExtractorError("Can`t found title")
            doc['image'] = "https://archive.org/services/img/{}".format(doc['identifier'])
            doc['url'] = "https://archive.org/details/{}".format(doc['identifier'])
            doc['_type'] = 'url'
            doc['ie_key'] = 'Archive.org'
        return docs

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
        if cate_id == 1:
            url = 'https://archive.org/search.php?query={}&page={}'.format(
                query, page
            )
            url += '&and[]=mediatype:"audio"'
            content = self._download_webpage(url, query)
            docs = self._extract_videos(content)
            if not docs:
                raise ExtractorError(
                    '[archive.org No doc results]', expected=True
                )
            is_next_page = len(docs) == 50
            docs = list(filter(lambda x: not x['identifier'].startswith('podcast_'), docs))
            docs = list(map(self.url_result, docs))
            for doc in docs:
                doc['mediatype'] = 'audio'
            ie_result = self.playlist_result(docs, query)
            # old
            # ie_result.update({'is_next_page': is_next_page})
            ie_result.update(
                {
                    'is_next_page': is_next_page,
                    'next_page': f'https://archive.org/search.php?query={query}&cate_id=1&page={page + 1}' if is_next_page else None
                }
            )
            return ie_result
            # url_query = {
            #     'q': query,
            #     'page': page,
            #     'rows': 500,
            #     'output': 'json'
            # }
            #
            # param_encode = '{}{}'.format(
            #     compat_urllib_parse_urlencode(url_query),
            #     self._FIELD_PARAMS
            # )
            #
            # result_url = 'https://archive.org/advancedsearch.php?{}'.format(param_encode)
            #
            # data = self._download_json(
            #     result_url, video_id='query "%s"' % query,
            #     note='Downloading page %s' % page,
            #     errnote='Unable to download API page',
            # )
            #
            # response = data.get('response', {})
            # docs = response.get('docs', [])
            # if not docs:
            #     raise ExtractorError(
            #         '[archive.org No doc results]', expected=True
            #     )
            #
            # is_next_page = len(docs) == 500
            # docs = list(filter(
            #     lambda x: x['mediatype'] == 'audio',
            #     map(self.url_result, docs)
            # ))
            # ie_result = self.playlist_result(docs, query)
            # ie_result['entries'] = list(
            #     filter(
            #         lambda x: not x['identifier'].startswith('podcast_'),
            #         ie_result['entries']
            #     )
            # )
            # ie_result.update({'is_next_page': is_next_page})
            # return ie_result
            # # print(json.dumps(ie_result))
            # # return self.playlist_result(docs, query)
        elif cate_id == 2:
            url = 'https://archive.org/search.php?query={}&page={}'.format(
                query, page
            )
            url += '&and[]=mediatype:"movies"'
            content = self._download_webpage(url, query)
            docs = self._extract_videos(content)
            if not docs:
                raise ExtractorError(
                    '[archive.org No doc results]', expected=True
                )
            is_next_page = len(docs) == 50
            docs = list(filter(lambda x: not x['identifier'].startswith('podcast_'), docs))
            docs = list(map(self.url_result, docs))
            for doc in docs:
                doc['mediatype'] = 'movie'
            ie_result = self.playlist_result(docs, query)
            # old
            ie_result.update({'is_next_page': is_next_page})
            ie_result.update(
                {
                    'is_next_page': is_next_page,
                    'next_page': f'https://archive.org/search.php?query={query}&cate_id=2&page={page + 1}' if is_next_page else None
                }
            )
            return ie_result
            # print(json.dumps(ie_result))
            # return self.playlist_result(docs, query)
        else:
            raise ExtractorError('cate_id must in range (1, 2)')
