# `youtube search`

支持的url
```bash
https://www.youtube.com/results?search_query=hello
https://www.youtube.com/results?search_query=hello&gl=cn
https://www.youtube.com/results?search_query=hello&page=2
https://www.youtube.com/results?search_query=hello&gl=cn&page=2
https://www.youtube.com/results?search_query=hello&sp=EgIIAw%253D%253D
https://www.youtube.com/results?search_query=hello&gl=cn&sp=EgIIAw%253D%253D
https://www.youtube.com/results?search_query=hello&sp=EgIIAw%253D%253D&page=2
https://www.youtube.com/results?search_query=hello&gl=cn&sp=EgIIAw%253D%253D&page=2

gl参数, 可选，代表根据国家过滤
page参数, 不传递的默认为1, 最多返回51页
sp过滤参数, 过滤规则（按天，按周，按年等)
参数顺序要search_query > gl > sp > page顺序
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "YQHsXMglC9A",
        "title": "Adele - Hello",
        "publishedAt": "",
        "thumbnail": "https://i.ytimg.com/vi/YQHsXMglC9A/mqdefault.jpg",
        "description": "This is a track hello by adelle",
        "url": "https://www.youtube.com/watch?v=YQHsXMglC9A",
        "player": "<iframe style=\"position:absolute;left:0px;top:0px;\" width=\"100%\" height=\"100%;z-index:100;\" src=\"https://www.youtube.com/embed/YQHsXMglC9A?autoplay=1\" frameborder=\"0\" allow=\"picture-in-picture\" allowfullscreen=\"\"></iframe>",
        "duration": "6:07",
        "viewCount": "2M",
        "media": null
      },
      ......
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true
  }
}
```
        
返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (bool): 是否有下一页
   
items列表里项字段
   
  - `id` (string): youtube 视频id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 播放的iframe
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息(忽略)


#
# `soundcloud search`


支持的url
```bash
https://soundcloud.com/search?q=hello
https://soundcloud.com/search?q=hello&page=3

page参数, 不传递的默认为1, 最多返回10页
参数顺序要q > page顺序
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "230155983",
        "title": "Hello - Adele",
        "publishedAt": "2015-10-26",
        "thumbnail": "https://i1.sndcdn.com/artworks-000134001026-tugyco-large.jpg",
        "description": "Vocals/Piano/Recording/Production by me, in my bedroom!\n\nFollow me on:\nWebsite: www.gracedaviesofficial.com\nFacebook: gracedaviesofficial\nYouTube: gracedaviesoffical\nInstagram: gracedaviesofficial\nSnapchat: gracedofficial\nTwitter: gracedavies",
        "url": "https://soundcloud.com/gracedaviesofficial/hello-adele",
        "player": "<iframe width=\"100%\" height=\"300\" scrolling=\"no\" frameborder=\"no\" allow=\"autoplay\" src=\"https://w.soundcloud.com/player/?url=https%3A//api.soundcloud.com/tracks/230155983&color=%23ff5500&auto_play=false&hide_related=false&show_comments=true&show_user=true&show_reposts=false&show_teaser=true&visual=true\"></iframe>",
        "duration": "05:00",
        "viewCount": "62M",
        "media": [
          {
            "url": "https://api-v2.soundcloud.com/media/soundcloud:tracks:230155983/3cf23989-1226-4fbd-852c-59bcab006c25/stream/hls",
            "preset": "mp3_0_0",
            "duration": 300880,
            "snipped": false,
            "format": {
              "protocol": "hls",
              "mime_type": "audio/mpeg"
            },
            "quality": "sq"
          },
          {
            "url": "https://api-v2.soundcloud.com/media/soundcloud:tracks:230155983/3cf23989-1226-4fbd-852c-59bcab006c25/stream/progressive",
            "preset": "mp3_0_0",
            "duration": 300880,
            "snipped": false,
            "format": {
              "protocol": "progressive",
              "mime_type": "audio/mpeg"
            },
            "quality": "sq"
          }
        ]
      },
      ......
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true
  }
}
```

返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (bool): 是否有下一页
   
items列表里项字段
   
  - `id` (string): youtube 视频id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 播放的iframe
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息
 
#
# `jamendo search`


支持的url
```bash
https://www.jamendo.com/search/tracks?q=linkin%20park

没有其他参数，也没有翻页功能，最多返回100条结果
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "820614",
        "title": "Numb-Linkin Park  plays-pianoraf",
        "publishedAt": "2011-08-01 13:15:29",
        "thumbnail": "https://cdn-img.jamendo.com/albums/s95/95964/covers/1.300.jpg",
        "description": "",
        "url": "https://www.jamendo.com/track/820614",
        "player": "<audio controls=\"controls\" style=\"position: relative;margin: 0 auto;display: table;z-index: 10;height: 80px;\" src=\"https://mp3l.jamendo.com/?trackid=820614&format=mp31&from=Iw8PpaA0OBcsQ6wEYWgIaQ%3D%3D%7CdCwNu6G%2FOJHaUrP4frgSow%3D%3D\" autoplay=\"\"></audio>",
        "duration": "02:18",
        "viewCount": "",
        "media": {
          "mp3": "https://mp3d.jamendo.com/download/track/820614/mp32/",
          "ogg": "https://ogg.jamendo.com/download/track/820614/ogg1/"
        }
      },
      ......
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true
  }
}
```

返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (bool): 是否有下一页
   
items列表里项字段
   
  - `id` (string): youtube 视频id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 播放的audio
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息
  
  
#
# `archive.org search`


支持的url
```bash
https://archive.org/search.php?query=hello&cate_id=1
https://archive.org/search.php?query=hello&cate_id=2&page=2

cate_id参数, 1=music, 2=video
page参数, 不传递的默认为1, 最多返回10页
参数顺序要query > cate_id > page顺序
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "HelloHelloHello",
        "title": "hello hello hello",
        "publishedAt": "2010-08-26 06:39:12",
        "thumbnail": "https://archive.org/services/img/HelloHelloHello",
        "description": "This is a podcast about hello",
        "url": "https://archive.org/details/HelloHelloHello",
        "player": "<iframe src=\"https://archive.org/embed/HelloHelloHello\" width=\"500\" height=\"140\" frameborder=\"0\" webkitallowfullscreen=\"true\" mozallowfullscreen=\"true\" allowfullscreen></iframe>",
        "duration": "",
        "viewCount": "",
        "media": null
      },
      ......
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true
  }
}
```

