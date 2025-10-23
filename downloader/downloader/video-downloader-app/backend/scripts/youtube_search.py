#!/usr/bin/env python3
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../downloader'))

try:
    from youtube_dl import YoutubeDL

    def search_youtube(query, page=1):
        search_url = f"https://www.youtube.com/results?search_query={query}&page={page}"

        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                result = ydl.extract_info(search_url, download=False)

                items = []
                if result and 'entries' in result:
                    for entry in result['entries'][:20]:
                        if entry:
                            items.append({
                                'id': entry.get('id', ''),
                                'title': entry.get('title', ''),
                                'thumbnail': entry.get('thumbnail', ''),
                                'url': f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                                'duration': entry.get('duration_string', ''),
                                'view_count': entry.get('view_count', ''),
                                'description': entry.get('description', '')[:200]
                            })

                return {
                    'data': {
                        'items': items,
                        'is_next_page': len(items) >= 20
                    }
                }
            except Exception as e:
                return {
                    'error': str(e),
                    'data': {
                        'items': [],
                        'is_next_page': False
                    }
                }

    if __name__ == '__main__':
        query = sys.argv[1] if len(sys.argv) > 1 else 'hello'
        page = int(sys.argv[2]) if len(sys.argv) > 2 else 1

        result = search_youtube(query, page)
        print(json.dumps(result))

except Exception as e:
    print(json.dumps({
        'error': str(e),
        'data': {
            'items': [],
            'is_next_page': False
        }
    }))
