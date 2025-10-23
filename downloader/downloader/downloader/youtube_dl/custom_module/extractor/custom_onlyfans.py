from __future__ import unicode_literals

import re
import json
from youtube_dl.extractor.common import InfoExtractor
from youtube_dl.utils import (
    parse_count,
    ExtractorError,
    GeoRestrictedError
)
from youtube_dl.compat import compat_http_client
import time


class BaseExtractor(InfoExtractor):
    def _real_extract(self, url, cookie_str):
        """Real extraction process. Redefine in subclasses."""
        pass

    def extract(self, url, cookie_str=''):
        """Extracts URL information and returns it in list of dicts."""
        try:
            for _ in range(2):
                try:
                    self.initialize()
                    ie_result = self._real_extract(url, cookie_str)
                    if self._x_forwarded_for_ip:
                        ie_result['__x_forwarded_for_ip'] = self._x_forwarded_for_ip
                    return ie_result
                except GeoRestrictedError as e:
                    if self.__maybe_fake_ip_and_retry(e.countries):
                        continue
                    raise
        except ExtractorError:
            raise
        except compat_http_client.IncompleteRead as e:
            raise ExtractorError('A network error has occurred.', cause=e,
                                 expected=True)
        except (KeyError, StopIteration) as e:
            raise ExtractorError('An extractor error has occurred.', cause=e)


