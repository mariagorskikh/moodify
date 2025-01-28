from flask import Flask, request, jsonify, send_file
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
import requests

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create temporary directories for processing
TEMP_DIR = tempfile.mkdtemp()
OUTPUT_DIR = os.path.join(TEMP_DIR, 'output')
UPLOAD_FOLDER = os.path.join(TEMP_DIR, 'uploads')
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

logger.info(f"Temporary directory created at: {TEMP_DIR}")
logger.info(f"Output directory created at: {OUTPUT_DIR}")
logger.info(f"Upload directory created at: {UPLOAD_FOLDER}")

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
        raise ValueError(f"Failed to download video: {str(e)}")

def apply_audio_effect(input_path, output_path, effect_type='slow_reverb'):
    """Apply audio effect using FFmpeg."""
    try:
        logger.info(f"Input path exists: {os.path.exists(input_path)}")
        logger.info(f"Input path size: {os.path.getsize(input_path) if os.path.exists(input_path) else 'file not found'}")
        
        # Define effect parameters for each vibe
        effect_params = {
            'slow_reverb': {
                'speed': 0.85,
                'reverb_delay': 60,
                'reverb_decay': 0.4
            },
            'energetic': {
                'speed': 1.2,
                'reverb_delay': 20,
                'reverb_decay': 0.2
            },
            'dark': {
                'speed': 0.8,
                'reverb_delay': 100,
                'reverb_decay': 0.6
            },
            'cute': {
                'speed': 1.1,
                'reverb_delay': 30,
                'reverb_decay': 0.3
            },
            'cool': {
                'speed': 0.95,
                'reverb_delay': 50,
                'reverb_decay': 0.5
            },
            'happy': {
                'speed': 1.05,
                'reverb_delay': 40,
                'reverb_decay': 0.3
            },
            'intense': {
                'speed': 1.35,
                'reverb_delay': 25,
                'reverb_decay': 0.2
            },
            'melodic': {
                'speed': 0.9,
                'reverb_delay': 70,
                'reverb_decay': 0.5
            },
            'chill': {
                'speed': 0.9,
                'reverb_delay': 80,
                'reverb_decay': 0.4
            },
            'sleepy': {
                'speed': 0.75,
                'reverb_delay': 90,
                'reverb_decay': 0.7
            }
        }
        
        # Get effect parameters or use default
        params = effect_params.get(effect_type, effect_params['slow_reverb'])
        
        # Build FFmpeg command with parameters
        filter_complex = (
            f'[0:a]asetrate=44100*{params["speed"]},aresample=44100,atempo=1.0[s];'
            f'[s]aecho=0.8:0.88:{params["reverb_delay"]}:{params["reverb_decay"]}[e]'
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[e]',
            '-acodec', 'libmp3lame', '-q:a', '2',
            output_path
        ]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"FFmpeg stdout: {result.stdout}")
        logger.info(f"FFmpeg stderr: {result.stderr}")
        
        if not os.path.exists(output_path):
            logger.error("Output file was not created")
            return False
            
        logger.info(f"Output file created successfully, size: {os.path.getsize(output_path)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in apply_audio_effect: {str(e)}")
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

