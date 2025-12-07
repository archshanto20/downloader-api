import os
import uuid
import time
import requests
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import static_ffmpeg

# FFmpeg সেটআপ
static_ffmpeg.add_paths()

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- Anti-Bot Options Generator ---
def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        # ইউটিউবকে ধোঁকা দেওয়ার জন্য অ্যান্ড্রয়েড ক্লায়েন্ট সাজা
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'], # অ্যান্ড্রয়েড হিসেবে রিকোয়েস্ট যাবে
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        # রিয়াল ব্রাউজার ইউজার এজেন্ট
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    }

@app.route('/')
def home():
    return "Anti-Bot Downloader Running! 🛡️"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"status": "error", "message": "No URL"}), 400

    # ১. ডাইরেক্ট ফাইল চেক
    try:
        head_check = requests.head(url, allow_redirects=True, timeout=3)
        content_type = head_check.headers.get('Content-Type', '')
        if 'text/html' not in content_type and 'video' not in content_type:
             return jsonify({
                "status": "success",
                "type": "direct_file",
                "title": url.split('/')[-1] or "Unknown File",
                "thumbnail": "https://cdn-icons-png.flaticon.com/512/2926/2926214.png",
                "url": url
            })
    except: pass

    # ২. ভিডিও প্ল্যাটফর্ম চেক (Anti-Bot সহ)
    try:
        opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            seen_resolutions = set()

            for f in info.get('formats', []):
                if f.get('height') and f.get('vcodec') != 'none':
                    res = f"{f['height']}p"
                    if res not in seen_resolutions:
                        formats_list.append({
                            'id': f['format_id'],
                            'resolution': res,
                            'ext': f['ext']
                        })
                        seen_resolutions.add(res)
            
            formats_list.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)

            return jsonify({
                "status": "success",
                "type": "video_platform",
                "title": info.get('title', 'media'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": formats_list
            })

    except Exception as e:
        # এরর হলে কনসোলে প্রিন্ট হবে, কিন্তু ইউজারকে ক্লিন মেসেজ দিবে
        print(f"Server Error Log: {str(e)}")
        return jsonify({"status": "error", "message": "Bot detected or Link invalid. Try again later."})


@app.route('/process_download', methods=['GET'])
def process_download():
    url = request.args.get('url')
    title = request.args.get('title', 'media')
    mode = request.args.get('mode', 'video')
    quality = request.args.get('quality')

    unique_id = uuid.uuid4()
    filename = f"{unique_id}"
    
    opts = get_ydl_opts()
    opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    if mode == 'audio':
        ext = "mp3"
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        })
    else:
        ext = "mp4"
        target_height = quality.replace('p', '') 
        opts.update({
            'format': f'bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        final_path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")

        @after_this_request
        def remove_file(response):
            try:
                time.sleep(2)
                if os.path.exists(final_path):
                    os.remove(final_path)
            except: pass
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{title}_{quality}.{ext}",
            mimetype=f'{mode}/{ext}'
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)import os
import uuid
import time
import requests
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import static_ffmpeg

# FFmpeg সেটআপ
static_ffmpeg.add_paths()

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- Anti-Bot Options Generator ---
def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        # ইউটিউবকে ধোঁকা দেওয়ার জন্য অ্যান্ড্রয়েড ক্লায়েন্ট সাজা
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'], # অ্যান্ড্রয়েড হিসেবে রিকোয়েস্ট যাবে
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        # রিয়াল ব্রাউজার ইউজার এজেন্ট
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    }

