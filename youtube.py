import requests
import re
import json
import logging
from urllib.parse import parse_qs, urlparse
import os
import time

logger = logging.getLogger(__name__)

# Get API key from environment variable or use default
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '7481d3b186msh641c6fc52c76f5fp1f3e47jsn0b2ad8d0a3c7')

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
        # Log environment
        api_key = os.getenv('RAPIDAPI_KEY')
        logger.info(f"API Key present: {bool(api_key)}")
        
        # Extract video ID
        video_id = extract_video_id(url)
        logger.info(f"Video ID: {video_id}")
        
        # API configuration
        api_url = "https://youtube-mp36.p.rapidapi.com/dl"
        querystring = {"id": video_id}
        
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": "youtube-mp36.p.rapidapi.com"
        }
        
        # Log request details
        logger.info(f"Making request to: {api_url}")
        logger.info(f"Query params: {querystring}")
        
        # Get download link
        response = requests.get(api_url, headers=headers, params=querystring, timeout=30)
        
        # Log response details
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response headers: {response.headers}")
        
        try:
            response_text = response.text
            logger.info(f"Response text: {response_text}")
            data = response.json()
            logger.info(f"Response data: {data}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            logger.error(f"Raw response: {response_text}")
            raise ValueError("Invalid JSON response from API")
        
        # Check API response
        if 'status' not in data:
            logger.error(f"Unexpected API response format: {data}")
            raise ValueError("Invalid API response format")
            
        if data['status'] != 'ok':
            error_msg = data.get('msg', 'Unknown API error')
            logger.error(f"API error: {error_msg}")
            raise ValueError(f"API error: {error_msg}")
            
        # Get download URL
        download_url = data.get('link')
        if not download_url:
            logger.error("No download URL in response")
            raise ValueError("No download URL in response")
            
        logger.info(f"Download URL: {download_url}")
        
        # Download audio file
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
        logger.error(f"Unexpected error: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