返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (bool): 是否有下一页
   
items列表里项字段
   
  - `id` (string): youtube 视频id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 播放的iframe
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息(忽略)
  
  
#
# `4shared search`


支持的url
```bash
https://www.4shared.com/web/q/#query=my+december&cate_id=1
https://www.4shared.com/web/q/#query=my+december&cate_id=1&page=2

cate_id参数, 1=music, 2=video
page参数, 不传递的默认为1，最多返回10页
参数顺序要query > cate_id > page顺序
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "YvBGcUXq",
        "title": "My Heart.mp3",
        "publishedAt": "2012-01-06 13:16:43",
        "thumbnail": "",
        "description": "",
        "url": "https://www.4shared.com/mp3/YvBGcUXq/My_Heart.html",
        "player": "<iframe src=\"https://www.4shared.com/web/embed/audio/file/YvBGcUXq?type=NORMAL&widgetWidth=530&showArtwork=true&playlistHeight=0&widgetRid=685337195355\" style=\"overflow:hidden;height:152px;width:530px;border: 0;margin:0;\"></iframe>",
        "duration": "05:23",
        "viewCount": "",
        "media": null
      },
      ......
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true
  }
}
```

返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (bool): 是否有下一页
   
items列表里项字段
   
  - `id` (string): youtube 视频id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 播放的iframe
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息(忽略)
  
  
  
# `基于youtube搜索结果的页面解析`


传递的url
```bash
https://www.youtube.com/watch?v=loOWKm8GW6A
详情页url即可
```


返回json格式
```bash
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "twenty one pilots - Level of Concern (Official Video)",
      "thumbnail": "https://i.ytimg.com/vi/loOWKm8GW6A/maxresdefault.jpg",
      "duration": "03:52",
      "view_count": "24M"
    },
    "audios": [
      {
        "ext": "MP3",
        "fileSize": "4.0M",
        "url": "https://r4---sn-vgqs7nl7.googlevideo.com/videoplayback?expire=1588928422&ei=Rsu0XpLsL4G0DdiDlIgP&ip=2001%3A19f0%3A5c01%3A51c%3A5400%3A1ff%3Afe37%3Ad11f&id=o-ANOUt0coIboqPTiBGOtuAmgNAC7u5NE8QHEjX_Xg9B6V&itag=251&source=youtube&requiressl=yes&mh=lo&mm=31%2C29&mn=sn-vgqs7nl7%2Csn-vgqskn7l&ms=au%2Crdu&mv=m&mvi=3&pl=52&initcwndbps=413750&vprv=1&mime=audio%2Fwebm&gir=yes&clen=3880554&dur=232.261&lmt=1586555268330831&mt=1588906718&fvip=4&keepalive=yes&c=WEB&txp=5531432&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALrAebAwRAIgJTxaN35Lwegyg_iFgjmAZkl1aKl2ghEh5Grf0CoMo-ICIF14ORAAkQiFKeY1fSDBptWejtrEmDTW-vSKcnrD4ql9&sig=AJpPlLswRQIhAKu9BOPDM1_valI0xUPoHrsFliTe9WZnx9l-zW_LMeGaAiBaEnwou2XnWouZnD7YzDLXtctDmWdN9C2xH6TBpeahOw==&ratebypass=yes",
        "formatNote": "320k",
        "hd": true,
        "pro": true
      },
      ......
    ],
    "videos": [
      {
        "ext": "mp4",
        "fileSize": "98M",
        "url": "https://r4---sn-vgqs7nl7.googlevideo.com/videoplayback?expire=1588928422&ei=Rsu0XpLsL4G0DdiDlIgP&ip=2001%3A19f0%3A5c01%3A51c%3A5400%3A1ff%3Afe37%3Ad11f&id=o-ANOUt0coIboqPTiBGOtuAmgNAC7u5NE8QHEjX_Xg9B6V&itag=137&aitags=133%2C134%2C135%2C136%2C137%2C160%2C242%2C243%2C244%2C247%2C248%2C278%2C394%2C395%2C396%2C397%2C398%2C399&source=youtube&requiressl=yes&mh=lo&mm=31%2C29&mn=sn-vgqs7nl7%2Csn-vgqskn7l&ms=au%2Crdu&mv=m&mvi=3&pl=52&initcwndbps=413750&vprv=1&mime=video%2Fmp4&gir=yes&clen=103009270&dur=232.231&lmt=1586556525048331&mt=1588906718&fvip=4&keepalive=yes&c=WEB&txp=5535432&sparams=expire%2Cei%2Cip%2Cid%2Caitags%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALrAebAwRAIgJTxaN35Lwegyg_iFgjmAZkl1aKl2ghEh5Grf0CoMo-ICIF14ORAAkQiFKeY1fSDBptWejtrEmDTW-vSKcnrD4ql9&sig=AJpPlLswRQIhAI1Gncs2yD5xC_Q9cuMpCPcB-zE0E7FyLpK8uDqBm8CJAiBefbrGxiOM7w47l9jLYM0iM8eb0iupynApzeTKqtYPEg==&ratebypass=yes",
        "formatNote": "1080p",
        "orgin_audio_url": "https://r4---sn-vgqs7nl7.googlevideo.com/videoplayback?expire=1588928422&ei=Rsu0XpLsL4G0DdiDlIgP&ip=2001%3A19f0%3A5c01%3A51c%3A5400%3A1ff%3Afe37%3Ad11f&id=o-ANOUt0coIboqPTiBGOtuAmgNAC7u5NE8QHEjX_Xg9B6V&itag=140&source=youtube&requiressl=yes&mh=lo&mm=31%2C29&mn=sn-vgqs7nl7%2Csn-vgqskn7l&ms=au%2Crdu&mv=m&mvi=3&pl=52&initcwndbps=413750&vprv=1&mime=audio%2Fmp4&gir=yes&clen=3760142&dur=232.292&lmt=1586555267594557&mt=1588906718&fvip=4&keepalive=yes&c=WEB&txp=5531432&sparams=expire%2Cei%2Cip%2Cid%2Citag%2Csource%2Crequiressl%2Cvprv%2Cmime%2Cgir%2Cclen%2Cdur%2Clmt&lsparams=mh%2Cmm%2Cmn%2Cms%2Cmv%2Cmvi%2Cpl%2Cinitcwndbps&lsig=ALrAebAwRAIgJTxaN35Lwegyg_iFgjmAZkl1aKl2ghEh5Grf0CoMo-ICIF14ORAAkQiFKeY1fSDBptWejtrEmDTW-vSKcnrD4ql9&sig=AJpPlLswRQIgMs32TS7NYWeilLH8xopE9QEV4oJzC0Jj6WHdzKCTnYsCIQDLHG9tP5izlBR50YwEBGp3WoXwZCL2neJKbQ83sozCeQ==&ratebypass=yes",
        "audio_exist": false,
        "hd": true,
        "pro": true,
        "vcodec": "avc1.640028"
      },
      ......
    ]
  }
}
```

