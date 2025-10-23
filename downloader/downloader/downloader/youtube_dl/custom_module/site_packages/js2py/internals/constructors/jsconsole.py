from __future__ import unicode_literals

from youtube_dl.custom_module.site_packages.js2py.internals.conversions import *
from youtube_dl.custom_module.site_packages.js2py.internals.func_utils import *


class ConsoleMethods:
    def log(this, args):
        x = ' '.join(to_string(e) for e in args)
        print(x)
        return undefined
