from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from pytube import YouTube
import os
import tempfile
import uuid
import logging
import traceback
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
    """Download audio using pytube."""
    try:
        # Extract video ID from URL
        yt = YouTube(url)
        
        # Get audio stream
        stream = yt.streams.filter(only_audio=True).first()
        if not stream:
            raise ValueError("No audio stream found")
            
        # Generate unique filename
        filename = f"audio_{uuid.uuid4()}.mp3"
        output_path = os.path.join(TEMP_DIR, filename)
        
        # Download the file
        stream.download(output_path=TEMP_DIR, filename=filename)
        
        if not os.path.exists(output_path):
            raise ValueError("Failed to download audio")
            
        return output_path
        
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise ValueError(f"Failed to download video: {str(e)}")

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    """Transform audio from YouTube URL."""
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