返回字段

 - `info` (dict): 该详情页相关信息
 - `audios` (list): 音频信息列表
 - `videos` (list): 视频信息列表


## `直接搜索youtube详情页地址的解析`

传递的url
```bash
https://www.youtube.com/watch?v=loOWKm8GW6A&AmoyShareSearch=1

详情页url+&AmoyShareSearch=1
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "loOWKm8GW6A",
        "title": "twenty one pilots - Level of Concern (Official Video)",
        "publishedAt": "",
        "thumbnail": "https://i.ytimg.com/vi/loOWKm8GW6A/maxresdefault.jpg",
        "description": "",
        "url": "https://www.youtube.com/watch?v=loOWKm8GW6A",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://www.amoyshare.com/player/?v=loOWKm8GW6A&watch=1588920286\"></iframe>",
        "format": "video"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略


# `基于soundcloud搜索结果的页面解析`


传递的url
```bash
https://soundcloud.com/gracedaviesofficial/hello-adele

详情页url即可
```

返回json格式
```bash
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Hello - Adele",
      "thumbnail": "https://i1.sndcdn.com/artworks-000134001026-tugyco-original.jpg",
      "duration": "05:00",
      "view_count": "62M"
    },
    "audios": [
      {
        "ext": "MP3",
        "fileSize": "--",
        "url": "https://cf-media.sndcdn.com/4axwr3aUKixa.128.mp3?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiKjovL2NmLW1lZGlhLnNuZGNkbi5jb20vNGF4d3IzYVVLaXhhLjEyOC5tcDMiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE1ODg5MTUyNDB9fX1dfQ__&Signature=D0R97uLJ-quREW7dwBZEdMl2A5eDj1VsS9lIwxw20Lb2v7KoKQBnncv9mrMJ4cBg3cFV18Qqt8esqh9xnsVDRtiJFsdssW-OHQr17SW-jyUNA38bda-Z7FaJyZlUB~ICR6fN8W1xcqNS9CPy6Lew8fJsp6f33Z6rTWOcA6jsvUFu0tgKkvhGrSa6RxtmkeDdcX4JuTT2tP-mynUZUpYnoQUv020dimg2yQBg9H06-E3Im6wnlSeFK9ce6DpSFUtR~w~sZU4Guzskg5b04Ja4kR0EkKG5T5Msxzy6auHTeySybWlQxxe3yAjqnQ3sso1fdxsvxllFyJ77ACiVEjDzrg__&Key-Pair-Id=APKAI6TU7MMXM5DG6EPQ",
        "formatNote": "320k",
        "hd": true,
        "pro": true
      },
      ......
    ],
    "videos": []
  }
}
```

返回字段

 - `info` (dict): 该详情页相关信息
 - `audios` (list): 音频信息列表
 - `videos` (list): 视频信息列表
 

## `直接搜索soundcloud详情页地址的解析`

传递的url
```bash
https://soundcloud.com/gracedaviesofficial/hello-adele&AmoyShareSearch=1

详情页url+&AmoyShareSearch=1
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "https://soundcloud.com/gracedaviesofficial/hello-adele",
        "title": "Hello - Adele",
        "publishedAt": "",
        "thumbnail": "https://i1.sndcdn.com/artworks-000134001026-tugyco-original.jpg",
        "description": "",
        "url": "https://soundcloud.com/gracedaviesofficial/hello-adele",
        "player": "<audio controls=\"controls\" style=\"position: relative;margin: 0 auto;display: table;z-index: 10;height: 80px;\" src=\"https://cf-media.sndcdn.com/4axwr3aUKixa.128.mp3?Policy=eyJTdGF0ZW1lbnQiOlt7IlJlc291cmNlIjoiKjovL2NmLW1lZGlhLnNuZGNkbi5jb20vNGF4d3IzYVVLaXhhLjEyOC5tcDMiLCJDb25kaXRpb24iOnsiRGF0ZUxlc3NUaGFuIjp7IkFXUzpFcG9jaFRpbWUiOjE1ODg5MTc1OTF9fX1dfQ__&Signature=RyKDT0D4q~yc7dabpkeEzh9gJ218BlTpU3whR5IHBPTEtqkw5ZCShiJjnRnKCchVbXbg7Aw1C1tcDdQoMxjhHHxhpo60BIH8BOP5xot6o4Btns-QU60u7goeGRFpCwdo6sK8ND6VfRxoUX8nPxvlsbkOBqHwMl-TTm6g8kZ9lpvCP0hdEoUUA7NB1-~VPvT-lRNXzww-gCoxHm5paOJ68coUBOaLX7fG5EBOwVpIlGWhbcn5s5D12B0NjpJ3N2n6AKWOx6JC-uG8slB0Omm4bYllSnz~gXyX~eIz3RyHfPCSVZSW~efz~ryGalnpwi5wrlvMppckWN0wTopGHRT6ww__&Key-Pair-Id=APKAI6TU7MMXM5DG6EPQ\" autoplay=\"\"></audio>",
        "format": "audio"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略
 

