from __future__ import unicode_literals

try:
    from .lazy_extractors import *
    from .lazy_extractors import _ALL_CLASSES
    _LAZY_LOADER = True
except ImportError:
    _LAZY_LOADER = False
    ############
    from youtube_dl.extractor.vimeo import VimeoIE
    from youtube_dl.extractor.dailymotion import DailymotionIE
    from youtube_dl.extractor.aol import AolIE
    from youtube_dl.extractor.kaltura import KalturaIE
    from youtube_dl.extractor.odnoklassniki import OdnoklassnikiIE
    from youtube_dl.extractor.pladform import PladformIE
    from youtube_dl.extractor.rutube import RutubeEmbedIE
    from youtube_dl.extractor.generic import GenericIE
    from .custom_youtube import *
    from .custom_soundcloud import *
    from .custom_archiveorg import *
    from .custom_4shared import *
    from .custom_jamendo import CustomJamendoRadioIE, CustomJamendoIE, CustomJamendoPlaylistIE, CustomJamendoSearchIE
    from .custom_instagram import *
    from .custom_naver import *
    from .custom_audiomack import *
    from .custom_hearthisat import *
    from .custom_fourtube import *
    from .custom_porn91 import *
    from .custom_alphaporno import *
    from .custom_camwithher import *
    from .custom_cliphunter import *
    from .custom_drtuber import *
    from .custom_eporner import *
    from .custom_extremetube import *
    from .custom_spankbang import *
    from .custom_lovehomeporn import *
    from .custom_playvid import *
    from .custom_pornhd import *
    from .custom_pornhub import *
    from .custom_youporn import *
    from .custom_xhamster import *
    from .custom_redtube import *
    from .custom_xvideos import *
    from .custom_xnxx import *
    from .custom_spankwire import *
    from .custom_youjizz import *
    from .custom_xtube import *
    from .custom_pornone import *
    from .custom_sexu import *
    from .custom_tube8 import *
    from .custom_toypics import *
    from .custom_pornoxo import *
    from .custom_sunporno import *
    from .custom_anysex import *
    from .custom_beeg import *
    from .custom_9anime import *
    from .custom_facebook import *
    from .custom_funimate import *
    from .custom_animedao import *
    from .custom_gogoanime import *
    from .custom_animefreak import *
    from .custom_indavideo import *
    from .custom_wistia import *
    from .custom_tiktok import *
    from .custom_gamestar import *
    from .custom_abc import *
    from .custom_tumblr import *
    from .custom_yespornplease import *
    from .custom_porngo import *
    # from .custom_nwkings import *
    from .custom_bandcamp import *
    from .custom_txxx import CustomTxxxIE
    from .custom_bellesa import *
    from .custom_frolicme import *
    from .custom_brightcove import *
    from .custom_motherless import *
    from .custom_lynda import *
    from .custom_nbc import CustomNBCIE, CustomNBCSportsVPlayerIE, CustomNBCSportsIE, CustomNBCSportsStreamIE, CustomCSNNEIE, CustomNBCNewsIE, CustomNBCOlympicsIE, CustomNBCOlympicsStreamIE, ThePlatformIE
    from .custom_arte import CustomArteTVIE, CustomArteTVEmbedIE, CustomArteTVPlaylistIE
    from .custom_firsttv import CustomFirstTVIE
    from .custom_ted import CustomTEDIE
    from .custom_amara import CustomAmaraIE
    from .custom_lbry import CustomLBRYIE
    from .custom_npr import CustomNprIE
    from .custom_yandexmusic import CustomYandexMusicTrackIE, CustomYandexMusicAlbumIE, CustomYandexMusicPlaylistIE, CustomYandexMusicArtistTracksIE
    from .custom_kakao import CustomKakaoIE
    from .custom_blogtalkradio import CustomBlogTalkRadioIE
    from .custom_giga import CustomGigaIE
    from .custom_lecturio import CustomLecturioIE
    from .custom_netzkino import CustomNetzkinoIE
    from .custom_ifunny import CustomIfunnyIE
    from .custom_ddrk import CustomDdrkIE
    from .custom_nick import CustomNickBrIE
    from .custom_varzesh3 import CustomVarzesh3IE
    from .custom_lemonde import CustomLemondeIE
    from .custom_msn import CustomMSNIE
    from .custom_clyp import CustomClypIE
    from .custom_internazionale import CustomInternazionaleIE
    from .custom_la7 import CustomLA7IE
    from .custom_rai import CustomRaiIE, CustomRaiPlayIE, CustomRaiPlayLiveIE, CustomRaiPlayPlaylistIE
    from .custom_vk import CustomVKIE, CustomVKMusicPlayListIE, CustomVKUserVideosIE, CustomVKWallPostIE, CustomVKUserPageIE
    from .custom_niconico import CustomNiconicoIE
    from .custom_spotify import CustomSpotifyIE, CustomSpotifyShowIE
    # from .custom_onlyfans import CustomOnlyFansIE
    from .custom_pornflip import CustomPornFlipIE
    from .custom_porntrex import CustomPornTrexIE
    # from .custom_thisvid import CustomThisVidIE
    from .custom_biqle import CustomBIQLEIE
    from .custom_erome import CustomEromeIE
    from .custom_slutload import CustomSlutLoadLiveIE, CustomSlutLoadMediaIE, CustomSlutLoadVideoIE
    from .custom_reddit import CustomRedditIE, CustomRedditRIE
    from .custom_mixcloud import CustomMixcloudIE, CustomMixcloudPlaylistIE
    from .custom_bilibili import CustomBiliBiliIE, CustomBiliBiliBangumiIE, CustomBilibiliAudioIE, CustomBilibiliAudioAlbumIE, CustomBiliBiliPlayerIE
    ############
    _ALL_CLASSES = [
        klass
        for name, klass in globals().items()
        if name.endswith('IE') and name != 'GenericIE'
    ]
    _ALL_CLASSES.append(GenericIE)


def gen_extractor_classes():
    """ Return a list of supported extractors.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return _ALL_CLASSES


def gen_extractors():
    """ Return a list of an instance of every supported extractor.
    The order does matter; the first extractor matched is the one handling the URL.
    """
    return [klass() for klass in gen_extractor_classes()]


def list_extractors(age_limit):
    """
    Return a list of extractors that are suitable for the given age,
    sorted by extractor ID.
    """

    return sorted(
        filter(lambda ie: ie.is_suitable(age_limit), gen_extractors()),
        key=lambda ie: ie.IE_NAME.lower())


def get_info_extractor(ie_name):
    """Returns the info extractor class with the given ie_name"""
    return globals()[ie_name + 'IE']