@app.route('/')
def home():
    return "Anti-Bot Downloader Running! 🛡️"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"status": "error", "message": "No URL"}), 400

    # ১. ডাইরেক্ট ফাইল চেক
    try:
        head_check = requests.head(url, allow_redirects=True, timeout=3)
        content_type = head_check.headers.get('Content-Type', '')
        if 'text/html' not in content_type and 'video' not in content_type:
             return jsonify({
                "status": "success",
                "type": "direct_file",
                "title": url.split('/')[-1] or "Unknown File",
                "thumbnail": "https://cdn-icons-png.flaticon.com/512/2926/2926214.png",
                "url": url
            })
    except: pass

    # ২. ভিডিও প্ল্যাটফর্ম চেক (Anti-Bot সহ)
    try:
        opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            seen_resolutions = set()

            for f in info.get('formats', []):
                if f.get('height') and f.get('vcodec') != 'none':
                    res = f"{f['height']}p"
                    if res not in seen_resolutions:
                        formats_list.append({
                            'id': f['format_id'],
                            'resolution': res,
                            'ext': f['ext']
                        })
                        seen_resolutions.add(res)
            
            formats_list.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)

            return jsonify({
                "status": "success",
                "type": "video_platform",
                "title": info.get('title', 'media'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": formats_list
            })

    except Exception as e:
        # এরর হলে কনসোলে প্রিন্ট হবে, কিন্তু ইউজারকে ক্লিন মেসেজ দিবে
        print(f"Server Error Log: {str(e)}")
        return jsonify({"status": "error", "message": "Bot detected or Link invalid. Try again later."})


@app.route('/process_download', methods=['GET'])
def process_download():
    url = request.args.get('url')
    title = request.args.get('title', 'media')
    mode = request.args.get('mode', 'video')
    quality = request.args.get('quality')

    unique_id = uuid.uuid4()
    filename = f"{unique_id}"
    
    opts = get_ydl_opts()
    opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    if mode == 'audio':
        ext = "mp3"
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        })
    else:
        ext = "mp4"
        target_height = quality.replace('p', '') 
        opts.update({
            'format': f'bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        final_path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")

        @after_this_request
        def remove_file(response):
            try:
                time.sleep(2)
                if os.path.exists(final_path):
                    os.remove(final_path)
            except: pass
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{title}_{quality}.{ext}",
            mimetype=f'{mode}/{ext}'
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)import os
import uuid
import time
import requests
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
import yt_dlp
import static_ffmpeg

# FFmpeg সেটআপ
static_ffmpeg.add_paths()

app = Flask(__name__)
CORS(app)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# --- Anti-Bot Options Generator ---
def get_ydl_opts():
    return {
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        # ইউটিউবকে ধোঁকা দেওয়ার জন্য অ্যান্ড্রয়েড ক্লায়েন্ট সাজা
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'], # অ্যান্ড্রয়েড হিসেবে রিকোয়েস্ট যাবে
                'player_skip': ['webpage', 'configs', 'js'],
            }
        },
        # রিয়াল ব্রাউজার ইউজার এজেন্ট
        'user_agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    }

@app.route('/')
def home():
    return "Anti-Bot Downloader Running! 🛡️"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"status": "error", "message": "No URL"}), 400

    # ১. ডাইরেক্ট ফাইল চেক
    try:
        head_check = requests.head(url, allow_redirects=True, timeout=3)
        content_type = head_check.headers.get('Content-Type', '')
        if 'text/html' not in content_type and 'video' not in content_type:
             return jsonify({
                "status": "success",
                "type": "direct_file",
                "title": url.split('/')[-1] or "Unknown File",
                "thumbnail": "https://cdn-icons-png.flaticon.com/512/2926/2926214.png",
                "url": url
            })
    except: pass

    # ২. ভিডিও প্ল্যাটফর্ম চেক (Anti-Bot সহ)
    try:
        opts = get_ydl_opts()
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            seen_resolutions = set()

            for f in info.get('formats', []):
                if f.get('height') and f.get('vcodec') != 'none':
                    res = f"{f['height']}p"
                    if res not in seen_resolutions:
                        formats_list.append({
                            'id': f['format_id'],
                            'resolution': res,
                            'ext': f['ext']
                        })
                        seen_resolutions.add(res)
            
            formats_list.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)

            return jsonify({
                "status": "success",
                "type": "video_platform",
                "title": info.get('title', 'media'),
                "thumbnail": info.get('thumbnail', ''),
                "formats": formats_list
            })

    except Exception as e:
        # এরর হলে কনসোলে প্রিন্ট হবে, কিন্তু ইউজারকে ক্লিন মেসেজ দিবে
        print(f"Server Error Log: {str(e)}")
        return jsonify({"status": "error", "message": "Bot detected or Link invalid. Try again later."})


@app.route('/process_download', methods=['GET'])
def process_download():
    url = request.args.get('url')
    title = request.args.get('title', 'media')
    mode = request.args.get('mode', 'video')
    quality = request.args.get('quality')

    unique_id = uuid.uuid4()
    filename = f"{unique_id}"
    
    opts = get_ydl_opts()
    opts['outtmpl'] = os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s")

    if mode == 'audio':
        ext = "mp3"
        opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
        })
    else:
        ext = "mp4"
        target_height = quality.replace('p', '') 
        opts.update({
            'format': f'bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

        final_path = os.path.join(DOWNLOAD_DIR, f"{filename}.{ext}")

        @after_this_request
        def remove_file(response):
            try:
                time.sleep(2)
                if os.path.exists(final_path):
                    os.remove(final_path)
            except: pass
            return response

        return send_file(
            final_path, 
            as_attachment=True, 
            download_name=f"{title}_{quality}.{ext}",
            mimetype=f'{mode}/{ext}'
        )

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)