## `基于jamendo搜索结果的页面解析`

传递的url
```bash
https://www.jamendo.com/track/820614

详情页url即可
```

返回json格式
```bash
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "info": {
      "title": "pianoraf - Numb-Linkin Park  plays-pianoraf",
      "thumbnail": "https://cdn-img.jamendo.com/albums/s95/95964/covers/1.600.jpg?du=1535683629",
      "duration": "02:18",
      "view_count": "222K"
    },
    "audios": [
      {
        "ext": "MP3",
        "fileSize": "--",
        "url": "https://flac.jamendo.com/?trackid=820614&format=flac&from=app-97dab294",
        "formatNote": "320k",
        "hd": true,
        "pro": true
      },
      ......
    ],
    "videos": []
  }
}
```

返回字段

 - `info` (dict): 该详情页相关信息
 - `audios` (list): 音频信息列表
 - `videos` (list): 视频信息列表
 

## `直接搜索jamendo详情页地址的解析`

传递的url
```bash
https://www.jamendo.com/track/820614&AmoyShareSearch=1

详情页url+&AmoyShareSearch=1
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "https://www.jamendo.com/track/820614",
        "title": "pianoraf - Numb-Linkin Park  plays-pianoraf",
        "publishedAt": "",
        "thumbnail": "https://cdn-img.jamendo.com/albums/s95/95964/covers/1.600.jpg?du=1535683629",
        "description": "",
        "url": "https://www.jamendo.com/track/820614",
        "player": "<audio controls=\"controls\" style=\"position: relative;margin: 0 auto;display: table;z-index: 10;height: 80px;\" src=\"https://mp3d.jamendo.com/?trackid=820614&format=mp32&from=app-97dab294\" autoplay=\"\"></audio>",
        "format": "audio"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略


# `基于archive.org搜索结果的页面解析`

传递的url
```bash
https://archive.org/details/Enya-Anywhere_Is.MPG
https://archive.org/details/HelloGoodbye_201312

详情页url即可
```


返回json格式
```bash
视频
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Enya Anywhere Is.MPG",
      "thumbnail": "http://ia600806.us.archive.org/29/items/Enya-Anywhere_Is.MPG/Enya-Anywhere_Is.MPG.thumbs/Enya-Anywhere_Is_000001.jpg",
      "duration": "03:53",
      "view_count": ""
    },
    "audios": [],
    "videos": [
      {
        "ext": "mp4",
        "fileSize": "23M",
        "url": "https://ia600806.us.archive.org/29/items/Enya-Anywhere_Is.MPG/Enya-Anywhere_Is.mp4",
        "formatNote": "480p",
        "orgin_audio_url": "",
        "audio_exist": false,
        "hd": false,
        "pro": false,
        "vcodec": "hkd.av01"
      }
    ]
  }
}

音频
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Hello Goodbye Oh Hello",
      "thumbnail": "http://ia800908.us.archive.org/34/items/HelloGoodbye_201312/Hello_Goodbye.png",
      "duration": "55:49",
      "view_count": ""
    },
    "audios": [
      {
        "ext": "MP3",
        "fileSize": "--",
        "url": "https://ia800908.us.archive.org/34/items/HelloGoodbye_201312/Hello_Goodbye.mp3",
        "formatNote": "320k",
        "hd": true,
        "pro": true
      },
      ......
    ],
    "videos": []
  }
}
```

返回字段

 - `info` (dict): 该详情页相关信息
 - `audios` (list): 音频信息列表
 - `videos` (list): 视频信息列表


## `直接搜索archive.org详情页地址的解析`

传递的url
```bash
https://archive.org/details/Enya-Anywhere_Is.MPG&AmoyShareSearch=1
https://archive.org/details/HelloGoodbye_201312&AmoyShareSearch=1

详情页url+&AmoyShareSearch=1
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "https://archive.org/details/Enya-Anywhere_Is.MPG",
        "title": "Enya Anywhere Is.MPG",
        "publishedAt": "",
        "thumbnail": "http://ia600806.us.archive.org/29/items/Enya-Anywhere_Is.MPG/Enya-Anywhere_Is.MPG.thumbs/Enya-Anywhere_Is_000001.jpg",
        "description": "",
        "url": "https://archive.org/details/Enya-Anywhere_Is.MPG",
        "player": "<video controls=\"\" autoplay=\"\" name=\"media\" width=\"100%\" height=\"100%\"><source src=\"https://ia800806.us.archive.org/29/items/Enya-Anywhere_Is.MPG/Enya-Anywhere_Is.mp4\" type=\"video/mp4\"></video>",
        "format": "video"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略


# `基于4shared.com搜索结果的页面解析`


传递的url
```bash
https://www.4shared.com/mp3/B3arrz-wei/AUD-20180312-WA0021.html
https://www.4shared.com/video/qp8_EQ4L/My_December_AMV.html

详情页url即可
```

返回json格式
```bash
音频
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "AUD-20180312-WA0021 ",
      "thumbnail": "https://dc407.4shared.com/img/B3arrz-wei/s22/162b8171418/AUD-20180312-WA0021",
      "duration": "",
      "view_count": ""
    },
    "audios": [
      {
        "ext": "MP3",
        "fileSize": "--",
        "url": "https://dc407.4shared.com/img/B3arrz-wei/4de25be6/dlink__2Fdownload_2FB3arrz-wei_2FAUD-20180312-WA0021.mp3_3Fsbsr_3D26e2e0f355b1aa7dc0e7c78b2758950ba43_26bip_3DNDUuNzYuMjYuNDY_26lgfp_3D52_26bip_3DNDUuNzYuMjYuNDY/preview.mp3",
        "formatNote": "320k",
        "hd": true,
        "pro": true
      },
      ......
    ],
    "videos": []
  }
}

视频
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "My December AMV ",
      "thumbnail": "",
      "duration": "",
      "view_count": ""
    },
    "audios": [],
    "videos": [
      {
        "ext": "mp4",
        "fileSize": "476K",
        "url": "https://dc338.4shared.com/img/qp8_EQ4L/2dd0978a/dlink__2Fdownload_2Fqp8_5FEQ4L_3Fsbsr_3D5cd5228532426bd1d94765c661817c59a43_26bip_3DNDUuNzYuMjYuNDY_26lgfp_3D20_26bip_3DNDUuNzYuMjYuNDY_26bip_3DNDUuNzYuMjYuNDY/preview.mp4",
        "formatNote": "--",
        "orgin_audio_url": "",
        "audio_exist": false,
        "hd": false,
        "pro": false,
        "vcodec": "hkd.av01"
      }
    ]
  }
}
```

