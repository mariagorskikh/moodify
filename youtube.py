import requests
import re
import json
import logging
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

def extract_video_id(url):
    """Extract video ID from YouTube URL."""
    try:
        # Try parsing URL
        parsed_url = urlparse(url)
        
        # Check for youtu.be
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path[1:]
        
        # Check for youtube.com
        if parsed_url.netloc in ['youtube.com', 'www.youtube.com']:
            if parsed_url.path == '/watch':
                return parse_qs(parsed_url.query).get('v', [None])[0]
            elif parsed_url.path.startswith(('/embed/', '/v/')):
                return parsed_url.path.split('/')[2]
        
        # Try regex as fallback
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
        
    except Exception as e:
        logger.error(f"Error extracting video ID: {str(e)}")
        return None

def download_audio(url):
    """Download audio from YouTube URL using RapidAPI."""
    try:
        # Extract video ID
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
            
        logger.info(f"Extracted video ID: {video_id}")
        
        # Use RapidAPI YouTube MP3 Converter
        api_url = "https://youtube-mp3-downloader2.p.rapidapi.com/ytmp3/ytmp3/"
        querystring = {"url": f"https://www.youtube.com/watch?v={video_id}"}
        
        headers = {
            "X-RapidAPI-Key": "7481d3b186msh641c6fc52c76f5fp1f3e47jsn0b2ad8d0a3c7",
            "X-RapidAPI-Host": "youtube-mp3-downloader2.p.rapidapi.com"
        }
        
        # Get download link
        logger.info("Requesting download link from API...")
        response = requests.get(api_url, headers=headers, params=querystring)
        response.raise_for_status()
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON response: {response.text}")
            raise ValueError("Invalid response from API")
            
        if not isinstance(data, dict):
            logger.error(f"Unexpected response format: {data}")
            raise ValueError("Invalid response format from API")
            
        # Get download URL from response
        download_url = data.get('link')
        if not download_url:
            logger.error(f"No download URL in response: {data}")
            raise ValueError("No download URL in API response")
            
        logger.info("Got download URL, downloading audio...")
        
        # Download the audio file
        audio_response = requests.get(download_url, stream=True)
        audio_response.raise_for_status()
        
        # Check content type
        content_type = audio_response.headers.get('content-type', '')
        if not content_type.startswith('audio/'):
            logger.error(f"Invalid content type: {content_type}")
            raise ValueError("Invalid content type in response")
            
        # Get the audio data
        audio_data = audio_response.content
        
        # Verify we got some data
        if not audio_data:
            raise ValueError("No audio data received")
            
        logger.info(f"Successfully downloaded {len(audio_data)} bytes of audio")
        return audio_data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise ValueError("Invalid response from API")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise ValueError(f"Failed to download audio: {str(e)}")
