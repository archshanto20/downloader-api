from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

def get_download_info(url):
    # আমরা এখানে কন্ডিশন দিচ্ছি: 
    # ১. protocol^=http: লিংকটি অবশ্যই http/https হতে হবে (m3u8 না)
    # ২. ext=mp4: ফরম্যাট অবশ্যই mp4 হতে হবে
    # ৩. acodec!='none': অডিও থাকতে হবে
    
    ydl_opts = {
        'format': 'best[protocol^=http][ext=mp4]/best[protocol^=http]',
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'noplaylist': True,
        # কুকেজ সমস্যা এড়ানোর জন্য ইউজার এজেন্ট ব্যবহার করা
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # ভিডিওর তথ্য বের করা
            info = ydl.extract_info(url, download=False)
            
            # সেফটি চেক: যদি কোনো কারণে এরপরও m3u8 চলে আসে
            download_url = info.get('url')
            
            if 'm3u8' in str(download_url):
                # যদি মেইন লিংক m3u8 হয়, আমরা ফরম্যাট লিস্ট ঘেঁটে mp4 খুঁজব
                formats = info.get('formats', [])
                for f in reversed(formats): # উল্টো দিক থেকে লুপ চালাবো (ভালো কোয়ালিটি সাধারণত শেষে থাকে)
                    f_url = f.get('url', '')
                    f_ext = f.get('ext', '')
                    f_proto = f.get('protocol', '')
                    
                    # শর্ত: mp4 হতে হবে এবং m3u8 হওয়া যাবে না
                    if f_ext == 'mp4' and 'm3u8' not in f_url and 'http' in f_proto:
                        download_url = f_url
                        break
            
            return {
                "status": "success",
                "title": info.get('title', 'Video'),
                "thumbnail": info.get('thumbnail', ''),
                "download_url": download_url,
                "ext": "mp4" # আমরা জোর করে mp4 বলছি কারণ আমরা ফিল্টার করেছি
            }
            
    except Exception as e:
        print(f"Error: {e}")
        return {
            "status": "error", 
            "message": "Direct MP4 link not found. Try a different video."
        }

@app.route('/')
def home():
    return "Server is Running (Strict MP4 Mode) 🚀"

@app.route('/analyze', methods=['POST'])
def analyze_link():
    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"status": "error", "message": "No URL provided"}), 400

    result = get_download_info(url)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5000)