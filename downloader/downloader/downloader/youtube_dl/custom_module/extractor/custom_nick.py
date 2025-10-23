# coding: utf-8
from __future__ import unicode_literals

import re

from youtube_dl.extractor.mtv import MTVServicesInfoExtractor
from youtube_dl.utils import update_url_query


class CustomNickBrIE(MTVServicesInfoExtractor):
    IE_NAME = 'nickelodeon:br'
    _VALID_URL = r'''(?x)
                    https?://
                        (?:
                            (?P<domain>(?:www\.)?nickjr|mundonick\.uol)\.com\.br|
                            (?:www\.)?nickjr\.[a-z]{2}|
                            (?:www\.)?nickelodeon(?:junior)?\.fr
                        )
                        /(?:programas/)?[^/]+/videos/(?:episodios/)?(?P<id>[^/?\#.]+)
                    '''
    _TESTS = [{
        'url': 'http://www.nickjr.com.br/patrulha-canina/videos/210-labirinto-de-pipoca/',
        'only_matching': True,
    }, {
        'url': 'http://mundonick.uol.com.br/programas/the-loud-house/videos/muitas-irmas/7ljo9j',
        'only_matching': True,
    }, {
        'url': 'http://www.nickjr.nl/paw-patrol/videos/311-ge-wol-dig-om-terug-te-zijn/',
        'only_matching': True,
    }, {
        'url': 'http://www.nickjr.de/blaze-und-die-monster-maschinen/videos/f6caaf8f-e4e8-4cc1-b489-9380d6dcd059/',
        'only_matching': True,
    }, {
        'url': 'http://www.nickelodeonjunior.fr/paw-patrol-la-pat-patrouille/videos/episode-401-entier-paw-patrol/',
        'only_matching': True,
    }]

    def _real_extract(self, url):
        domain, display_id = re.match(self._VALID_URL, url).groups()
        webpage = self._download_webpage(url, display_id)
        uri = self._search_regex(
            r'data-(?:contenturi|mgid)="([^"]+)', webpage, 'mgid')
        video_id = self._id_from_uri(uri)
        config = self._download_json(
            'http://media.mtvnservices.com/pmt/e1/access/index.html',
            video_id, query={
                'uri': uri,
                'configtype': 'edge',
            }, headers={
                'Referer': url,
            })
        info_url = self._remove_template_parameter(config['feedWithQueryParams'])
        if info_url == 'None':
            if domain.startswith('www.'):
                domain = domain[4:]
            content_domain = {
                'mundonick.uol': 'mundonick.com.br',
                'nickjr': 'br.nickelodeonjunior.tv',
            }[domain]
            query = {
                'mgid': uri,
                'imageEp': content_domain,
                'arcEp': content_domain,
            }
            if domain == 'nickjr.com.br':
                query['ep'] = 'c4b16088'
            info_url = update_url_query(
                'http://feeds.mtvnservices.com/od/feed/intl-mrss-player-feed', query)
        return self._get_videos_info_from_url(info_url, video_id)
