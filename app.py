from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import logging
import traceback
import sys
from youtube import download_audio

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # Ensure logs go to stdout for Vercel
)
logger = logging.getLogger(__name__)

@app.route('/')
def serve_index():
    """Serve index.html"""
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('.', path)

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    """Transform YouTube URL to audio."""
    try:
        # Log request details
        logger.info("Received /api/transform request")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Validate request
        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({
                'error': 'Request must be JSON',
                'details': 'Content-Type header must be application/json'
            }), 400

        data = request.get_json()
        logger.info(f"Request data: {data}")
        
        if not data or 'url' not in data:
            logger.error("No URL in request data")
            return jsonify({
                'error': 'No URL provided',
                'details': 'Request body must include a url field'
            }), 400

        url = data['url']
        logger.info(f"Processing URL: {url}")
        
        try:
            # Download audio
            logger.info("Starting audio download...")
            audio_data = download_audio(url)
            
            if not audio_data or len(audio_data) == 0:
                logger.error("No audio data received")
                return jsonify({
                    'error': 'No audio data received',
                    'details': 'The download process completed but no audio data was returned'
                }), 400
                
            # Log success
            logger.info(f"Successfully downloaded {len(audio_data)} bytes of audio")
            
            # Create response
            response = Response(
                audio_data,
                status=200,
                mimetype='audio/mpeg',
                direct_passthrough=True
            )
            
            # Set headers
            response.headers['Content-Type'] = 'audio/mpeg'
            response.headers['Content-Length'] = str(len(audio_data))
            response.headers['Accept-Ranges'] = 'bytes'
            response.headers['Cache-Control'] = 'no-cache'
            
            # Log response details
            logger.info(f"Response headers: {dict(response.headers)}")
            
            return response
            
        except ValueError as e:
            logger.error(f"Value error in download: {str(e)}")
            return jsonify({
                'error': str(e),
                'details': 'Error occurred while processing the YouTube URL'
            }), 400
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify({
                'error': 'Failed to process audio',
                'details': str(e),
                'traceback': traceback.format_exc()
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Service is running'
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
