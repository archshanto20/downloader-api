# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)  # এটি অন্য ডোমেইন (আপনার HTML) থেকে রিকোয়েস্ট অ্যালাউ করবে

def get_download_info(url):
    # yt-dlp অপশন: আমরা সেরা ফরম্যাট এবং সরাসরি লিংক চাই
    ydl_opts = {
        'format': 'best',  # সেরা কোয়ালিটি
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # ভিডিওর টাইটেল এবং থাম্বনেইল
            title = info.get('title', 'Unknown File')
            thumbnail = info.get('thumbnail', '')
            
            # ডাউনলোড লিংক বের করা
            download_url = info.get('url')
            
            # ফরম্যাট চেক (ভিডিও না অডিও)
            ext = info.get('ext', 'mp4')

            return {
                "status": "success",
                "title": title,
                "thumbnail": thumbnail,
                "download_url": download_url,
                "ext": ext
            }
    except Exception as e:
        # যদি yt-dlp ব্যর্থ হয়, আমরা ধরে নেব এটি একটি সাধারণ ফাইল (PDF/JPG)
        # সাধারণ ফাইলের ক্ষেত্রে ইনপুট লিংকটিই ডাউনলোড লিংক
        return {
            "status": "direct_link",
            "download_url": url,
            "title": "Direct File (PDF/Image/Zip)",
            "thumbnail": "https://cdn-icons-png.flaticon.com/512/4208/4208397.png"
        }

@app.route('/')
def home():
    return "Server is Running! 🚀"

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