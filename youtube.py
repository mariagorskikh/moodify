import requests
import re
import json
import logging
from urllib.parse import parse_qs, urlparse
import os

logger = logging.getLogger(__name__)

# Get API key from environment variable or use default
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    try:
        logger.info(f"Extracting video ID from URL: {url}")
        
        # Try parsing URL
        parsed_url = urlparse(url)
        
        # Check for youtu.be
        if parsed_url.netloc == 'youtu.be':
            video_id = parsed_url.path[1:]
            logger.info(f"Extracted video ID from youtu.be URL: {video_id}")
            return video_id
        
        # Check for youtube.com
        if parsed_url.netloc in ['youtube.com', 'www.youtube.com']:
            if parsed_url.path == '/watch':
                video_id = parse_qs(parsed_url.query).get('v', [None])[0]
                logger.info(f"Extracted video ID from youtube.com watch URL: {video_id}")
                return video_id
            elif parsed_url.path.startswith(('/embed/', '/v/')):
                video_id = parsed_url.path.split('/')[2]
                logger.info(f"Extracted video ID from embed/v URL: {video_id}")
                return video_id
        
        # Try regex as fallback
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
            r'(?:embed\/)([0-9A-Za-z_-]{11})',
            r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                video_id = match.group(1)
                logger.info(f"Extracted video ID using regex: {video_id}")
                return video_id
                
        logger.error("Could not extract video ID from URL")
        raise ValueError("Could not extract video ID from URL")
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        raise ValueError(f"Invalid YouTube URL: {str(e)}")

def download_audio(url):
    """Download audio from YouTube URL using RapidAPI."""
    try:
        # Check environment
        api_key = RAPIDAPI_KEY
        if not api_key:
            raise ValueError("RAPIDAPI_KEY environment variable is not set")
        logger.info("API key is configured")
        
        # Extract video ID
        video_id = extract_video_id(url)
        logger.info(f"Processing video ID: {video_id}")
        
        # Use YouTube MP3 Converter API
        api_url = "https://youtube-mp3-converter-v2.p.rapidapi.com/ytmp3/url"
        querystring = {"url": f"https://www.youtube.com/watch?v={video_id}"}
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "youtube-mp3-converter-v2.p.rapidapi.com"
        }
        
        # Log request details
        logger.info(f"Making API request to: {api_url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Query params: {querystring}")
        
        # Make API request
        response = requests.get(api_url, headers=headers, params=querystring, timeout=30)
        
        # Log response details
        logger.info(f"API response status: {response.status_code}")
        logger.info(f"API response headers: {dict(response.headers)}")
        
        try:
            response_text = response.text
            logger.info(f"API response text: {response_text}")
            data = response.json()
            logger.info(f"API response data: {data}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse API response: {response_text}")
            raise ValueError("Invalid response from API")
        
        # Get download URL
        if 'url' not in data:
            logger.error(f"No download URL in response: {data}")
            raise ValueError("No download URL in API response")
            
        download_url = data['url']
        logger.info(f"Got download URL: {download_url}")
        
        # Download the audio file
        logger.info("Downloading audio file...")
        audio_response = requests.get(download_url, timeout=30)
        audio_response.raise_for_status()
        
        # Log audio response details
        logger.info(f"Audio download status: {audio_response.status_code}")
        logger.info(f"Audio content type: {audio_response.headers.get('content-type')}")
        logger.info(f"Audio content length: {audio_response.headers.get('content-length')}")
        
        # Get audio data
        audio_data = audio_response.content
        if not audio_data:
            logger.error("No audio data received")
            raise ValueError("No audio data received")
            
        logger.info(f"Successfully downloaded {len(audio_data)} bytes")
        return audio_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {str(e)}")
        raise ValueError(f"Request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
