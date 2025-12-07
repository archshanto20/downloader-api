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

def format_selector(ctx):
    """এটি বেস্ট ভিডিও এবং অডিও ফরম্যাট সিলেক্ট করতে সাহায্য করে"""
    return ctx.get('format_id')

@app.route('/')
def home():
    return "Ultra Downloader & Converter Running! 🚀"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"status": "error", "message": "No URL"}), 400

    # === ধাপ ১: চেক করি এটি সাধারণ ফাইল কিনা (Direct Link) ===
    try:
        head_check = requests.head(url, allow_redirects=True, timeout=3)
        content_type = head_check.headers.get('Content-Type', '')
        
        # যদি এটি ভিডিও প্ল্যাটফর্ম না হয় এবং ডাইরেক্ট ফাইল হয়
        if 'text/html' not in content_type and 'video' not in content_type:
             return jsonify({
                "status": "success",
                "type": "direct_file",
                "title": url.split('/')[-1] or "Unknown File",
                "thumbnail": "https://cdn-icons-png.flaticon.com/512/2926/2926214.png",
                "url": url
            })
    except:
        pass # ফেইল করলে আমরা yt-dlp দিয়ে ট্রাই করব

    # === ধাপ ২: ভিডিও প্ল্যাটফর্ম অ্যানালাইসিস ===
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            
            formats_list = []
            seen_resolutions = set()

            # ভিডিও ফরম্যাটগুলো খুঁজে বের করা
            for f in info.get('formats', []):
                # রেজোলিউশন আছে এবং ভিডিও কোডেক আছে
                if f.get('height') and f.get('vcodec') != 'none':
                    res = f"{f['height']}p"
                    # ডুপ্লিকেট রিমুভ করা
                    if res not in seen_resolutions:
                        formats_list.append({
                            'id': f['format_id'],
                            'resolution': res,
                            'ext': f['ext'],
                            'note': f.get('format_note', '')
                        })
                        seen_resolutions.add(res)
            
            # ভালো দেখার জন্য রেজোলিউশন সর্ট করা (বড় থেকে ছোট)
            formats_list.sort(key=lambda x: int(x['resolution'][:-1]), reverse=True)

            return jsonify({
                "status": "success",
                "type": "video_platform",
                "title": info.get('title', 'media'),
                "thumbnail": info.get('thumbnail', ''),
                "duration": info.get('duration_string', ''),
                "formats": formats_list
            })

    except Exception as e:
        return jsonify({"status": "error", "message": "Link not supported or Private."})


@app.route('/process_download', methods=['GET'])
def process_download():
    url = request.args.get('url')
    title = request.args.get('title', 'media')
    mode = request.args.get('mode', 'video') # video / audio
    quality = request.args.get('quality')    # resolution (1080p) or bitrate (192)

    unique_id = uuid.uuid4()
    filename = f"{unique_id}"
    
    ydl_opts = {
        'outtmpl': os.path.join(DOWNLOAD_DIR, f"{filename}.%(ext)s"),
        'quiet': True,
        'noplaylist': True,
    }

    if mode == 'audio':
        # অডিও কনভার্সন
        ext = "mp3"
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality, # 128, 192, 320
            }],
        })
    else:
        # ভিডিও স্পেসিফিক কোয়ালিটি
        ext = "mp4"
        # ইউজার যে পিক্সেল সিলেক্ট করেছে (যেমন 1080), সেটার সমান বা নিচের সেরাটা নামাবে
        target_height = quality.replace('p', '') 
        
        ydl_opts.update({
            # লজিক: সিলেক্ট করা হাইট এর ভিডিও + বেস্ট অডিও -> মার্জ করে MP4
            'format': f'bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]',
            'merge_output_format': 'mp4',
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
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