import requests
import re
import json
import logging
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    # Try parsing URL
    parsed_url = urlparse(url)
    
    # Check for youtu.be
    if parsed_url.netloc == 'youtu.be':
        return parsed_url.path[1:]
    
    # Check for youtube.com
    if parsed_url.netloc in ['youtube.com', 'www.youtube.com']:
        if parsed_url.path == '/watch':
            return parse_qs(parsed_url.query)['v'][0]
        elif parsed_url.path.startswith(('/embed/', '/v/')):
            return parsed_url.path.split('/')[2]
    
    return None

def get_video_info(video_id):
    """Get video info using YouTube's oEmbed endpoint."""
    try:
        url = f"https://www.youtube.com/oembed?url=http://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return None

def get_audio_url(video_id):
    """Get audio URL using a public API."""
    try:
        # Try using y2mate API
        url = "https://yt2mp3.info/api/single/mp3"
        payload = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "quality": "128"
        }
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        if 'url' in data:
            return data['url']
            
        raise ValueError("No audio URL found in response")
        
    except Exception as e:
        logger.error(f"Error getting audio URL: {str(e)}")
        raise ValueError(f"Failed to get audio URL: {str(e)}")

def download_audio(url):
    """Download audio from YouTube URL."""
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")
            
        # Get video info
        video_info = get_video_info(video_id)
        if not video_info:
            raise ValueError("Could not get video info")
            
        # Get audio URL
        audio_url = get_audio_url(video_id)
        if not audio_url:
            raise ValueError("Could not get audio URL")
            
        # Download audio
        response = requests.get(audio_url, stream=True)
        response.raise_for_status()
        
        return response.content
        
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
