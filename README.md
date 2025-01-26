# Moodify 🎵

A web application that transforms YouTube videos into mood-based audio experiences. Apply different vibes to your favorite songs using audio effects like slow reverb, energetic beats, and more.

## Features

- 🎧 Download and process audio from YouTube videos
- 🎨 Multiple mood transformations:
  - 🌙 Dreamy (slow reverb)
  - 🎉 Energetic
  - 🖤 Dark
  - 💖 Cute
  - 😎 Cool
  - 🌈 Happy
  - 🔥 Intense
  - 🎶 Melodic
  - 🌿 Chill
  - 💤 Sleepy
- 🎵 Real-time audio playback in browser
- ✨ Beautiful, modern UI with emoji selectors

## Prerequisites

- Python 3.8+
- FFmpeg
- Node.js (for development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moodify.git
cd moodify
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Install FFmpeg:
- Mac: `brew install ffmpeg`
- Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)
- Linux: `sudo apt-get install ffmpeg`

## Usage

1. Start the Flask server:
```bash
python app.py
```

2. Open `index.html` in your web browser

3. Paste a YouTube URL and select a mood emoji

4. Wait for processing and enjoy your transformed audio!

## Tech Stack

- Backend: Flask
- Audio Processing: FFmpeg
- YouTube Download: yt-dlp
- Frontend: Vanilla JavaScript
- Styling: CSS with modern animations

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
