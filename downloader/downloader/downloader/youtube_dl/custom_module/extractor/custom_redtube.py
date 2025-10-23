from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    get_element_by_id,
    get_elements_by_class,
    determine_ext,
    ExtractorError,
    int_or_none,
    merge_dicts,
    str_to_int,
    url_or_none,
)


class CustomRedTubeIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:[^/]+\.)?redtube\.com/|embed\.redtube\.com/\?.*?\bid=)(?P<id>[0-9]+)'
    _TESTS = [{
        'url': 'http://www.redtube.com/66418',
        'md5': 'fc08071233725f26b8f014dba9590005',
        'info_dict': {
            'id': '66418',
            'ext': 'mp4',
            'title': 'Sucked on a toilet',
            'upload_date': '20110811',
            'duration': 596,
            'view_count': int,
            'age_limit': 18,
        }
    }, {
        'url': 'http://embed.redtube.com/?bgcolor=000000&id=1443286',
        'only_matching': True,
    }]

    @staticmethod
    def _extract_urls(webpage):
        return re.findall(
            r'<iframe[^>]+?src=["\'](?P<url>(?:https?:)?//embed\.redtube\.com/\?.*?\bid=\d+)',
            webpage)

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(
            'http://www.redtube.com/%s' % video_id, video_id)

        ERRORS = (
            (('video-deleted-info', '>This video has been removed'), 'has been removed'),
            (('private_video_text', '>This video is private', '>Send a friend request to its owner to be able to view it'), 'is private'),
        )

        for patterns, message in ERRORS:
            if any(p in webpage for p in patterns):
                raise ExtractorError(
                    'Video %s %s' % (video_id, message), expected=True)

        info = self._search_json_ld(webpage, video_id, default={})

        if not info.get('title'):
            info['title'] = self._html_search_regex(
                (r'<h(\d)[^>]+class="(?:video_title_text|videoTitle|video_title)[^"]*">(?P<title>(?:(?!\1).)+)</h\1>',
                 r'(?:videoTitle|title)\s*:\s*(["\'])(?P<title>(?:(?!\1).)+)\1',),
                webpage, 'title', group='title',
                default=None) or self._og_search_title(webpage)

        formats = []
        sources = self._parse_json(
            self._search_regex(
                r'sources\s*:\s*({.+?})', webpage, 'source', default='{}'),
            video_id, fatal=False)
        if sources and isinstance(sources, dict):
            for format_id, format_url in sources.items():
                if format_url:
                    formats.append({
                        'url': format_url,
                        'format_id': format_id,
                        'height': int_or_none(format_id),
                    })
        medias = self._parse_json(
            self._search_regex(
                r'mediaDefinition["\']?\s*:\s*(\[.+?}\s*\])', webpage,
                'media definitions', default='{}'),
            video_id, fatal=False)
        if medias and isinstance(medias, list):
            for media in medias:
                format_url = url_or_none(media.get('videoUrl'))
                if not format_url:
                    continue
                if media.get('format') == 'hls' or determine_ext(format_url) == 'm3u8':
                    # formats.extend(self._extract_m3u8_formats(
                    #     format_url, video_id, 'mp4',
                    #     entry_protocol='m3u8_native', m3u8_id='hls',
                    #     fatal=False))
                    continue
                sources = self._download_json(
                    format_url, video_id, 'Downloading API',
                    'Unable to download API page')
                for source in sources:
                    format_id = source.get('quality')
                    formats.append({
                        'url': source['videoUrl'],
                        'format_id': format_id,
                        'height': int_or_none(format_id),
                    })
        if not formats:
            video_url = self._html_search_regex(
                r'<source src="(.+?)" type="video/mp4">', webpage, 'video URL')
            formats.append({'url': video_url})
        self._sort_formats(formats)

        thumbnail = self._og_search_thumbnail(webpage)
        # upload_date = unified_strdate(self._search_regex(
        #     r'<span[^>]+>(?:ADDED|Published on) ([^<]+)<',
        #     webpage, 'upload date', default=None))
        duration = int_or_none(self._og_search_property(
            'video:duration', webpage, default=None) or self._search_regex(
                r'videoDuration\s*:\s*(\d+)', webpage, 'duration', default=None))
        view_count = str_to_int(self._search_regex(
            (r'<div[^>]*>Views</div>\s*<div[^>]*>\s*([\d,.]+)',
             r'<span[^>]*>VIEWS</span>\s*</td>\s*<td>\s*([\d,.]+)',
             r'<span[^>]+\bclass=["\']video_view_count[^>]*>\s*([\d,.]+)'),
            webpage, 'view count', default=None))
        upload_date = self._html_search_regex(
            r'''<span class="video-infobox-date-added">Published on (.*?)</span>''',
            webpage,
            'upload date'
        )

        # No self-labeling, but they describe themselves as
        # "Home of Videos Porno"
        age_limit = 18

        return merge_dicts(info, {
            'id': video_id,
            'ext': 'mp4',
            'thumbnail': thumbnail,
            'publishedAt': upload_date,
            'duration': duration,
            'view_count': view_count,
            'age_limit': age_limit,
            'formats': formats,
        })


class CustomRedTubeSearchIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?redtube\.com/(?:new|top|mostviewed|longest)?\?(.*?&)?search=(?P<query>[^&]+)(?:[&]|$)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)

        items = re.findall(
            r'<li id="tags_videos_.*?</li>',
            webpage, re.S
        )

        if not items:
            raise

        entries = []
        for item in items:
            vid = self._search_regex(
                r'''id="tags_videos_(.*?)"''', item,
                'vid'
            )
            title = self._search_regex(
                r'''alt="(.*?)"''', item,
                'title'
            )
            thumbnail = self._search_regex(
                r'''data-src="(.*?)"''',
                item,
                'thumbnail'
            )
            publishedAt = ''

            description = re.search(
                r'''<span class="badge-tooltip">(.*?)</span>''',
                item, re.S
            )
            if description:
                description = description.group(1).strip()
            else:
                description = ''
            item_url = 'https://www.redtube.com/{}'.format(vid)

            duration = re.search(
                r'''<span class="duration">(.*?)</span>''',
                item,
                re.S
            )
            if duration:
                duration = duration.group(1).strip()
            else:
                duration = ''
            view_count = str_to_int(self._search_regex(
                r'''<span class="video_count">(.*?)views</span>''',
                item,
                'view count',
                default=''
            ))
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
        # is_next_page = '<a id="wp_navNext"' in webpage
        is_next_page = False
        if is_next_page:
            next_page_str = re.search(
                r'<a id="wp_navNext" class="js_pop_page tm_pag_nav_next" href="(.*?)">',
                webpage,
                re.S
            ).group(1).replace('amp;', '')
            ie_result.update(
                {'next_page': 'https://www.redtube.com{}'.format(next_page_str)})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
