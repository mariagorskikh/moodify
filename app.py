from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import logging
from werkzeug.utils import secure_filename
from youtube import download_audio

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temporary directory
TEMP_DIR = '/tmp'
os.makedirs(TEMP_DIR, exist_ok=True)

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
            audio_data = download_audio(url)
            
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
