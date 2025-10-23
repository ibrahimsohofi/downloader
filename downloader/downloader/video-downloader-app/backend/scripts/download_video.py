#!/usr/bin/env python3
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../downloader'))

try:
    from youtube_dl import YoutubeDL

    def download_video(url, output_path='downloads'):
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }

        with YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                return {
                    'success': True,
                    'file_path': filename,
                    'title': info.get('title', ''),
                    'message': 'Download completed successfully'
                }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'message': 'Download failed'
                }

    if __name__ == '__main__':
        url = sys.argv[1] if len(sys.argv) > 1 else ''
        output_path = sys.argv[2] if len(sys.argv) > 2 else 'downloads'

        if not url:
            print(json.dumps({
                'success': False,
                'error': 'No URL provided',
                'message': 'Download failed'
            }))
        else:
            result = download_video(url, output_path)
            print(json.dumps(result))

except Exception as e:
    print(json.dumps({
        'success': False,
        'error': str(e),
        'message': 'Download failed'
    }))
