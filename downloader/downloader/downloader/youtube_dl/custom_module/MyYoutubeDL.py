#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, unicode_literals

import locale
import os
import platform
import re
import subprocess
import sys
import traceback
import json

from ..YoutubeDL import YoutubeDL
from ..compat import (
    compat_basestring,
    compat_str,
)
from ..utils import (
    encode_compat_str,
    error_to_compat_str,
    ExtractorError,
    GeoRestrictedError,
    ISO3166Utils,
    MaxDownloadsReached,
    platform_name,
    version_tuple,
    write_string,
    sanitized_Request,
    UnavailableVideoError,
    SameFileError,
    DEFAULT_OUTTMPL
)
from .extractor import get_info_extractor, gen_extractor_classes, _LAZY_LOADER
from ..extractor.openload import PhantomJSwrapper
from ..downloader.rtmp import rtmpdump_version
from ..postprocessor import (
    FFmpegPostProcessor,
)
from .version import __version__


class MyYoutubeDL(YoutubeDL):
    def urlopen(self, req, data=None):
        """ Start an HTTP download """
        if isinstance(req, compat_basestring):
            req = sanitized_Request(req)
        return self._opener.open(req, data=data, timeout=self._socket_timeout)

    def get_info_extractor(self, ie_key):
        """
        Get an instance of an IE with name ie_key, it will try to get one from
        the _ies list, if there's no instance it will create a new one and add
        it to the extractor list.
        """
        ie = self._ies_instances.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)()
            self.add_info_extractor(ie)
        return ie

    def add_default_info_extractors(self):
        """
        Add the InfoExtractors returned by gen_extractors to the end of the list
        """
        for ie in gen_extractor_classes():
            self.add_info_extractor(ie)

    def print_debug_header(self):
        if not self.params.get('verbose'):
            return

        if type('') is not compat_str:
            # Python 2.6 on SLES11 SP1 (https://github.com/ytdl-org/youtube-dl/issues/3326)
            self.report_warning(
                'Your Python is broken! Update to a newer and supported version')

        stdout_encoding = getattr(
            sys.stdout, 'encoding', 'missing (%s)' % type(sys.stdout).__name__)
        encoding_str = (
            '[debug] Encodings: locale %s, fs %s, out %s, pref %s\n' % (
                locale.getpreferredencoding(),
                sys.getfilesystemencoding(),
                stdout_encoding,
                self.get_encoding()))
        write_string(encoding_str, encoding=None)

        self._write_string('[debug] youtube-dl version ' + __version__ + '\n')
        if _LAZY_LOADER:
            self._write_string('[debug] Lazy loading extractors enabled' + '\n')
        try:
            sp = subprocess.Popen(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            out, err = sp.communicate()
            out = out.decode().strip()
            if re.match('[0-9a-f]+', out):
                self._write_string('[debug] Git HEAD: ' + out + '\n')
        except Exception:
            try:
                sys.exc_clear()
            except Exception:
                pass

        def python_implementation():
            impl_name = platform.python_implementation()
            if impl_name == 'PyPy' and hasattr(sys, 'pypy_version_info'):
                return impl_name + ' version %d.%d.%d' % sys.pypy_version_info[:3]
            return impl_name

        self._write_string('[debug] Python version %s (%s) - %s\n' % (
            platform.python_version(), python_implementation(),
            platform_name()))

        exe_versions = FFmpegPostProcessor.get_versions(self)
        exe_versions['rtmpdump'] = rtmpdump_version()
        exe_versions['phantomjs'] = PhantomJSwrapper._version()
        exe_str = ', '.join(
            '%s %s' % (exe, v)
            for exe, v in sorted(exe_versions.items())
            if v
        )
        if not exe_str:
            exe_str = 'none'
        self._write_string('[debug] exe versions: %s\n' % exe_str)

        proxy_map = {}
        for handler in self._opener.handlers:
            if hasattr(handler, 'proxies'):
                proxy_map.update(handler.proxies)
        self._write_string('[debug] Proxy map: ' + compat_str(proxy_map) + '\n')

        if self.params.get('call_home', False):
            ipaddr = self.urlopen('https://yt-dl.org/ip').read().decode('utf-8')
            self._write_string('[debug] Public IP address: %s\n' % ipaddr)
            latest_version = self.urlopen(
                'https://yt-dl.org/latest/version').read().decode('utf-8')
            if version_tuple(latest_version) > version_tuple(__version__):
                self.report_warning(
                    'You are using an outdated version (newest version: %s)! '
                    'See https://yt-dl.org/update if you need help updating.' %
                    latest_version)

    def download(self, url_list):
        """Download a given list of URLs."""
        outtmpl = self.params.get('outtmpl', DEFAULT_OUTTMPL)
        if (len(url_list) > 1
                and outtmpl != '-'
                and '%' not in outtmpl
                and self.params.get('max_downloads') != 1):
            raise SameFileError(outtmpl)

        for url in url_list:
            try:
                # It also downloads the videos
                res = self.extract_info(
                    url, force_generic_extractor=self.params.get('force_generic_extractor', False))
            except UnavailableVideoError:
                self.report_error('unable to download video')
            except MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloaded files reached.')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    self.to_stdout(json.dumps(res))
                if isinstance(res, dict):
                    res = json.dumps(res)
                return res

        # return self._download_retcode

    def extract_info(self, url, download=True, ie_key=None, extra_info={},
                     process=True, force_generic_extractor=False):
        '''
        Returns a list with a dictionary for each video we find.
        If 'download', also downloads the videos.
        extra_info is a dict containing the extra values to add to each result
        '''

        if not ie_key and force_generic_extractor:
            ie_key = 'Generic'

        if ie_key:
            ies = [self.get_info_extractor(ie_key)]
        else:
            ies = self._ies

        for ie in ies:
            if not ie.suitable(url):
                continue
            ie = self.get_info_extractor(ie.ie_key())
            if not ie.working():
                self.report_warning(
                    'The program functionality for this site has been marked as broken, '
                    'and will probably not work.')

            try:
                if self.params.get('cookie_str'):
                    ie_result = ie.extract(url, self.params['cookie_str'])
                else:
                    ie_result = ie.extract(url)
                if ie_result is None:  # Finished already (backwards compatibility; listformats and friends should be moved here)
                    # break
                    return 'Can`t got result!'
                if isinstance(ie_result, list):
                    # Backwards compatibility: old IE result format
                    ie_result = {
                        '_type': 'compat_list',
                        'entries': ie_result,
                    }
                self.add_default_extra_info(ie_result, ie, url)
                if process:
                    return self.process_ie_result(ie_result, download,
                                                  extra_info)
                else:
                    return ie_result
            except GeoRestrictedError as e:
                msg = e.msg
                if e.countries:
                    msg += '\nThis video is available in %s.' % ', '.join(
                        map(ISO3166Utils.short2full, e.countries))
                msg += '\nYou might want to use a VPN or a proxy server (with --proxy) to workaround.'
                return msg
                # self.report_error(msg)
                # break
            except ExtractorError as e:  # An error we somewhat expected
                # self.report_error(compat_str(e), e.format_traceback())
                return compat_str(e) + '\n' + (e.format_traceback() if e.format_traceback() else '')
                # break
            except MaxDownloadsReached:
                raise
            except Exception as e:
                if self.params.get('ignoreerrors', False):
                    self.report_error(error_to_compat_str(e),
                                      tb=encode_compat_str(
                                          traceback.format_exc()))
                    break
                else:
                    raise
        else:
            return 'no suitable InfoExtractor for URL %s' % url
            # self.report_error('no suitable InfoExtractor for URL %s' % url)