返回字段

 - `info` (dict): 该详情页相关信息
 - `audios` (list): 音频信息列表
 - `videos` (list): 视频信息列表


## `直接搜索4shared.com详情页地址的解析`

传递的url
```bash
https://www.4shared.com/mp3/B3arrz-wei/AUD-20180312-WA0021.html&AmoyShareSearch=1
https://www.4shared.com/video/qp8_EQ4L/My_December_AMV.html&AmoyShareSearch=1

详情页url+&AmoyShareSearch=1
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "https://www.4shared.com/mp3/B3arrz-wei/AUD-20180312-WA0021.html",
        "title": "AUD-20180312-WA0021 ",
        "publishedAt": "",
        "thumbnail": "https://dc621.4shared.com/img/B3arrz-wei/s22/162b8171418/AUD-20180312-WA0021",
        "description": "",
        "url": "https://www.4shared.com/mp3/B3arrz-wei/AUD-20180312-WA0021.html",
        "player": "<audio controls=\"controls\" style=\"position: relative;margin: 0 auto;display: table;z-index: 10;height: 80px;\" src=\"https://dc407.4shared.com/img/B3arrz-wei/4de25be6/dlink__2Fdownload_2FB3arrz-wei_2FAUD-20180312-WA0021.mp3_3Fsbsr_3D26e2e0f355b1aa7dc0e7c78b2758950ba43_26bip_3DNDUuNzYuMjYuNDY_26lgfp_3D52_26bip_3DNDUuNzYuMjYuNDY/preview.mp3\" autoplay=\"\"></audio>",
        "format": "audio"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略
 

## `其余支持直接搜索详情页地址的解析`

支持的url
```bash
https://video.foxnews.com/v/6146553357001#sp=show-clips
https://www.youtube.com/watch?v=JoJ_61KdSCg
https://vimeo.com/352492210
https://www.dailymotion.com/video/x76iqsk
https://www.tiktok.com/@rambunk/video/6723268025371413765?langCountry=zh_Hant
https://www.facebook.com/watch/?v=10155986324237112
https://www.instagram.com/p/Bp8y8LZFtPj/
https://soundcloud.com/liltjay/f-n
http://ironlungpv.bandcamp.com/track/exiled
https://www.mixcloud.com/tarqeeb/juggernaut-027-tarqeeb-19-07-2019/
https://audiomack.com/song/jackharlow/thru-the-night
https://www.jamendo.com/track/659892/lost-hope
https://www.pornhub.com/view_video.php?viewkey=ph5d55733e75985
https://www.xvideos.com/video1935740/creampie_asian_slut_gets_fucked
https://xhamster.com/videos/thick-mature-sara-jay-fucked-by-black-cock-babe-imani-rose-12377139
https://www.xnxx.com/video-hsuor96/mofos_-_stranded_teens_-_blonde_housewifes_huge_boobs_starring_kyra_hot
https://www.youporn.com/watch/12254691/amateur-redhead-riding-my-dick
https://www.redtube.com/605979
https://www.nicovideo.jp/watch/sm35571473
https://www.1tv.ru/shows/eksklyuziv/vypuski/habib-nurmagomedov-est-pravila-igry-a-est-pravila-chesti-eksklyuziv-vypusk-ot-13-10-2018
http://www.vlive.tv/video/140828
https://www.newgrounds.com/portal/view/739252
https://www.gameinformer.com/exclusive-video/2019/10/09/game-freak-explains-everything-about-sobble-from-pokemon-sword-and
https://video.nationalgeographic.com/video/animals-source/wild-life-with-bertie-gregory/0000016b-d86b-d83c-affb-fc7f106c0000
https://video.nationalgeographic.com/video/magazine/decoder/0000016c-4976-d982-a7ff-f977eb3b0000
https://www.lynda.com/PHP-tutorials/Welcome/133321/180281-4.html
https://www.aol.com/video/playlist/PL10528/5da0e2b710ca044b5ad51deb/
https://www.cbsnews.com/video/u-s-withdraws-1000-troops-from-northern-syria-leaving-kurds-to-fight-turkish-soldiers-alone/
https://www.abc.net.au/news/2019-10-13/building-under-construction-collapses-in-new-orleans/11597754
https://www.liveleak.com/view?t=arffn_1566414533
https://gfycat.com/distantexemplaryabyssiniangroundhornbill
https://www.ted.com/talks/nancy_lublin_crisis_support_for_the_world_one_text_away
https://www.youtube.com/watch?v=ADD7hqnmO4E&feature=youtu.be
https://tv.naver.com/v/12673935
https://m.imdb.com/video/vi615824921?pf_rd_r=KKZ2THC8SXTQ8VHYH5ZJ&pf_rd_p=55c313b3-794b-4543-8e47-45553f284702&pf_rd_m=A2FGELUUNOQJNL&pf_rd_t=15061&pf_rd_i=home&pf_rd_s=featured-today-2&ref_=hm_edcft_mobi_ss_ep1_2&listId=ls025720609
https://www.gamestar.de/videos/marauder-crowdfunding-trailer-zum-weltraumpiraten-shooter,100531.html
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "",
        "title": "",
        "publishedAt": "",
        "thumbnail": "",
        "description": "",
        "url": "",
        "player": "",
        "format": ""
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```

返回字段

 - `items` (list): 该详情页相关信息列表(固定只有一个结果)
 - `nextPageToken` (string): 忽略
 - `prevPageToken` (string): 忽略
 - `is_next_page` (string): 忽略
 

# `instagram user, hashtag, location 搜索列表页`

支持的url
```bash
https://www.instagram.com/karliekloss/                               ---> user
https://www.instagram.com/explore/tags/happynewyear/                 ---> tag
https://www.instagram.com/explore/locations/212988663/happynewyear/  ---> location
https://www.instagram.com/explore/locations/212988663/               ---> location
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "CBDuRmQDNeV",
        "title": "",
        "publishedAt": "2020-06-05",
        "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/sh0.08/e35/c7.0.1212.1212a/s640x640/101826699_178109750298173_3008888143440262581_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=ZoTp7AKSzzcAX_n-fDs&oh=b36b3eccfa3b2998f2f7f30f024501bb&oe=5F09E796",
        "description": "Today would have been Breonna Taylor\u2019s 27th birthday. A celebration and life stripped away when the police wrongfully broke into her house, riddling her with bullets in March. Breonna was an EMT, an essential worker during a time of crisis, a friend, a daughter and so much more. Breonna never got to experience her 27th trip around the sun and those responsible for her murder still walk freely. Honor Breonna and demand justice for her and her family. Text ENOUGH to 55156 #SayHerName",
        "url": "https://instagram.com/p/CBDuRmQDNeV/",
        "player": "<blockquote class=\"instagram-media\" data-instgrm-captioned\n            data-instgrm-permalink=\"https://instagram.com/p/CBDuRmQDNeV/?utm_source=ig_embed&utm_campaign=loading\"\n            data-instgrm-version=\"12\"\n            style=\" background:#FFF; border:0; border-radius:3px; \n            box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);\">\n        </blockquote>\n        <script async src=\"//www.instagram.com/embed.js\"></script>",
        "format": "sidecar",
        "duration": "",
        "viewCount": "",
        "media": null
      },
      {
        "id": "CA6-2XujgKS",
        "title": "",
        "publishedAt": "2020-06-02",
        "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/sh0.08/e35/s640x640/77038634_298471324514573_8263274942945294416_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=EF6J214d79kAX8BulSG&oh=36adb20c3edf06755e6d6b2577cd124e&oe=5F0821FE",
        "description": "Black Lives Matter",
        "url": "https://instagram.com/p/CA6-2XujgKS/",
        "player": "<blockquote class=\"instagram-media\" data-instgrm-captioned\n            data-instgrm-permalink=\"https://instagram.com/p/CA6-2XujgKS/?utm_source=ig_embed&utm_campaign=loading\"\n            data-instgrm-version=\"12\"\n            style=\" background:#FFF; border:0; border-radius:3px; \n            box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);\">\n        </blockquote>\n        <script async src=\"//www.instagram.com/embed.js\"></script>",
        "format": "image",
        "duration": "",
        "viewCount": "",
        "media": null
      },
      {
        "id": "CAtXV6-gkxK",
        "title": "",
        "publishedAt": "2020-05-28",
        "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/sh0.08/e35/c0.90.720.720a/s640x640/100975157_2747153318848370_7485398932446714644_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=102&_nc_ohc=exmWIkC8R8YAX8aOCi1&oh=66d81c9c0e040d000cc77574b6ce05c5&oe=5EE15237",
        "description": "Reminder: treat yourself today \ud83d\ude43",
        "url": "https://instagram.com/p/CAtXV6-gkxK/",
        "player": "<blockquote class=\"instagram-media\" data-instgrm-captioned\n            data-instgrm-permalink=\"https://instagram.com/p/CAtXV6-gkxK/?utm_source=ig_embed&utm_campaign=loading\"\n            data-instgrm-version=\"12\"\n            style=\" background:#FFF; border:0; border-radius:3px; \n            box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);\">\n        </blockquote>\n        <script async src=\"//www.instagram.com/embed.js\"></script>",
        "format": "video",
        "duration": "",
        "viewCount": "567K",
        "media": null
      },
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": true,
    "next_page": "https://www.instagram.com/graphql/query/?query_hash=42323d64886122307be10013ad2dcc44&variables={"first": 20, "after": "QVFEZWJoMG9mTnkwbXowNGs1U2Fuc3NSNXgzX1M0RFNDNDhqVnlVVENIbnNpN1BoeVRqX0pJZXFXNjJPdGFtX0VKMDBtSTNNNzhuNklDS2pja3hUejlydA==", "id": "10581097"}&category=user"
  }
}
```
        
返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (boolean): 是否有下一页
 - `next_page` (string): 下一页url，没有则值为null
   
items列表里项字段
   
  - `id` (string): instagram id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 预览的embed链接
  - `format` (string): 资源类型video, image, sidecar(video和image混合)
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息(忽略)

# `instagram image, video, sidecar，igtv 详情页解析`

支持的url
```bash
https://www.instagram.com/p/CA6-2XujgKS/            ---> image
https://www.instagram.com/p/CAtXV6-gkxK/            ---> video
https://www.instagram.com/p/CBBQMRqD7Pj/            ---> sidecar
https://www.instagram.com/tv/B-ztbtZFowP/           ---> igtv
```

返回json格式
```bash
image
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Image by karliekloss",
      "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/e35/s1080x1080/77038634_298471324514573_8263274942945294416_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=EF6J214d79kAX8BulSG&oh=8e4c75cbed046c531af40738dfaf4ba2&oe=5F09DE4B",
      "description": "Black Lives Matter",
      "duration": "",
      "view_count": ""
    },
    "subtitles": [],
    "audios": [],
    "videos": [],
    "images": [
      {
        "url": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/e35/s1080x1080/77038634_298471324514573_8263274942945294416_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=EF6J214d79kAX8BulSG&oh=8e4c75cbed046c531af40738dfaf4ba2&oe=5F09DE4B",
        "height": 1080,
        "width": 1080,
        "ext": "JPG",
        "fileSize": "--",
        "formatNote": "1080p"
      }
    ],
    "sidecars": []
  }
}

