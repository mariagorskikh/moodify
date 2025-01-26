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
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
            
        logger.info(f"Extracted video ID: {video_id}")
        
        # First API endpoint - get download link
        api_url = "https://youtube-mp36.p.rapidapi.com/dl"
        querystring = {"id": video_id}
        
        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "youtube-mp36.p.rapidapi.com"
        }
        
        # Get download link
        logger.info("Requesting download link from API...")
        logger.info(f"API URL: {api_url}")
        logger.info(f"Query params: {querystring}")
        
        response = requests.get(api_url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        
        logger.info(f"API response status: {response.status_code}")
        logger.info(f"API response headers: {response.headers}")
        
        try:
            data = response.json()
            logger.info(f"API response data: {data}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            raise ValueError("Invalid response from API")
            
        if not isinstance(data, dict):
            logger.error(f"Unexpected response format: {data}")
            raise ValueError("Invalid response format from API")
            
        # Check status
        status = data.get('status')
        if status != 'ok':
            logger.error(f"API returned non-ok status: {status}")
            raise ValueError(f"API error: {data.get('msg', 'Unknown error')}")
            
        # Get download URL
        download_url = data.get('link')
        if not download_url:
            logger.error(f"No download URL in response: {data}")
            raise ValueError("No download URL in API response")
            
        logger.info(f"Got download URL: {download_url}")
        
        # Download the audio file
        logger.info("Downloading audio file...")
        audio_response = requests.get(download_url, timeout=30)
        audio_response.raise_for_status()
        
        logger.info(f"Audio download status: {audio_response.status_code}")
        logger.info(f"Audio response headers: {audio_response.headers}")
        
        # Get the audio data
        audio_data = audio_response.content
        
        # Verify we got some data
        if not audio_data:
            logger.error("No audio data received")
            raise ValueError("No audio data received")
            
        logger.info(f"Successfully downloaded {len(audio_data)} bytes of audio")
        return audio_data
        
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        raise ValueError("Request timed out - please try again")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise ValueError("Invalid response from API")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
