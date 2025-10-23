from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
    ExtractorError
)


class Custom9AnimeIE(InfoExtractor):
    IE_NAME = 'custom 9anime'
    _VALID_URL = r'https?://(?:www(?:\d+)?\.)?9anime\.(?:to|ru|video|page|life|live|one|love|app|at|zone)/watch/(?P<name>[^\.]+)\.(?P<id>[^\/]+)/?(?P<mid>[^/]+)?'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def _real_extract(self, url):
        video_id = self._match_id(url)

        mobj = re.match(self._VALID_URL, url)
        try:
            mid = mobj.group('mid')
            if not mid:
                raise IndexError('not found mid')
        except IndexError:
            mid = '01'

        webpage = self._download_webpage(url, video_id)

        title = self._html_search_regex(r'<title>(.*?)</title>', webpage, 'title')
        description = self._html_search_regex(r'<div class="desc">(.*?)</div>', webpage, 'description', default='') or\
                      self._html_search_meta(r'description', webpage, 'description')
        view_count = parse_count(self._html_search_regex(r'<div>Views: <span><span class="quality">(.*?)</span></div>', webpage, 'view_count', default=''))
        thumbnail = self._html_search_meta(r'og:image', webpage, 'og:image')
        duration = self._html_search_regex(r'<div>Duration: <span>(.*?)</span> </div>', webpage, 'duration')
        publishedAt = self._html_search_regex(r'<div>Date aired: <span>(.*?)</span> </div>', webpage, 'publishedAt')

        info_json_data = self._download_json(f'https://9anime.to/ajax/film/servers?id={video_id}', video_id)
        html = info_json_data['html']
        mp4upload_html = html.split('data-id="35">')[-1]
        if html:
            if mid == '01':
                data_id = re.findall('data-id="(.*?)"', mp4upload_html)[0]
            else:
                num_str = re.findall(rf'{mid}">(.*?)</a>', html, re.S)[0]
                data_str = re.findall(rf'<a.*?>{num_str}</a>', mp4upload_html, re.S)[0]
                data_id = re.findall('data-id="(.*?)"', data_str, re.S)[-1]
            get_iframe_url = f'https://9anime.to/ajax/episode/info?id={data_id}'
            iframe_json_data = self._download_json(get_iframe_url, data_id)
            iframe_url = iframe_json_data['target']
            sub_title = iframe_json_data['name']
            title = f'{title} {sub_title}'
            download_web_page = self._download_webpage(iframe_url, sub_title)
            info_str = re.findall(r'document\|player\|(.*?)title\|source', download_web_page)
            if info_str:
                info_str = info_str[0]
            else:
                raise ExtractorError(f'a wrong happen, the webpage content is {download_web_page}')
            data = info_str.split('|')
            video_url = f'https://{data[3]}.mp4upload.com:{data[32]}/d/{data[31]}/video.mp4'
            height = int(data[5])
            video_info = {
                'url': video_url,
                'format_id': '%dp' % height,
                'height': height,
                'ext': 'mp4'
            }
            formats = [video_info]
            player = '<video controls="" autoplay="" name="media" ' \
                     'width="100%" height="100%">' \
                     '<source src="{}" type="video/mp4"></video>'.format(video_url)
            info = {
                'title': title,
                'description': description,
                'view_count': view_count,
                'thumbnail': thumbnail,
                'duration': duration,
                'publishedAt': publishedAt,
                'player': player,
                'formats': formats
            }
            print(json.dumps(info))
        else:
            raise
