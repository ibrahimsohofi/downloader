from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    # get_elements_by_class,
    get_element_by_id,
    int_or_none,
    sanitized_Request,
    str_to_int,
    unescapeHTML,
    parse_duration,
    url_or_none,
)
from youtube_dl.aes import aes_decrypt_text


class CustomYouPornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youporn\.com/watch/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        request = sanitized_Request(url)
        request.add_header('Cookie', 'age_verified=1')
        webpage = self._download_webpage(request, display_id)

        title = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']watchVideoTitle[^>]+>(.+?)</div>',
            webpage, 'title', default=None) or self._og_search_title(
            webpage, default=None) or self._html_search_meta(
            'title', webpage, fatal=True)

        links = []

        # Main source
        definitions = self._parse_json(
            self._search_regex(
                r'mediaDefinition\s*=\s*(\[.+?\]);', webpage,
                'media definitions', default='[]'),
            video_id, fatal=False)
        if definitions:
            for definition in definitions:
                if not isinstance(definition, dict):
                    continue
                video_url = url_or_none(definition.get('videoUrl'))
                if video_url:
                    links.append(video_url)

        # Fallback #1, this also contains extra low quality 180p format
        for _, link in re.findall(r'<a[^>]+href=(["\'])(http.+?)\1[^>]+title=["\']Download [Vv]ideo', webpage):
            links.append(link)

        # Fallback #2 (unavailable as at 22.06.2017)
        sources = self._search_regex(
            r'(?s)sources\s*:\s*({.+?})', webpage, 'sources', default=None)
        if sources:
            for _, link in re.findall(r'[^:]+\s*:\s*(["\'])(http.+?)\1', sources):
                links.append(link)

        # Fallback #3 (unavailable as at 22.06.2017)
        for _, link in re.findall(
                r'(?:videoSrc|videoIpadUrl|html5PlayerSrc)\s*[:=]\s*(["\'])(http.+?)\1', webpage):
            links.append(link)

        # Fallback #4, encrypted links (unavailable as at 22.06.2017)
        for _, encrypted_link in re.findall(
                r'encryptedQuality\d{3,4}URL\s*=\s*(["\'])([\da-zA-Z+/=]+)\1', webpage):
            links.append(aes_decrypt_text(encrypted_link, title, 32).decode('utf-8'))

        formats = []
        for video_url in set(unescapeHTML(link) for link in links):
            f = {
                'url': video_url,
            }
            # Video URL's path looks like this:
            #  /201012/17/505835/720p_1500k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            #  /201012/17/505835/vl_240p_240k_505835/YouPorn%20-%20Sex%20Ed%20Is%20It%20Safe%20To%20Masturbate%20Daily.mp4
            # We will benefit from it by extracting some metadata
            mobj = re.search(r'(?P<height>\d{3,4})[pP]_(?P<bitrate>\d+)[kK]_\d+/', video_url)
            if mobj:
                height = int(mobj.group('height'))
                bitrate = int(mobj.group('bitrate'))
                f.update({
                    'format_id': '%dp-%dk' % (height, bitrate),
                    'height': height,
                    'tbr': bitrate,
                })
            formats.append(f)
        self._sort_formats(formats)

        description = self._html_search_regex(
            r'(?s)<div[^>]+\bid=["\']description["\'][^>]*>(.+?)</div>',
            webpage, 'description',
            default=None) or self._og_search_description(
            webpage, default=None)
        thumbnail = self._search_regex(
            r'(?:imageurl\s*=|poster\s*:)\s*(["\'])(?P<thumbnail>.+?)\1',
            webpage, 'thumbnail', fatal=False, group='thumbnail')

        uploader = self._html_search_regex(
            r'(?s)<div[^>]+class=["\']submitByLink["\'][^>]*>(.+?)</div>',
            webpage, 'uploader', fatal=False)
        upload_date = self._html_search_regex(
            r'''<div class="video-uploaded">UPLOADED: <span>(.*?)</span></div>''',
            webpage,
            'upload date',
            fatal=False
        )
        duration = parse_duration(self._html_search_meta(
            'video:duration', webpage, 'duration'
        ))

        age_limit = self._rta_search(webpage)

        average_rating = int_or_none(self._search_regex(
            r'<div[^>]+class=["\']videoRatingPercentage["\'][^>]*>(\d+)%</div>',
            webpage, 'average rating', fatal=False))

        view_count = str_to_int(self._search_regex(
            r'(?s)<div[^>]+class=(["\']).*?\bvideoInfoViews\b.*?\1[^>]*>.*?(?P<count>[\d,.]+)<',
            webpage, 'view count', fatal=False, group='count'))
        comment_count = str_to_int(self._search_regex(
            r'>All [Cc]omments? \(([\d,.]+)\)',
            webpage, 'comment count', fatal=False))

        def extract_tag_box(regex, title):
            tag_box = self._search_regex(regex, webpage, title, default=None)
            if not tag_box:
                return []
            return re.findall(r'<a[^>]+href=[^>]+>([^<]+)', tag_box)

        categories = extract_tag_box(
            r'(?s)Categories:.*?</[^>]+>(.+?)</div>', 'categories')
        tags = extract_tag_box(
            r'(?s)Tags:.*?</div>\s*<div[^>]+class=["\']tagBoxContent["\'][^>]*>(.+?)</div>',
            'tags')

        return {
            'id': video_id,
            'display_id': display_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'uploader': uploader,
            'publishedAt': upload_date,
            'average_rating': average_rating,
            'view_count': view_count,
            'comment_count': comment_count,
            'categories': categories,
            'tags': tags,
            'age_limit': age_limit,
            'formats': formats,
            'player': '<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="{}"></iframe>'.format(
                url.replace('/watch/', '/embed/')),
        }


class CustomYouPornSearchIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?youporn\.com/search(?:/views|/rating|/duration|/date)?/\?(.*?&)?query=(?P<query>[^&]+)(?:[&]|$)'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        query_id = mobj.group('query')

        webpage = self._download_webpage(url, query_id)
        webpage = webpage.replace("'", '"')

        items_body = re.search(
            r'''<div class="searchResults full-row-thumbs row js_video_row">(.+?)<div class="js_pornstarsScrollable_row">''',
            webpage,
            re.S
        )
        if items_body:
            items_body = items_body.group(1)
        else:
            raise
        items = re.findall(
            r'''<div data-espnode="videobox"(.*?)<span class="add-to-button js_add-to-button"''',
            items_body,
            re.S
        )

        entries = []
        for item in items:
            vid = self._search_regex(
                r'''data-video-id="(.*?)"''', item, 'vid'
            )
            title = self._search_regex(
                r'''<div class="video-box-title" title="(.*?)">''', item, 'title'
            )
            thumbnail = self._search_regex(
                r'''data-thumbnail="(.*?)"''',
                item,
                'thumbnail'
            )
            date_arr = thumbnail.split('/')
            date_arr = list(filter(lambda x: len(x) in (2, 6) and x.isdigit(), date_arr))
            date_str = ''.join(date_arr)
            publishedAt = '{0}-{1}-{2}'.format(date_str[:4], date_str[4:6], date_str[6:8])

            description = ''
            display_id = re.findall(
                r'<a href="/watch/{}/(.*?)/"'.format(vid),
                item,
                re.S)[0]
            item_url = 'https://www.youporn.com/watch/{}/{}/'.format(
                vid, display_id)
            duration = self._search_regex(
                r'''<div class="video-duration">(.*?)</div>''',
                item,
                'duration'
            ) or ''
            view_count = str_to_int(self._search_regex(
                r'''<span class="video-box-views">(.*?) Views</span>''',
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
        is_next_page = 'aria-label="Next page"' in webpage
        if is_next_page:
            next_page_str = get_element_by_id('next', webpage)
            next_page_str = re.search(
                r'href="(.*?)"',
                next_page_str, re.S
            ).group(1).replace('amp;', '')
            ie_result.update(
                {'next_page': 'https://www.youporn.com{}'.format(
                    next_page_str)})
        ie_result.update({'is_next_page': is_next_page})
        # print(json.dumps(ie_result))
        return ie_result