def split_audio(input_path, start_time, end_time, output_path):
    """Split audio file between start_time and end_time."""
    try:
        # Use ffmpeg with accurate seeking
        command = [
            'ffmpeg',
            '-y',  # Overwrite output file if it exists
            '-ss', str(start_time),  # Start time
            '-i', input_path,  # Input file
            '-t', str(end_time - start_time),  # Duration
            '-acodec', 'libmp3lame',  # Use MP3 codec
            '-ar', '44100',  # Audio sample rate
            '-ab', '192k',  # Audio bitrate
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error splitting audio: {result.stderr}")
            raise Exception(f"Failed to split audio: {result.stderr}")
            
        return output_path
    except Exception as e:
        logger.error(f"Error in split_audio: {str(e)}")
        raise

def mix_audio_tracks(tracks_data):
    """Mix multiple audio tracks with specified parameters."""
    try:
        # Create a temporary directory for track processing
        temp_dir = os.path.join(TEMP_DIR, f'mix_{uuid.uuid4()}')
        os.makedirs(temp_dir, exist_ok=True)
        output_path = os.path.join(temp_dir, 'mixed.mp3')
        
        # Process each track and prepare FFmpeg filter complex
        filter_complex = []
        inputs = []
        
        for i, track in enumerate(tracks_data):
            # Save track to temporary file
            track_path = os.path.join(temp_dir, f'track_{i}.mp3')
            track['file'].save(track_path)
            inputs.extend(['-i', track_path])
            
            # Add volume and trim filter
            volume = float(track['volume']) / 100
            start_time = float(track['start_time'])
            duration = float(track['trim_length']) if track['trim_length'] else None
            
            filter_str = f'[{i}]volume={volume}'
            if start_time > 0:
                filter_str += f',adelay={int(start_time*1000)}|{int(start_time*1000)}'
            if duration:
                filter_str += f',atrim=0:{duration}'
            filter_str += f'[a{i}]'
            
            filter_complex.append(filter_str)
        
        # Mix all tracks
        mix_str = ''.join(f'[a{i}]' for i in range(len(tracks_data)))
        filter_complex.append(f'{mix_str}amix=inputs={len(tracks_data)}:normalize=0[out]')
        
        # Build FFmpeg command
        command = [
            'ffmpeg', '-y',
            *inputs,
            '-filter_complex', ';'.join(filter_complex),
            '-map', '[out]',
            '-acodec', 'libmp3lame',
            '-ar', '44100',
            '-ab', '192k',
            output_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Error mixing audio: {result.stderr}")
            raise Exception(f"Failed to mix audio: {result.stderr}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Error in mix_audio_tracks: {str(e)}")
        raise

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    try:
        data = request.get_json()
        logger.info(f"Received request data: {data}")
        
        if not data or 'url' not in data:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url']
        effect_type = data.get('effect_type', 'slow_reverb')
        
        logger.info(f"Processing URL: {url} with effect: {effect_type}")
        
        # Process the audio
        output_path = process_youtube_audio(url, effect_type)
        
        if not os.path.exists(output_path):
            logger.error("Output file not found after processing")
            return jsonify({'error': 'Failed to create output file'}), 500
        
        logger.info(f"Sending processed file: {output_path}")
        # Return the processed file
        return send_file(
            output_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"moodify_{secure_filename(effect_type)}.mp3"
        )

    except ValueError as e:
        logger.error(f"Error in transform_audio: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Error in transform_audio: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

@app.route('/api/split', methods=['POST'])
def split_audio_endpoint():
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio_file']
        start_time = float(request.form['start_time'])
        end_time = float(request.form['end_time'])
        
        # Save the uploaded file temporarily
        temp_input = os.path.join(UPLOAD_FOLDER, 'temp_input.mp3')
        audio_file.save(temp_input)
        
        # Generate output path
        output_filename = f'split_{start_time}_{end_time}.mp3'
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        try:
            # Split the audio
            split_audio(temp_input, start_time, end_time, output_path)
            
            # Send the file back to the client
            return send_file(output_path, as_attachment=True)
        finally:
            # Clean up temporary files
            if os.path.exists(temp_input):
                os.remove(temp_input)
            if os.path.exists(output_path):
                os.remove(output_path)
                
    except Exception as e:
        logger.error(f"Error in split_audio_endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mix', methods=['POST'])
def mix_tracks_endpoint():
    try:
        if not request.files:
            return jsonify({'error': 'No audio files provided'}), 400
        
        # Collect track data
        tracks_data = []
        for key in request.files:
            if key.startswith('track_'):
                track_num = key.split('_')[1]
                tracks_data.append({
                    'file': request.files[key],
                    'volume': request.form.get(f'volume_{track_num}', '100'),
                    'start_time': request.form.get(f'start_time_{track_num}', '0'),
                    'trim_length': request.form.get(f'trim_length_{track_num}', '')
                })
        
        if not tracks_data:
            return jsonify({'error': 'No valid tracks found'}), 400
        
        # Mix the tracks
        output_path = mix_audio_tracks(tracks_data)
        
        # Send the mixed file
        return send_file(output_path, as_attachment=True, download_name='mixed.mp3')
        
    except Exception as e:
        logger.error(f"Error in mix_tracks_endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(debug=True, port=5005)
