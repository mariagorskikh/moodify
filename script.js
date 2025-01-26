// API endpoint
const API_URL = 'https://moodify-backend-app-8d6fcd4a2d68.herokuapp.com';

document.addEventListener('DOMContentLoaded', () => {
    const youtubeInput = document.getElementById('youtube-link');
    const emojiContainer = document.querySelector('.emoji-container');
    const loadingDiv = document.getElementById('loading');
    const audioClip = document.getElementById('audio-clip');
    const buttonContainer = document.querySelector('.button-container');
    const retryButton = document.getElementById('retry');
    const shareButton = document.getElementById('share');

    let selectedVibe = null;
    let currentAudioUrl = null;

    const vibes = [
        { emoji: '🌙', type: 'slow_reverb', name: 'Dreamy' },
        { emoji: '🎉', type: 'energetic', name: 'Energetic' },
        { emoji: '🖤', type: 'dark', name: 'Dark' },
        { emoji: '💖', type: 'cute', name: 'Cute' },
        { emoji: '😎', type: 'cool', name: 'Cool' },
        { emoji: '🌈', type: 'happy', name: 'Happy' },
        { emoji: '🔥', type: 'intense', name: 'Intense' },
        { emoji: '🎶', type: 'melodic', name: 'Melodic' },
        { emoji: '🌿', type: 'chill', name: 'Chill' },
        { emoji: '💤', type: 'sleepy', name: 'Sleepy' }
    ];

    // Create emoji buttons
    vibes.forEach(vibe => {
        const emojiWrapper = document.createElement('div');
        emojiWrapper.className = 'emoji-wrapper';
        
        const emojiButton = document.createElement('button');
        emojiButton.className = 'emoji';
        emojiButton.textContent = vibe.emoji;
        emojiButton.onclick = () => selectVibe(vibe);

        const tooltip = document.createElement('span');
        tooltip.className = 'tooltip';
        tooltip.textContent = vibe.name;

        emojiWrapper.appendChild(emojiButton);
        emojiWrapper.appendChild(tooltip);
        emojiContainer.appendChild(emojiWrapper);
    });

    function selectVibe(vibe) {
        // Remove selection from all emojis
        document.querySelectorAll('.emoji').forEach(emoji => {
            emoji.classList.remove('selected');
        });

        // Add selection to clicked emoji
        const clickedEmoji = Array.from(document.querySelectorAll('.emoji'))
            .find(emoji => emoji.textContent === vibe.emoji);
        clickedEmoji.classList.add('selected');

        selectedVibe = vibe;
    }

    async function processYouTubeLink() {
        const url = youtubeInput.value.trim();
        if (!url || !selectedVibe) {
            alert('Please enter a YouTube URL and select a vibe!');
            return;
        }

        try {
            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            const response = await fetch(`${API_URL}/api/transform`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: selectedVibe.type
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to process audio');
            }

            const blob = await response.blob();
            currentAudioUrl = URL.createObjectURL(blob);
            
            audioClip.src = currentAudioUrl;
            audioClip.classList.remove('hidden');
            buttonContainer.classList.remove('hidden');
            audioClip.play();

        } catch (error) {
            alert(error.message);
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }

    // Add event listeners
    youtubeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            processYouTubeLink();
        }
    });

    retryButton.addEventListener('click', () => {
        // Clear current audio
        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
            currentAudioUrl = null;
        }
        audioClip.classList.add('hidden');
        buttonContainer.classList.add('hidden');
        processYouTubeLink();
    });

    shareButton.addEventListener('click', async () => {
        if (currentAudioUrl) {
            try {
                await navigator.share({
                    title: 'Check out this transformed audio!',
                    text: 'Listen to this cool audio transformation I made with Moodify!',
                    url: window.location.href
                });
            } catch (err) {
                console.log('Error sharing:', err);
            }
        }
    });
});