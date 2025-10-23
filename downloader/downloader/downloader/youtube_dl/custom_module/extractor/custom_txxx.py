from __future__ import unicode_literals

import re
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    ExtractorError,
    urljoin
)


class CustomTxxxIE(InfoExtractor):
    _VALID_URL = r'https?://(?:www\.|m\.)?txxx\.(tube|com|net)/videos/(?P<id>\d+)/(?P<display_id>[^/?#&]+)'
    video_file_url = 'https://txxx.tube/api/videofile.php?video_id=%s&lifetime=8640000'
    detail_info_url = 'https://txxx.com/api/json/video/86400/%s/%s/%s.json'

    def b164_decode(self, encode_video_url):
        from youtube_dl.custom_module.site_packages import js2py

        js_str = '''
            function b164_func(e) {
                    var t = "АВСDЕFGHIJKLМNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,~"
                      , a = ""
                      , s = 0;
                    //[^АВСЕМA-Za-z0-9\.\,\~]/g.exec(e) && this.log("error decoding url"),
                    e = e.replace(/[^АВСЕМA-Za-z0-9\.\,\~]/g, "");
                    do {
                        var o = t.indexOf(e.charAt(s++))
                          , n = t.indexOf(e.charAt(s++))
                          , i = t.indexOf(e.charAt(s++))
                          , r = t.indexOf(e.charAt(s++));
                        o = o << 2 | n >> 4,
                        n = (15 & n) << 4 | i >> 2;
                        var l = (3 & i) << 6 | r;
                        a += String.fromCharCode(o),
                        64 != i && (a += String.fromCharCode(n)),
                        64 != r && (a += String.fromCharCode(l))
                    } while (s < e.length);
                    return unescape(a)
                }
        '''
        b164_func = js2py.eval_js(js_str)
        decode_video_url = b164_func(encode_video_url)
        decode_video_url = urljoin('https://txxx.tube', decode_video_url)
        return decode_video_url

    def _real_extract(self, url):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        self.detail_info_url %= (
            f'{video_id[: -6]}000000',
            f'{video_id[: -3]}000',
            video_id
        )
        video_data = self._download_json(self.detail_info_url, video_id)['video']
        title = video_data['title']

        description = video_data.get('description', '')

        thumbnail = video_data['thumbsrc']

        duration = video_data['duration']
        if duration.count(':') == 1:
            minute, second = duration.split(':')
            duration = int(minute) * 60 + int(second)
        elif duration.count(':') == 2:
            hour, minute, second = duration.split(':')
            duration = int(hour) * 3600 + int(minute) * 60 + int(second)
        else:
            raise

        publishedAt = video_data['post_date'].split(' ')[0]

        view_count = ''

        headers = {'referer': f'https://txxx.tube/embed/{video_id}/'}
        _ = self._download_json(self.video_file_url % video_id, video_id, headers=headers)
        encode_video_url = _[0]['video_url']
        decode_video_url = self.b164_decode(encode_video_url)

        if not decode_video_url:
            raise ExtractorError('Could`t found video url!')

        formats = []
        info = {
            'url': decode_video_url,
            'protocol': 'https',
            'ext': 'mp4',
        }
        formats.append(info)

        # embed_url = f'https://txxx.tube/embed/{video_id}/'
        # player = f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="{embed_url}"></iframe>'

        return {
            'id': video_id,
            'title': title,
            'description': description,
            'duration': duration,
            'thumbnail': thumbnail,
            'view_count': view_count,
            'publishedAt': publishedAt,
            'age_limit': 18,
            'formats': formats,
            # 'player': player
        }