video | igtv
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Video by karliekloss",
      "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/sh0.08/e35/c0.90.720.720a/s640x640/100975157_2747153318848370_7485398932446714644_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=102&_nc_ohc=exmWIkC8R8YAX8aOCi1&oh=b804004acc00104c440b2dcaf420894a&oe=5EE2A3B7",
      "description": "Reminder: treat yourself today \ud83d\ude43",
      "duration": "",
      "view_count": ""
    },
    "subtitles": [],
    "audios": [],
    "videos": [
      {
        "ext": "MP4",
        "fileSize": "--",
        "url": "https://scontent-ort2-1.cdninstagram.com/v/t50.2886-16/101424709_148146440107498_8341823680979503679_n.mp4?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=110&_nc_ohc=28SLwxhX4NUAX9onMWw&oe=5EE26215&oh=67c6d8c654bfa6b84c6ba5b3a92f412b",
        "formatNote": "937p",
        "orgin_audio_url": "",
        "audio_exist": true,
        "hd": true,
        "pro": true,
        "vcodec": "--"
      }
    ],
    "images": [],
    "sidecars": []
  }
}

sidecar
{
  "code": {
    "error": "0000",
    "msg": "call success"
  },
  "data": {
    "info": {
      "title": "Sidecar by karliekloss",
      "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/e35/101835975_143675143943609_2697646007936050338_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=ms2SGhL5k4UAX-ePWe6&oh=e010a99cb80d86f402ba3b079e82f72c&oe=5EE2ABD7",
      "description": "My hometown of St. Louis is in the top 5 for cities whose police departments kill black men at higher rates than the US murder rate. This is unacceptable. The policies listed here can be changed immediately if we all flood our mayors offices with calls demanding change. I urge you to join me in making these calls. #8cantwait",
      "duration": "",
      "view_count": ""
    },
    "subtitles": [],
    "audios": [],
    "videos": [],
    "images": [],
    "sidecars": [
      {
        "ext": "MP4",
        "fileSize": "--",
        "url": "https://scontent-ort2-1.cdninstagram.com/v/t50.2886-16/101620116_281647109884773_2693955700176252676_n.mp4?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=109&_nc_ohc=dN3C2povLHcAX9Hw4h2&oe=5EE26485&oh=b32a9ea89382bb11cb42fee3fc627e2b",
        "formatNote": "750p",
        "orgin_audio_url": "",
        "audio_exist": true,
        "hd": true,
        "pro": true,
        "vcodec": "--"
      },
      {
        "url": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/e35/s1080x1080/101543753_180150910066208_5443099396458379120_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=108&_nc_ohc=jUFbHeIOkssAX_YIQAo&oh=fcf2aecf96704a7be0a22bfc9ab2ccba&oe=5F08B336",
        "width": 1080,
        "height": 1080,
        "ext": "JPG",
        "fileSize": "--",
        "formatNote": "1080p"
      },
      ......
    ]
  }
}
```
        
返回字段

 - `info` (dict): 该链接相关信息
 - `audios` (list): 忽略
 - `videos` (list): 视频信息列表
 - `images` (list): 图片信息列表
 - `sidecars` (list): 视频或图片混合信息列表
   
images列表里项字段
   
  - `url` (string): 下载链接
  - `height` (string): 高
  - `width` (string): 宽
  - `ext` (string): 格式
  - `fileSize` (string): 忽略
  - `formatNote` (string): 最大像素
  
videos列表里项字段
   
  - `ext` (string): 格式
  - `fileSize` (string): 忽略
  - `url` (string): 下载链接
  - `formatNote` (string): 最大像素
  - `orgin_audio_url` (string): 忽略
  - `audio_exist` (boolean): 忽略
  - `hd` (boolean): 忽略
  - `pro` (boolean): 忽略
  - `vcodec` (string): 忽略
  
sidecars列表里项字段

  - 参阅image和video项字段处理结果
  
  
# `instagram image, video, sidecar，igtv 详情页搜索`

支持的url
```bash
https://www.instagram.com/p/CA6-2XujgKS/            ---> image
https://www.instagram.com/p/CAtXV6-gkxK/            ---> video
https://www.instagram.com/p/CBBQMRqD7Pj/            ---> sidecar
https://www.instagram.com/tv/B-ztbtZFowP/           ---> igtv
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "https://www.instagram.com/p/CBBQMRqD7Pj/",
        "title": "Sidecar by karliekloss",
        "viewCount": "",
        "duration": "",
        "thumbnail": "https://scontent-ort2-1.cdninstagram.com/v/t51.2885-15/e35/101835975_143675143943609_2697646007936050338_n.jpg?_nc_ht=scontent-ort2-1.cdninstagram.com&_nc_cat=105&_nc_ohc=ms2SGhL5k4UAX-ePWe6&oh=e010a99cb80d86f402ba3b079e82f72c&oe=5EE2ABD7",
        "description": "My hometown of St. Louis is in the top 5 for cities whose police departments kill black men at higher rates than the US murder rate. This is unacceptable. The policies listed here can be changed immediately if we all flood our mayors offices with calls demanding change. I urge you to join me in making these calls. #8cantwait",
        "url": "https://www.instagram.com/p/CBBQMRqD7Pj/",
        "player": "<blockquote class=\"instagram-media\" data-instgrm-captioned\n                    data-instgrm-permalink=\"https://www.instagram.com/p/CBBQMRqD7Pj/?utm_source=ig_embed&utm_campaign=loading\"\n                    data-instgrm-version=\"12\"\n                    style=\" background:#FFF; border:0; border-radius:3px; \n                    box-shadow:0 0 1px 0 rgba(0,0,0,0.5),0 1px 10px 0 rgba(0,0,0,0.15); margin: 1px; max-width:658px; min-width:326px; padding:0; width:99.375%; width:-webkit-calc(100% - 2px); width:calc(100% - 2px);\">\n                </blockquote>\n                <script async src=\"//www.instagram.com/embed.js\"></script>",
        "format": "sidecar"
      }
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false
  }
}
```
        
返回字段

 - `items` (list): 返回的搜索结果列表
   
items列表里项字段
   
  - `id` (string): instagram id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 预览的embed链接
  - `format` (string): 资源类型video, image, sidecar(video和image混合)
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  
  
  
  
# `pornhub youporn xhamster redtube xvideos xnxx 成人站关键字搜索`

支持的url
```bash
https://pornhub.com/video/search?search=my+home&o=mv&hd=1&t=m&page=2
https://www.youporn.com/search/views/?search-btn=&query=home
https://xhamster.com/search/kaley+cuoco+sex+tape?date=latest&min-duration=10&max-duration=30&page=2
https://www.redtube.com/mostviewed?search=black+guys+fucking+hard&category=anal&min_duration=11&max_duration=46&hd=1&page=2
https://www.xvideos.com/?k=sister+home+alone&sort=relevance&datef=month&durf=3-10min
https://www.xnxx.com/search/hits/month/10-20min/familial_relations
```

返回json格式
```bash
{
  "data": {
    "items": [
      {
        "id": "ph5ef3903fb896f",
        "title": "On Vacation with my Hot Step-Mom with Huge Tits",
        "publishedAt": "3 weeks ago",
        "thumbnail": "https://di.phncdn.com/videos/202006/24/326638082/original/(m=eafTGgaaaa)(mh=l-q7U1eknrvmrrxV)8.jpg",
        "description": null,
        "url": "https://www.pornhub.com/view_video.php?viewkey=ph5ef3903fb896f",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://www.pornhub.com/embed/ph5ef3903fb896f\"></iframe>",
        "format": "video",
        "duration": "8:17",
        "viewCount": "14.2K",
        "media": null
      },
      {
        "id": "9914589",
        "title": "Kaley Cuoco Compilation",
        "publishedAt": "2014-07-12",
        "thumbnail": "https://fi1.ypncdn.com/201407/12/9914589/original/8/kaley-cuoco-compilation-8(m=e8KSKgaaaa).jpg",
        "description": "",
        "url": "https://www.youporn.com/watch/9914589/kaley-cuoco-compilation/",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://www.youporn.com/embed/9914589/kaley-cuoco-compilation/\"></iframe>",
        "format": "video",
        "duration": "02:05",
        "viewCount": "",
        "media": null
      },
      {
        "id": "xhG3S7n",
        "title": "students want to study, but like sex better",
        "publishedAt": "",
        "thumbnail": "https://thumb-lvlt.xhcdn.com/a/prcD3lT6Y7Qi-uVNB_IIMg/015/344/454/240x135.2.jpg",
        "description": "",
        "url": "https://xhamster.com/videos/students-want-to-study-but-like-sex-better-xhG3S7n",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://xhamster.com/embed/xhG3S7n\"></iframe>",
        "format": "video",
        "duration": "12:00",
        "viewCount": "1K",
        "media": null
      },
      {
        "id": "2778766",
        "title": "Roxy getting fucked with three rock hard cocks",
        "publishedAt": "",
        "thumbnail": "https://ei.rdtcdn.com/m=eW0Q8f/media/videos/201801/03/2778766/original/10.jpg",
        "description": "Upox",
        "url": "https://www.redtube.com/2778766",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://embed.redtube.com/?id=2778766\"></iframe>",
        "format": "video",
        "duration": "12:00",
        "viewCount": "279K",
        "media": null
      },
      {
        "id": "56863379",
        "title": "Fucked My Step Sister In The Shower - Cold shower with my step sister while parents are not home",
        "publishedAt": "",
        "thumbnail": "https://img-hw.xvideos-cdn.com/videos/thumbs169ll/86/e3/0e/86e30e1e9282a4c57379821ffd8aa545/86e30e1e9282a4c57379821ffd8aa545.8.jpg",
        "description": "Lena Saritta",
        "url": "https://www.xvideos.com/video56863379/fucked_my_step_sister_in_the_shower_-_cold_shower_with_my_step_sister_while_parents_are_not_home",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://www.xvideos.com/embedframe/56863379\"></iframe>",
        "format": "video",
        "duration": "8 min",
        "viewCount": "97.6k",
        "media": null
      },
      {
        "id": "56736163",
        "title": "Xvideo",
        "publishedAt": "",
        "thumbnail": "https://img-l3.xnxx-cdn.com/videos/thumbs169xnxxll/c6/2d/6d/c62d6dc702756c95bcf5611a1c59e2ff/c62d6dc702756c95bcf5611a1c59e2ff.THUMBNUM.jpg",
        "description": "",
        "url": "https://www.xnxx.com/video-xs1wj81/THUMBNUM/xvideo",
        "player": "<iframe width=\"100%\" height=\"100%\" frameborder=\"0\" allowfullscreen src=\"https://www.xvideos.com/embedframe/56736163\"></iframe>",
        "format": "video",
        "duration": "11min",
        "viewCount": "18k",
        "media": null
      },
      .....
    ],
    "nextPageToken": null,
    "prevPageToken": null,
    "is_next_page": false,
    "next_page": "https://www.pornhub.com/video/search?search=my+home&o=mv&hd=1&t=m&page=3" "https://www.youporn.com/search/views/?query=home&page=2" "https://xhamster.com/search/kaley+cuoco+sex+tape?date=latest&min-duration=10&max-duration=30&page=3" "https://www.redtube.com/mostviewed?search=black+guys+fucking+hard&category=anal&min_duration=11&max_duration=46&hd=1&page=3" "https://www.xvideos.com/?k=sister+home+alone&datef=month&durf=3-10min&p=1" "https://www.xnxx.com/search/month/10-20min/familial_relations/1"
  }
}
```

返回字段

 - `items` (list): 返回的搜索结果列表
 - `is_next_page` (boolean): 是否有下一页
 - `next_page` (string): 下一页url，没有则没有此字段
   
items列表里项字段
   
  - `id` (string): id
  - `title` (string): 标题
  - `publishedAt` (string): 日期
  - `thumbnail` (string): 封面图
  - `description` (string): 简介
  - `url` (string): 详情页url
  - `player` (string): 预览的embed链接
  - `format` (string): 资源类型video, image
  - `duration` (string): 播放时长
  - `viewCount` (string): 浏览数
  - `media` (string): 资源信息(忽略)