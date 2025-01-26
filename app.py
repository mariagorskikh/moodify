from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import logging
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temporary directory
TEMP_DIR = '/tmp'
os.makedirs(TEMP_DIR, exist_ok=True)

def download_audio(url):
    """Download audio using yt-dlp."""
    try:
        # Generate unique filename
        filename = f"audio_{uuid.uuid4()}.mp3"
        output_path = os.path.join(TEMP_DIR, filename)
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',  # Choose best audio format
            'outtmpl': output_path,      # Output template
            'postprocessors': [{          # Extract audio
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'no_warnings': True,          # Reduce output
            'quiet': True,
            'extract_flat': True,         # Don't download playlists
            'force_generic_extractor': False,
            'cachedir': False,            # Disable cache
        }
        
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio from: {url}")
            ydl.download([url])
        
        # Check if file exists (yt-dlp adds extension)
        final_path = output_path + '.mp3'
        if not os.path.exists(final_path):
            raise ValueError("Failed to download audio")
            
        return final_path
        
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise ValueError(f"Failed to download video: {str(e)}")

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    """Download audio from YouTube URL."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        url = data['url']
        logger.info(f"Processing request - URL: {url}")
        
        try:
            # Download audio
            output_path = download_audio(url)
            
            # Read and return the file
            with open(output_path, 'rb') as f:
                audio_data = f.read()
                
            # Clean up
            try:
                os.remove(output_path)
            except Exception as e:
                logger.warning(f"Failed to clean up file: {str(e)}")
            
            # Return audio file
            response = Response(audio_data, mimetype='audio/mpeg')
            response.headers['Content-Disposition'] = 'attachment; filename=audio.mp3'
            return response
            
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return jsonify({'error': 'Failed to process audio'}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True)