class CustomOnlyFansIE(BaseExtractor):
    _VALID_URL = r'https?://(?:www\.)?onlyfans\.com/(?P<id>\d+)/(?P<user>[^/?#&]+)'
    api_url = 'https://onlyfans.com/api2/v2/posts/%s?skip_users=all&skip_users_dups=1'

    @classmethod
    def suitable(cls, url):
        rs = re.match(cls._VALID_URL, url) is not None
        return rs

    def gen_sign_dt(self, ts_str):
        import hashlib
        from youtube_dl.custom_module.site_packages.js2py import EvalJs

        # b_text = f"kumgH49U7Fz0bmKCVDo1K2T9uy0fqTTD\n{ts_str}\n/api2/v2/init\n0".encode()
        b_text = f"kumgH49U7Fz0bmKCVDo1K2T9uy0fqTTD{ts_str}/api2/v2/init0".encode()
        sha = hashlib.sha1(b_text)
        sign_d = sha.hexdigest()

        js_str = r'''
            var u = ["W5hdMuPxahW", "WRjXWOWIWRpdQmoGW71vzq", "WQ1ejr7cLbzUCCkQra", "cCkfWQ3dTxdcUmooqa3cKq", "BmoDWQVdGavBiCkRWOZcPG", "WRXMWQ1SW5VcQG", "W6S0WPNdTJ5+qmonvmoG", "y8oqWQtdLtjC", "fZSNWO3cGGugAmkwvNTl", "WOZdKg19ogrv", "WORcSmolWPqLWQi", "WOznaCkllsddPCoLWQBcUGvJWObOW6FcQ23dP39IumoUW5DVW5ddOYOaW6JdPSk5yG", "WQxdLmkTW73cKN9ACmodW6W", "WPXbaCk+W6RdUa", "DCo1WQfnW5pcJeSjWQ/dQW", "W49NW6pdP8oRdmkkW7tcPg0", "WRpcNsawW7OJ", "DSoMFgbGWR4aW6u", "DmomWPzwFLNcKuPpWPhdUgW", "W53dPCksCIX9", "WRnRWQj5W6ZcRCkrAWGD", "kCo0WOFcJSkhmSkJgfra", "x8o6W57cISkTbCoDfYqA", "iCkzW44hmGq", "W5WCb3JcOIJdLSkhmLa", "W7GYvdiPW4NdOCohWPldKG", "o8kwCmkIW5mAe1uvmq", "wGddT2FcS8o6W4ldIZn9W6VcSW", "gMpdO1pcM8og", "bvFcOdNdV8kH", "WQjjkGVcOXe", "W6iPW54wWOxdHCo0W5b4", "WQm1k8kCWO/cQSoiW6tdISoJ", "W7FcJCo5WR/dOYukCCoGW6HXWPZcQG", "W6JdRv4HW7NdTq", "WOVcL8k0FaRdLfT6W4yt", "WPNdK33dV0qkjw4rDfXYWRO", "WPNdLY/cHHv0wgm", "W5uNAIf2fa", "E8orWOdcHYtcKCkXWO8kWRmpW4/cPSoxyvyxWP4L", "WQvWWOa1", "l8kltN8cdJLgkHS", "WQldIJGMWRxdI2ixDmk7", "jCkTW7n5W6xcOv8KWOi", "W5OQztrbe2T9W7ZcMa", "WPS+WRtcRmoakmkiW5/cO24", "W6hcICkK", "W6ldVCkHW6ldJvxcOmoPmSkd", "wmoofdmTmW", "w8oKhmkueSo6W7JdUW", "WQW4jmkjWRJcRq", "W6aRW5S", "W6pcG8k2mfJcJIFcPraP", "WRlcP8o5WQNcTGNcS8oRpCkswt0", "W7BcKwfGW4hdRhCvE8kBAa", "uJxcQ8oBcSkVW5FcI8khWQ0", "W7eXa8kJWOdcTCoz", "WP1zW6pdKSoWgSkL", "nmkBF8k3W6qD", "W5yqWOVcPsHH", "rwP+W4VdSLmXqCkouW", "W5aAWOZcRa", "uCk4imo1W7JcIW", "W5JcPq3cOs1YW5a", "WO1bW53dTgO4zmkAk8ouW7Dy", "W5hdUKHaW5/cIa", "W4tcHYBcQajx", "WP3cHCkCqSkQvNRcLL9DamoX", "i8k+EcDcWRufWRJcSmog", "kmkEs8krWQddSKXqm31XW7O", "lSkuW4esbqpcSebcWO4", "DSoyWPFcNadcN8kHWOu5W6K", "W7C/wYCEW44", "h8kFWQa", "W6iZWPhdQG", "kSkzW5quiX7cPWTIWO/dUK5UW74mW7GwW6NdGZ/dNLpcPG", "WPnmdSkRW53dV1lcMcDA", "bCkEhr06emkaya", "xtJcPmoopCkO", "bCksqMbQySkArtBdQmo5WPS", "C8ophCoaW6lcQW", "vbNcQse", "qmooW6pdHmk/AG", "EvXLWRa", "WR9VW4dcSePzvCopw8oaoa", "WOfDaSklexW"];
            function c(t, e) {
                t -= 350;
                var r = u[t];
                if (void 0 === c["cbFZkw"]) {
                    var n = function (t) {
                        for (var e, r, n = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+/=", s = "", i = 0, a = 0; r = t["charAt"](a++); ~r && (e = i % 4 ? 64 * e + r : r,
                            i++ % 4) ? s += String["fromCharCode"](255 & e >> (-2 * i & 6)) : 0)
                            r = n["indexOf"](r);
                        return s
                    }
                        , s = function (t, e) {
                            var r, s, i = [], a = 0, o = "", u = "";
                            t = n(t);
                            for (var c = 0, l = t["length"]; c < l; c++)
                                u += "%" + ("00" + t["charCodeAt"](c)["toString"](16))["slice"](-2);
                            for (t = decodeURIComponent(u),
                                s = 0; s < 256; s++)
                                i[s] = s;
                            for (s = 0; s < 256; s++)
                                a = (a + i[s] + e["charCodeAt"](s % e["length"])) % 256,
                                    r = i[s],
                                    i[s] = i[a],
                                    i[a] = r;
                            s = 0,
                                a = 0;
                            for (var d = 0; d < t["length"]; d++)
                                s = (s + 1) % 256,
                                    a = (a + i[s]) % 256,
                                    r = i[s],
                                    i[s] = i[a],
                                    i[a] = r,
                                    o += String["fromCharCode"](t["charCodeAt"](d) ^ i[(i[s] + i[a]) % 256]);
                            return o
                        };
                    c["TnUiKG"] = s,
                        c["yWabio"] = {},
                        c["cbFZkw"] = !0
                }
                var i = u[0]
                    , a = t + i
                    , o = c["yWabio"][a];
                return void 0 === o ? (void 0 === c["XrStpl"] && (c["XrStpl"] = !0),
                    r = c["TnUiKG"](r, e),
                    c["yWabio"][a] = r) : r = o,
                    r
            };
            (function (t, e) {
                var r = function (t, e) {
                    return c(e - -202, t)
                };
                while (1)
                    try {
                        var n = -parseInt(r("MksQ", 159)) * -parseInt(r("]j!Z", 195)) + parseInt(r("MVHQ", 165)) + parseInt(r("KuUl", 199)) + -parseInt(r("7O28", 226)) * -parseInt(r("CqDU", 188)) + -parseInt(r("*lmf", 169)) * -parseInt(r("sl25", 216)) + -parseInt(r("vuSz", 196)) + parseInt(r("q5C@", 175)) * -parseInt(r("wGEg", 177));
                        if (n === e)
                            break;
                        t["push"](t["shift"]())
                    } catch (s) {
                        t["push"](t["shift"]())
                    }
            }
            )(u, 772198);
            var sign_dt = function() {
                var e = function(t, e) {
                    return c(t - -789, e)
                };
                var r = {
                    C: function(t, e) {
                        return t + e
                    },
                    w: function(t, e) {
                        return t + e
                    },
                    a: function(t, e) {
                        return t + e
                    },
                    R: function(t, e) {
                        return t + e
                    },
                    D: function(t, e) {
                        return t + e
                    },
                    q: function(t, e) {
                        return t + e
                    },
                    N: function(t, e) {
                        return t + e
                    },
                    L: function(t, e) {
                        return t + e
                    },
                    Z: function(t, e) {
                        return t + e
                    },
                    l: function(t, e) {
                        return t + e
                    },
                    Y: function(t, e) {
                        return t + e
                    },
                    i: function(t, e) {
                        return t + e
                    },
                    f: function(t, e) {
                        return t + e
                    },
                    p: function(t, e) {
                        return t + e
                    },
                    Q: function(t, e) {
                        return t - e
                    },
                    s: function(t, e) {
                        return t % e
                    },
                    S: function(t, e) {
                        return t - e
                    },
                    K: function(t, e) {
                        return t + e
                    },
                    j: function(t, e) {
                        return t + e
                    },
                    m: function(t, e) {
                        return t % e
                    },
                    O: function(t, e) {
                        return t + e
                    },
                    y: function(t, e) {
                        return t - e
                    },
                    r: function(t, e) {
                        return t - e
                    },
                    g: function(t, e) {
                        return t - e
                    },
                    U: function(t, e) {
                        return t % e
                    },
                    n: function(t, e) {
                        return t + e
                    },
                    k: function(t, e) {
                        return t % e
                    },
                    B: function(t, e) {
                        return t - e
                    },
                    h: function(t, e) {
                        return t % e
                    },
                    c: function(t, e) {
                        return t + e
                    },
                    X: function(t, e) {
                        return t % e
                    },
                    P: function(t, e) {
                        return t - e
                    },
                    J: function(t, e) {
                        return t + e
                    },
                    W: function(t, e) {
                        return t % e
                    },
                    T: function(t, e) {
                        return t + e
                    },
                    b: function(t, e) {
                        return t - e
                    },
                    o: function(t, e) {
                        return t % e
                    },
                    d: function(t, e) {
                        return t % e
                    },
                    I: function(t, e) {
                        return t % e
                    },
                    e: function(t, e, r, n) {
                        return t(e, r, n)
                    },
                    E: function(t, e, r, n) {
                        return t(e, r, n)
                    }
                };
                r["F"] = "getters.auth/authUserId",
                r["u"] = function(t, e) {
                    return t(e)
                }
                ,
                r["x"] = "kumgH49U7Fz0bmKCVDo1K2T9uy0fqTTD",
                r["v"] = "136",
                r["V"] = "60e5ada8";
                var n = r
                    , i = "/api2/v2/init"
                    , dt = {};
                //u["time"] = +new Date; //by python generate
                dt["time"] = %python_ts_str;
                var l = null
                    //, d = n["u"](s.a, [n["x"], u["time"], i, 0].join("\n"));  //sha1 method by python generate
                    , d = "%python_sign_d";
                return dt["sign"] = [n["v"], d, function(t) {
                    var r = function(t, r) {
                        return e(t - -297, r)
                    };
                    return Math.abs(n["C"](n["C"](n["C"](n["C"](n["C"](n["C"](n["w"](n["a"](n["R"](n["D"](n["q"](n["N"](n["L"](n["Z"](n["l"](n["Y"](n["Y"](n["i"](n["f"](n["p"](n["Q"](t[n["s"](2229, t[r(-653, "PI^k")])][r(-651, "wGEg")](0), 78), n["S"](t[2456 % t[r(-704, "NYDj")]][r(-705, "CqTV")](0), 127)), n["K"](t[1962 % t[r(-672, "Mrih")]][r(-710, "wi&N")](0), 132)), n["j"](t[n["m"](625, t[r(-687, "oC^C")])][r(-660, "sl25")](0), 65)), n["j"](t[n["m"](1054, t[r(-656, "t35i")])][r(-663, "22*3")](0), 80)) + n["j"](t[1443 % t[r(-690, "1eE#")]][r(-710, "wi&N")](0), 89), n["O"](t[n["m"](1792, t[r(-686, "*lmf")])][r(-652, "q5C@")](0), 98)) + n["S"](t[n["m"](1178, t[r(-659, "f4OF")])][r(-710, "wi&N")](0), 75), t[577 % t[r(-670, "aENH")]][r(-728, "K39l")](0) + 103) + n["y"](t[n["m"](1585, t[r(-733, "CxM)")])][r(-684, "XN!v")](0), 92), n["r"](t[746 % t[r(-674, "(#ag")]][r(-651, "wGEg")](0), 131)), n["g"](t[n["m"](920, t[r(-733, "CxM)")])][r(-731, "&rdf")](0), 81)) + (t[n["U"](2789, t[r(-656, "t35i")])][r(-665, "nXAg")](0) - 112) + (t[n["U"](2565, t[r(-718, "orlt")])][r(-730, "y&n%")](0) - 114), n["n"](t[n["k"](2281, t[r(-736, "2LkC")])][r(-692, "7O28")](0), 61)), n["B"](t[2087 % t[r(-653, "PI^k")]][r(-711, "I8Q7")](0), 62)) + n["B"](t[n["h"](475, t[r(-680, "ST)]")])][r(-664, "bgfH")](0), 140), n["c"](t[194 % t[r(-667, "TL^K")]][r(-728, "K39l")](0), 70)), n["B"](t[2172 % t[r(-661, "rjM6")]][r(-697, "(#ag")](0), 113)), n["B"](t[n["X"](1694, t[r(-702, "CqDU")])][r(-654, "MVHQ")](0), 139)) + n["P"](t[n["X"](1289, t[r(-733, "CxM)")])][r(-732, "rjM6")](0), 120), n["J"](t[n["W"](362, t[r(-693, "vuSz")])][r(-708, "Th%H")](0), 94)), n["J"](t[n["W"](2353, t[r(-666, "u5aN")])][r(-681, "uufB")](0), 89)), n["T"](t[n["W"](1357, t[r(-674, "(#ag")])][r(-682, "tEy6")](0), 81)) + n["P"](t[1510 % t[r(-722, "bgfH")]][r(-720, "CqDU")](0), 73), n["b"](t[n["o"](863, t[r(-733, "CxM)")])][r(-662, "f4OF")](0), 148)) + n["b"](t[1129 % t[r(-729, "tEy6")]][r(-726, "CqZu")](0), 84), n["T"](t[n["d"](2032, t[r(-723, "MksQ")])][r(-682, "tEy6")](0), 86)) + n["T"](t[n["d"](1004, t[r(-690, "1eE#")])][r(-727, "ST)]")](0), 96) + n["b"](t[2682 % t[r(-694, "CqZu")]][r(-676, "PI^k")](0), 143), t[n["d"](1840, t[r(-724, "BkZ9")])][r(-676, "PI^k")](0) + 64), t[n["I"](278, t[r(-714, "Th%H")])][r(-700, "v7i1")](0) + 106))[r(-703, "*b6h")](16)
                }(d), n["V"]].join(":"),
                dt
            };
        '''.replace('%python_ts_str', ts_str).replace('%python_sign_d', sign_d)
        ej = EvalJs()
        ej.execute(js_str)
        sign_dt = ej.sign_dt()
        sign = sign_dt['sign']
        return sign

    def _real_extract(self, url, request_header_json):
        mobj = re.match(self._VALID_URL, url)
        video_id = mobj.group('id')

        if request_header_json:
            # request_header = json.loads(request_header_json)
            ts_str = str(time.time()).replace('.', '')[:13]
            request_header = {
                'accept': 'application/json, text/plain, */*',
                'app-token': '33d57ade8c02dbc5a333db99ff9ae26a',
                'cookie': 'csrf=MD8nnBfF32f25d4778a8ada9cc8ebdd736713d04; fp=81d578c490275de9c4bc717de173f3f9; sess=jctt2373pt9udvvn5ek54bpg87; auth_id=152395336; st=c985461907c062d4430d477dcd64a9428a4679dce7bf6fca3c017b89a2033d65; ref_src=',
                'sign': self.gen_sign_dt(ts_str),
                'time': ts_str,
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
                'user-id': '152395336',
                'x-bc': '619961ba772bcd76553508c62d0f1e51ce53fbcb',
            }
        else:
            raise ExtractorError('Require login, please pass login info!')
        json_data = self._download_json(self.api_url % video_id, video_id, headers=request_header)

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
