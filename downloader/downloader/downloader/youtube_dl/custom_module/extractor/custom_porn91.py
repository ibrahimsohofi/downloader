# coding: utf-8
from __future__ import unicode_literals

import re
from urllib import parse
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_duration,
    int_or_none,
    ExtractorError,
)


class CustomPorn91IE(InfoExtractor):
    IE_NAME = 'custom 91porn'
    _VALID_URL = r'(?:https?://)(?:www\.|)91porn\.com/.+?\?viewkey=(?P<id>[\w\d]+)'

    _TEST = {
        'url': 'http://91porn.com/view_video.php?viewkey=7e42283b4f5ab36da134',
        'md5': '7fcdb5349354f40d41689bd0fa8db05a',
        'info_dict': {
            'id': '7e42283b4f5ab36da134',
            'title': '18岁大一漂亮学妹，水嫩性感，再爽一次！',
            'ext': 'mp4',
            'duration': 431,
            'age_limit': 18,
        }
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._set_cookie('91porn.com', 'language', 'cn_CN')

        webpage = self._download_webpage(
            'http://91porn.com/view_video.php?viewkey=%s' % video_id, video_id)

        if '作为游客，你每天只可观看10个视频' in webpage:
            raise ExtractorError('91 Porn says: Daily limit 10 videos exceeded', expected=True)

        info_dict = {}
        title = self._search_regex(
            r'''<h4 class="login_register_header" align=left>([^<]+)</h4>''', webpage, 'title').strip()
        title = title.replace('\n', '')
        if not title:
            raise ExtractorError('Can`t found title, this page is empty, raise failure!', expected=True)

        description = self._html_search_meta('description', webpage)

        thumbnail = self._html_search_regex(
            r'poster="(.*?)"', webpage, 'thumbnail', default=''
        )

        duration = parse_duration(
            self._search_regex(
                r'时长: <span class="video-info-span">(\d+:\d+)</span>',
                # r'时长:\s*</span>\s*(\d+:\d+)',
                webpage,
                'duration',
                fatal=False
            )
        )

        view_count = parse_duration(
            self._search_regex(
                r'查看: <span class="video-info-span">(\d+) </span>',
                # r'时长:\s*</span>\s*(\d+:\d+)',
                webpage,
                'view count',
                fatal=False
            )
        )

        publishedAt = self._html_search_regex(
            r'''<span class="title-yakov">(.+?)</span>&nbsp;''',
            webpage,
            'publishedAt',
            default=''
        )

        strencode2 = self._html_search_regex(
            '''strencode2\("(.+?)"\)''',
            webpage,
            'strencode2', default=''
        )
        if not strencode2:
            raise ExtractorError('Can`t found video url!')
        else:
            source_tag = parse.unquote(strencode2)

        if '/m3u8' in source_tag:
            protocol = 'm3u8_native'
        else:
            protocol = 'https_native'
        video = re.search(r"src=\'(.*?)\'", source_tag, re.DOTALL)
        video_url = video.group(1)
        info_dict['formats'] = [
            {'url': video_url, 'ext': 'mp4', 'protocol': protocol}
        ]

        comment_count = int_or_none(self._search_regex(
            r'留言:\s*</span>\s*(\d+)', webpage, 'comment count', fatal=False))

        player = '<video controls="" autoplay="" name="media" ' \
                 'width="100%" height="100%">' \
                 '<source src="{}" type="video/mp4"></video>'.format(info_dict['formats'][0]['url'])

        info_dict.update({
            'id': video_id,
            'title': title,
            'description': description,
            'thumbnail': thumbnail,
            'duration': duration,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'comment_count': comment_count,
            'player': player,
            'age_limit': self._rta_search(webpage),
        })

        return info_dict
