# coding: utf-8
from __future__ import unicode_literals

import re, time

from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.compat import compat_str
from youtube_dl.utils import (
    determine_ext,
    ExtractorError,
    int_or_none,
    unescapeHTML,
)


class CustomMSNIE(InfoExtractor):
    _VALID_URL = r'https?://(?:(?:www|preview)\.)?msn\.com/(?:[^/]+/)+(?P<display_id>[^/]+)/[a-z]{2}-(?P<id>[\da-zA-Z]+)'
    _TESTS = [{
        'url': 'https://www.msn.com/en-in/money/video/7-ways-to-get-rid-of-chest-congestion/vi-BBPxU6d',
        'md5': '087548191d273c5c55d05028f8d2cbcd',
        'info_dict': {
            'id': 'BBPxU6d',
            'display_id': '7-ways-to-get-rid-of-chest-congestion',
            'ext': 'mp4',
            'title': 'Seven ways to get rid of chest congestion',
            'description': '7 Ways to Get Rid of Chest Congestion',
            'duration': 88,
            'uploader': 'Health',
            'uploader_id': 'BBPrMqa',
        },
    }, {
        # Article, multiple Dailymotion Embeds
        'url': 'https://www.msn.com/en-in/money/sports/hottest-football-wags-greatest-footballers-turned-managers-and-more/ar-BBpc7Nl',
        'info_dict': {
            'id': 'BBpc7Nl',
        },
        'playlist_mincount': 4,
    }, {
        'url': 'http://www.msn.com/en-ae/news/offbeat/meet-the-nine-year-old-self-made-millionaire/ar-BBt6ZKf',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/video/watch/obama-a-lot-of-people-will-be-disappointed/vi-AAhxUMH',
        'only_matching': True,
    }, {
        # geo restricted
        'url': 'http://www.msn.com/en-ae/foodanddrink/joinourtable/the-first-fart-makes-you-laugh-the-last-fart-makes-you-cry/vp-AAhzIBU',
        'only_matching': True,
    }, {
        'url': 'http://www.msn.com/en-ae/entertainment/bollywood/watch-how-salman-khan-reacted-when-asked-if-he-would-apologize-for-his-‘raped-woman’-comment/vi-AAhvzW6',
        'only_matching': True,
    }, {
        # Vidible(AOL) Embed
        'url': 'https://www.msn.com/en-us/money/other/jupiter-is-about-to-come-so-close-you-can-see-its-moons-with-binoculars/vi-AACqsHR',
        'only_matching': True,
    }, {
        # Dailymotion Embed
        'url': 'https://www.msn.com/es-ve/entretenimiento/watch/winston-salem-paire-refait-des-siennes-en-perdant-sa-raquette-au-service/vp-AAG704L',
        'only_matching': True,
    }, {
        # YouTube Embed
        'url': 'https://www.msn.com/en-in/money/news/meet-vikram-%E2%80%94-chandrayaan-2s-lander/vi-AAGUr0v',
        'only_matching': True,
    }, {
        # NBCSports Embed
        'url': 'https://www.msn.com/en-us/money/football_nfl/week-13-preview-redskins-vs-panthers/vi-BBXsCDb',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        display_id, page_id = re.match(self._VALID_URL, url).groups()

        webpage = self._download_webpage(url, display_id)

        mapping = {
            'FHD': 1080,
            'HD': 720,
            'HQ': 540,
            'SD': 540,
            'LO': 360,
            'HLS': 1080,
            'DASH': 1080
        }

        entries = []
        infos = re.findall(
            r'data-pluginConfig\s*=\s*(["\'])(?P<data>.+?)\1',
            webpage
        ) or re.findall(
            r'data-metadata\s*=\s*(["\'])(?P<data>.+?)\1',
            webpage
        )
        if infos:
            for _, metadata in infos:
                video = self._parse_json(unescapeHTML(metadata), display_id)

                provider_id = video.get('providerId')
                player_name = video.get('playerName')
                if player_name and provider_id:
                    entry = None
                    if player_name == 'AOL':
                        if provider_id.startswith('http'):
                            provider_id = self._search_regex(
                                r'https?://delivery\.vidible\.tv/video/redirect/([0-9a-f]{24})',
                                provider_id, 'vidible id')
                        entry = self.url_result(
                            'aol-video:' + provider_id, 'Aol', provider_id)
                        entry.update(
                            {'_type': 'url_transparent'}
                        )
                    elif player_name == 'Dailymotion':
                        entry = {
                            '_type': 'url',
                            'ie_key': 'Dailymotion',
                            'id': provider_id,
                            'display_id': display_id,
                            'url': 'https://www.dailymotion.com/video/' + provider_id,
                            'title': video['title'],
                            'description': video.get('description'),
                            'thumbnail': (video.get('thumbnail', '') or video.get('headlineImage', {'url': ''})).get('url', ''),
                            'duration': video.get('durationSecs'),
                            'publishedAt': '',
                            'player': f'<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.dailymotion.com/embed/video/{provider_id}"></iframe>'
                        }
                    elif player_name == 'YouTube':
                        entry = {
                            '_type': 'url',
                            'ie_key': 'CustomYoutube',
                            'id': provider_id,
                            'display_id': display_id,
                            'url': f'https://www.youtube.com/watch?v={provider_id}',
                            'title': video['title'],
                            'description': video.get('description'),
                            'thumbnail': (video.get('thumbnail', '') or video.get('headlineImage', {'url': ''})).get('url', ''),
                            'duration': video.get('durationSecs'),
                            'publishedAt': '',
                            'player': f'''<iframe width="100%" height="100%" frameborder="0" allowfullscreen src="https://www.amoyshare.com/player/?v={provider_id}&watch={int(time.time())}"></iframe>'''
                        }
                    elif player_name == 'NBCSports':
                        entry = self.url_result(
                            'http://vplayer.nbcsports.com/p/BxmELC/nbcsports_embed/select/media/' + provider_id,
                            'CustomNBCSportsVPlayer', provider_id)
                        entry.update(
                            {'_type': 'url_transparent'}
                        )
                        return entry
                    if entry:
                        entries.append(entry)
                        continue

                video_id = video['freewheel']['providerId']
                title = self._html_search_meta(r'og:title', webpage, 'title')
                description = self._html_search_meta(r'description', webpage,
                                                     'description', default='')
                thumbnail = self._html_search_meta(r'og:image', webpage,
                                                   'og:image')
                duration = self._html_search_regex(r'Duration:(.*?)</span>',
                                                   webpage, 'duration',
                                                   default=None)
                if duration:
                    duration_parts = duration.split(':')
                    if len(duration_parts) == 2:
                        mins, seconds = duration_parts
                        mins, seconds = int(mins) * 60, int(seconds)
                        duration = mins + seconds
                    else:
                        hours, mins, seconds = duration_parts
                        hours, mins, seconds = int(hours) * 3600, int(
                            mins) * 60, int(seconds)
                        duration = hours + mins + seconds

                publishedAt = self._html_search_regex(r'>(.*?)</time>', webpage,
                                                      'publish date',
                                                      default='')

                formats = []
                for file_ in video.get('videoFiles', []):
                    format_url = file_.get('url')
                    bitrate = file_['bitrate']
                    if not format_url or bitrate == 0:
                        continue
                    else:
                        formats.append({
                            'url': format_url,
                            'ext': 'mp4',
                            'height': mapping[file_['id']],
                            'vbr': int_or_none(self._search_regex(r'_(\d+)\.mp4', format_url, 'vbr', default=None)),
                        })
                self._sort_formats(formats)

                subtitles = {}
                for file_ in video.get('files', []):
                    format_url = file_.get('url')
                    format_code = file_.get('formatCode')
                    if not format_url or not format_code:
                        continue
                    if compat_str(format_code) == '3100':
                        subtitles.setdefault(file_.get('culture', 'en'), []).append({
                            'ext': determine_ext(format_url, 'ttml'),
                            'url': format_url,
                        })

                return {
                    'id': video_id,
                    'display_id': display_id,
                    'title': title,
                    'description': description,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'publishedAt': publishedAt,
                    'formats': formats,
                    'subtitles': subtitles
                }

        if not entries:
            error = unescapeHTML(self._search_regex(
                r'data-error=(["\'])(?P<error>.+?)\1',
                webpage, 'error', group='error',
                default='Unsupport link or 404'))
            raise ExtractorError('%s said: %s' % (self.IE_NAME, error), expected=True)

        return self.playlist_result(entries, page_id)
