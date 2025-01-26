from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import logging
import traceback
import sys
import os
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

@app.route('/api/debug', methods=['GET'])
def debug_info():
    """Debug endpoint to check environment and configuration."""
    try:
        # Get environment variables
        api_key = os.getenv('RAPIDAPI_KEY', 'Not set')
        python_path = os.getenv('PYTHONPATH', 'Not set')
        
        # Check if we can import required modules
        import requests
        requests_version = requests.__version__
        
        # Get all environment variables
        all_env = {k: v for k, v in os.environ.items() if not k.lower().startswith('key')}
        
        return jsonify({
            'status': 'debug',
            'environment': {
                'RAPIDAPI_KEY': 'Present' if api_key != 'Not set' else 'Missing',
                'PYTHONPATH': python_path,
                'PWD': os.getcwd(),
                'All Environment': all_env
            },
            'dependencies': {
                'requests': requests_version
            },
            'files': os.listdir('.')
        })
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    """Transform YouTube URL to audio."""
    try:
        # Log request details
        logger.info("Received /api/transform request")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        # Check environment
        api_key = os.getenv('RAPIDAPI_KEY')
        if not api_key:
            logger.error("RAPIDAPI_KEY not set")
            return jsonify({
                'error': 'API key not configured',
                'details': 'Server configuration error'
            }), 500
            
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
        'message': 'Service is running',
        'environment': {
            'RAPIDAPI_KEY': 'Present' if os.getenv('RAPIDAPI_KEY') else 'Missing'
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
