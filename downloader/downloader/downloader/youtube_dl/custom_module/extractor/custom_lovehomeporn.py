from __future__ import unicode_literals

import re

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    float_or_none,
    xpath_text
)


class CustomLoveHomePornIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.)?lovehomeporn\.com/video/(?P<id>\d+)(?:/(?P<display_id>[^/?#&]+))?'
    _TEST = {
        'url': 'http://lovehomeporn.com/video/48483/stunning-busty-brunette-girlfriend-sucking-and-riding-a-big-dick#menu',
        'info_dict': {
            'id': '48483',
            'display_id': 'stunning-busty-brunette-girlfriend-sucking-and-riding-a-big-dick',
            'ext': 'mp4',
            'title': 'Stunning busty brunette girlfriend sucking and riding a big dick',
            'age_limit': 18,
            'duration': 238.47,
        },
        'params': {
            'skip_download': True,
        }
    }

    def _extract_nuevo(self, config_url, web_url, video_id, headers={}):
        config = self._download_xml(
            config_url, video_id, transform_source=lambda s: s.strip(),
            headers=headers)
        webpage = self._download_webpage(web_url, video_id)

        title = xpath_text(config, './title', 'title', fatal=True).strip()
        description = self._html_search_meta('description', webpage, 'description')
        view_count = re.search(r'<span itemprop="interactionCount">(.*?) views</span>',
                               webpage, re.S)
        if view_count:
            view_count = int(view_count.group(1).strip())
        else:
            view_count = ''
        publishedAt = re.search(
            r'''<i class="icon-calendar"></i>(.*?)</span>''',
            webpage, re.S
        )
        if publishedAt:
            publishedAt = publishedAt.group(1).replace('<span>', '').strip()
        else:
            publishedAt = ''
        video_id = xpath_text(config, './mediaid', default=video_id)
        thumbnail = xpath_text(config, ['./image', './thumb'])
        duration = float_or_none(xpath_text(config, './duration'))

        formats = []
        for element_name, format_id in (('file', 'sd'), ('filehd', 'hd')):
            video_url = xpath_text(config, element_name)
            if video_url:
                formats.append({
                    'url': video_url,
                    'format_id': format_id,
                    'height': 480 if format_id == 'sd' else 720
                })
        self._check_formats(formats, video_id)

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'thumbnail': thumbnail,
            'duration': duration,
            'formats': formats
        }

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')
        display_id = mobj.group('display_id')

        info = self._extract_nuevo(
            'http://lovehomeporn.com/media/nuevo/config.php?key=%s' % video_id,
            url,
            video_id)
        info.update({
            'display_id': display_id,
            'age_limit': 18
        })
        return info
