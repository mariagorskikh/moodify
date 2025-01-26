from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import subprocess
import logging
import traceback
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create temporary directories for processing
TEMP_DIR = '/tmp' if os.getenv('VERCEL') else tempfile.mkdtemp()
OUTPUT_DIR = os.path.join(TEMP_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger.info(f"Temporary directory created at: {TEMP_DIR}")
logger.info(f"Output directory created at: {OUTPUT_DIR}")

def extract_video_id(url):
    """Extract the video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_audio(url, output_path):
    """Download audio from YouTube using yt-dlp."""
    try:
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True,
            'extract_audio': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            # Add these options to bypass restrictions
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'no_warnings': True,
            'quiet': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['js', 'configs', 'webpage']
                }
            },
            # Add common browser user-agent
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio from: {url}")
            ydl.download([url])
            
        # yt-dlp adds extension, so we need to check for the actual file
        mp3_path = output_path + '.mp3'
        if os.path.exists(mp3_path):
            return mp3_path
        else:
            logger.error(f"Expected file not found: {mp3_path}")
            raise ValueError("Failed to download audio")
            
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        if "Sign in to confirm you're not a bot" in str(e):
            raise ValueError("YouTube is requiring verification. Please try a different video or try again later.")
        raise ValueError(f"Failed to download video: {str(e)}")

def apply_audio_effect(input_path, output_path, effect_type='slow_reverb'):
    """Apply audio effect using FFmpeg."""
    try:
        # Define effect parameters based on type
        effect_params = {
            'slow_reverb': {
                'speed': 0.85,
                'reverb_delay': 100,
                'reverb_decay': 10
            },
            'energetic': {
                'speed': 1.2,
                'reverb_delay': 30,
                'reverb_decay': 2
            },
            'dark': {
                'speed': 0.8,
                'reverb_delay': 100,
                'reverb_decay': 15
            },
            'cute': {
                'speed': 1.1,
                'reverb_delay': 20,
                'reverb_decay': 2
            },
            'cool': {
                'speed': 0.95,
                'reverb_delay': 50,
                'reverb_decay': 5
            },
            'happy': {
                'speed': 1.05,
                'reverb_delay': 40,
                'reverb_decay': 4
            },
            'intense': {
                'speed': 1.15,
                'reverb_delay': 20,
                'reverb_decay': 2
            },
            'melodic': {
                'speed': 1.0,
                'reverb_delay': 60,
                'reverb_decay': 8
            },
            'chill': {
                'speed': 0.9,
                'reverb_delay': 80,
                'reverb_decay': 6
            },
            'sleepy': {
                'speed': 0.75,
                'reverb_delay': 120,
                'reverb_decay': 12
            }
        }
        
        params = effect_params.get(effect_type, effect_params['slow_reverb'])
        
        # Construct FFmpeg filter
        filter_complex = f"asetrate=44100*{params['speed']},aresample=44100," + \
                        f"aecho=0.8:0.8:{params['reverb_delay']}:{params['reverb_decay']}[e]"
        
        # Construct FFmpeg command
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[e]',
            '-acodec', 'libmp3lame', '-q:a', '2',
            output_path
        ]
        
        # Run FFmpeg
        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            return False
            
        return os.path.exists(output_path)
        
    except Exception as e:
        logger.error(f"Error in apply_audio_effect: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def process_youtube_audio(url, effect_type='slow_reverb'):
    """Download and process YouTube audio."""
    download_path = None
    try:
        logger.info(f"Processing YouTube URL: {url}")
        
        # Extract video ID and construct clean URL
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL format")
            
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Clean YouTube URL: {clean_url}")
        
        # Generate unique filename
        temp_filename = f"{uuid.uuid4()}"
        download_path = os.path.join(TEMP_DIR, temp_filename)
        output_path = os.path.join(OUTPUT_DIR, f"{temp_filename}.mp3")

        # Download the audio
        downloaded_file = download_audio(clean_url, download_path)
        logger.info(f"Download completed, file size: {os.path.getsize(downloaded_file)}")

        # Convert and apply effect
        logger.info("Applying audio effect...")
        if not apply_audio_effect(downloaded_file, output_path, effect_type):
            raise ValueError("Failed to process audio with effects")
        logger.info("Audio effect applied successfully")

        # Clean up downloaded file
        os.remove(downloaded_file)
        logger.info("Cleaned up temporary files")

        return output_path

    except ValueError as e:
        # Re-raise user-friendly errors
        raise
    except Exception as e:
        logger.error(f"Error in process_youtube_audio: {str(e)}")
        logger.error(traceback.format_exc())
        if download_path and os.path.exists(download_path + '.mp3'):
            os.remove(download_path + '.mp3')
        raise ValueError("An unexpected error occurred while processing the video")

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400
            
        url = data['url']
        effect_type = data.get('effect_type', 'slow_reverb')
        
        logger.info(f"Received request - URL: {url}, Effect: {effect_type}")
        
        output_path = process_youtube_audio(url, effect_type)
        
        if not output_path or not os.path.exists(output_path):
            return jsonify({'error': 'Failed to process audio'}), 500
            
        # Read the file and return it as a response
        with open(output_path, 'rb') as f:
            audio_data = f.read()
        
        # Clean up the output file
        os.remove(output_path)
        
        response = Response(audio_data, mimetype='audio/mpeg')
        response.headers['Content-Disposition'] = f'attachment; filename=moodify_{secure_filename(effect_type)}.mp3'
        return response

    except ValueError as e:
        logger.error(f"Error in transform_audio: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in transform_audio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

# For local development
if __name__ == '__main__':
    app.run(debug=True, port=5005)
