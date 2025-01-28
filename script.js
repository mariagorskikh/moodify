document.addEventListener('DOMContentLoaded', () => {
    const emojiContainer = document.querySelector('.emoji-container');
    const youtubeInput = document.getElementById('youtube-link');
    const loadingDiv = document.getElementById('loading');
    const audioClip = document.getElementById('audio-clip');
    const buttonContainer = document.querySelector('.button-container');
    const saveButton = document.getElementById('save-clip');
    const retryButton = document.getElementById('retry');
    const shareButton = document.getElementById('share');
    const audioEditor = document.getElementById('audio-editor');
    const startTimeInput = document.getElementById('start-time');
    const endTimeInput = document.getElementById('end-time');
    const splitButton = document.getElementById('split-clip');
    const waveformCanvas = document.getElementById('waveform');
    const timeMarker = document.getElementById('time-marker');
    const ctx = waveformCanvas.getContext('2d');
    const previewSplitButton = document.getElementById('preview-split');
    const selectionOverlay = document.getElementById('selection-overlay');
    const setCurrentButtons = document.querySelectorAll('.set-current-time');
    const trackMixer = document.getElementById('track-mixer');
    const trackUpload = document.getElementById('track-upload');
    const trackList = document.querySelector('.track-list');
    const previewMixButton = document.getElementById('preview-mix');
    const downloadMixButton = document.getElementById('download-mix');
    const trackTemplate = document.getElementById('track-template');

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

    let selectedVibe = null;
    let processedAudioUrl = null;
    let audioContext = null;
    let audioBuffer = null;
    let tracks = [];
    let isPreviewPlaying = false;

    // Clear existing emoji container
    emojiContainer.innerHTML = '';

    // Create emoji buttons with tooltips
    vibes.forEach(vibe => {
        const emojiWrapper = document.createElement('div');
        emojiWrapper.classList.add('emoji-wrapper');
        
        const emojiButton = document.createElement('button');
        emojiButton.className = 'emoji';
        emojiButton.textContent = vibe.emoji;
        
        const tooltip = document.createElement('span');
        tooltip.classList.add('tooltip');
        tooltip.textContent = vibe.name;
        
        emojiWrapper.appendChild(emojiButton);
        emojiWrapper.appendChild(tooltip);
        emojiContainer.appendChild(emojiWrapper);

        emojiButton.addEventListener('click', () => {
            // Remove selected class from all emojis
            document.querySelectorAll('.emoji').forEach(e => e.classList.remove('selected'));
            // Add selected class to clicked emoji
            emojiButton.classList.add('selected');
            selectedVibe = vibe;
            
            // If we have a processed audio and select a new vibe, enable retry
            if (processedAudioUrl) {
                buttonContainer.classList.remove('hidden');
            }
        });
    });

    async function processYouTubeLink(url, vibeType) {
        try {
            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            const response = await fetch('http://localhost:5005/api/transform', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: vibeType
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to process audio');
            }

            const blob = await response.blob();
            
            // Revoke the old URL if it exists
            if (processedAudioUrl) {
                URL.revokeObjectURL(processedAudioUrl);
            }
            
            processedAudioUrl = URL.createObjectURL(blob);
            
            audioClip.src = processedAudioUrl;
            audioClip.classList.remove('hidden');
            buttonContainer.classList.remove('hidden');
            
            // Start playing automatically
            try {
                await audioClip.play();
            } catch (playError) {
                console.log('Auto-play failed:', playError);
            }
            
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }

    async function drawWaveform(audioElement) {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
        }

        try {
            const response = await fetch(audioElement.src);
            const arrayBuffer = await response.arrayBuffer();
            audioBuffer = await audioContext.decodeAudioData(arrayBuffer);

            // Set up canvas
            const canvas = waveformCanvas;
            const width = canvas.width = canvas.offsetWidth;
            const height = canvas.height = canvas.offsetHeight;
            const centerY = height / 2;

            // Clear canvas
            ctx.clearRect(0, 0, width, height);

            // Draw waveform
            ctx.beginPath();
            ctx.strokeStyle = '#00fff5';
            ctx.lineWidth = 2;

            const data = audioBuffer.getChannelData(0);
            const step = Math.ceil(data.length / width);
            const amp = height / 2;

            for (let i = 0; i < width; i++) {
                const min = Math.min(...data.slice(i * step, (i + 1) * step));
                const max = Math.max(...data.slice(i * step, (i + 1) * step));
                
                ctx.moveTo(i, centerY + min * amp);
                ctx.lineTo(i, centerY + max * amp);
            }

            ctx.stroke();

            // Update end time input with audio duration
            endTimeInput.value = audioBuffer.duration.toFixed(1);
            endTimeInput.max = audioBuffer.duration;
        } catch (error) {
            console.error('Error drawing waveform:', error);
        }
    }

    youtubeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && selectedVibe) {
            const url = youtubeInput.value.trim();
            if (url) {
                processYouTubeLink(url, selectedVibe.type);
            }
        }
    });

    saveButton.addEventListener('click', () => {
        if (processedAudioUrl) {
            const a = document.createElement('a');
            a.href = processedAudioUrl;
            a.download = `moodify_${selectedVibe.type}.mp3`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    retryButton.addEventListener('click', () => {
        const url = youtubeInput.value.trim();
        if (url && selectedVibe) {
            processYouTubeLink(url, selectedVibe.type);
        }
    });

    shareButton.addEventListener('click', () => {
        if (processedAudioUrl) {
            // Remove any existing share menu
            const existingMenu = document.querySelector('.share-menu');
            if (existingMenu) {
                existingMenu.remove();
            }

            const shareMenu = document.createElement('div');
            shareMenu.className = 'share-menu';
            
            const shareOptions = [
                { name: 'TikTok', icon: '🎵', url: 'https://www.tiktok.com/upload?lang=en' },
                { name: 'X (Twitter)', icon: '🐦', url: `https://twitter.com/intent/tweet?text=${encodeURIComponent('Check out this awesome music remix I made with Moodify! 🎵✨')}` },
                { name: 'Facebook', icon: '📱', url: 'https://www.facebook.com/sharer/sharer.php?u=' + encodeURIComponent(window.location.href) },
                { name: 'Copy Link', icon: '🔗', action: 'copy' }
            ];

            shareOptions.forEach(option => {
                const button = document.createElement('button');
                button.className = 'share-option';
                button.innerHTML = `${option.icon} ${option.name}`;
                
                button.addEventListener('click', async () => {
                    if (option.action === 'copy') {
                        try {
                            await navigator.clipboard.writeText(processedAudioUrl);
                            alert('Link copied to clipboard!');
                        } catch (err) {
                            alert('Failed to copy link');
                        }
                    } else {
                        window.open(option.url, '_blank');
                    }
                    shareMenu.remove();
                });
                
                shareMenu.appendChild(button);
            });

            // Position the menu below the share button
            const buttonRect = shareButton.getBoundingClientRect();
            shareMenu.style.position = 'absolute';
            shareMenu.style.top = `${buttonRect.bottom + 10}px`;
            shareMenu.style.left = `${buttonRect.left}px`;
            
            // Close menu when clicking outside
            const closeMenu = (e) => {
                if (!shareMenu.contains(e.target) && e.target !== shareButton) {
                    shareMenu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            };
            
            // Add a slight delay before adding the click listener to prevent immediate closure
            setTimeout(() => {
                document.addEventListener('click', closeMenu);
            }, 100);

            document.body.appendChild(shareMenu);
        }
    });

    // Update selection overlay position
    function updateSelectionOverlay() {
        const startTime = parseFloat(startTimeInput.value);
        const endTime = parseFloat(endTimeInput.value);
        const duration = audioClip.duration;
        
        if (!duration) return;
        
        const startPercent = (startTime / duration) * 100;
        const endPercent = (endTime / duration) * 100;
        
        selectionOverlay.style.left = `${startPercent}%`;
        selectionOverlay.style.width = `${endPercent - startPercent}%`;
    }

    // Set current time buttons
    setCurrentButtons.forEach(button => {
        button.addEventListener('click', () => {
            const target = button.dataset.target;
            const currentTime = audioClip.currentTime;
            
            if (target === 'start') {
                startTimeInput.value = currentTime.toFixed(1);
            } else {
                endTimeInput.value = currentTime.toFixed(1);
            }
            
            updateSelectionOverlay();
        });
    });

    // Preview split functionality
    previewSplitButton.addEventListener('click', () => {
        const startTime = parseFloat(startTimeInput.value);
        const endTime = parseFloat(endTimeInput.value);
        
        if (endTime <= startTime) {
            alert('End time must be greater than start time');
            return;
        }
        
        audioClip.currentTime = startTime;
        audioClip.play();
        
        const stopPreview = () => {
            if (audioClip.currentTime >= endTime) {
                audioClip.pause();
                audioClip.removeEventListener('timeupdate', stopPreview);
            }
        };
        
        audioClip.addEventListener('timeupdate', stopPreview);
    });

    // Update selection when time inputs change
    startTimeInput.addEventListener('input', updateSelectionOverlay);
    endTimeInput.addEventListener('input', updateSelectionOverlay);

    // Click on waveform to set time
    waveformCanvas.addEventListener('click', (e) => {
        const rect = waveformCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const progress = x / rect.width;
        const time = audioClip.duration * progress;
        
        audioClip.currentTime = time;
        
        // Update the nearest time input
        const startDiff = Math.abs(time - parseFloat(startTimeInput.value));
        const endDiff = Math.abs(time - parseFloat(endTimeInput.value));
        
        if (startDiff < endDiff) {
            startTimeInput.value = time.toFixed(1);
        } else {
            endTimeInput.value = time.toFixed(1);
        }
        
        updateSelectionOverlay();
    });

    // Split button functionality
    splitButton.addEventListener('click', async () => {
        const startTime = parseFloat(startTimeInput.value);
        const endTime = parseFloat(endTimeInput.value);

        if (endTime <= startTime) {
            alert('End time must be greater than start time');
            return;
        }

        if (!processedAudioUrl) {
            alert('No audio file loaded');
            return;
        }

        try {
            splitButton.disabled = true;
            splitButton.textContent = 'Processing...';

            // First, fetch the audio file and convert it to a blob
            const audioResponse = await fetch(processedAudioUrl);
            const audioBlob = await audioResponse.blob();

            // Create form data to send the file
            const formData = new FormData();
            formData.append('audio_file', audioBlob, 'audio.mp3');
            formData.append('start_time', startTime);
            formData.append('end_time', endTime);

            const response = await fetch('http://localhost:5005/api/split', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to split audio');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // Trigger download
            const a = document.createElement('a');
            a.href = url;
            a.download = `moodify_split_${startTime}-${endTime}.mp3`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            alert('Error splitting audio: ' + error.message);
        } finally {
            splitButton.disabled = false;
            splitButton.textContent = 'Download Split';
        }
    });

    // Update time marker position during playback
    audioClip.addEventListener('timeupdate', () => {
        const progress = audioClip.currentTime / audioClip.duration;
        timeMarker.style.left = `${progress * 100}%`;
    });

    // Show audio editor when audio is loaded
    audioClip.addEventListener('loadedmetadata', () => {
        audioEditor.classList.remove('hidden');
        drawWaveform(audioClip);
        endTimeInput.value = audioClip.duration.toFixed(1);
        updateSelectionOverlay();
        trackMixer.classList.remove('hidden');
    });

    // Add audio player controls
    audioClip.addEventListener('play', () => {
        audioClip.classList.add('playing');
    });

    audioClip.addEventListener('pause', () => {
        audioClip.classList.remove('playing');
    });

    audioClip.addEventListener('ended', () => {
        audioClip.classList.remove('playing');
    });

    // Handle track upload
    trackUpload.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        for (const file of files) {
            await addTrack(file);
        }
        trackUpload.value = '';
    });

    // Add a new track
    async function addTrack(file) {
        const track = {
            file,
            audioBuffer: null,
            audioContext: null,
            gainNode: null,
            sourceNode: null
        };

        // Create track element from template
        const trackElement = document.importNode(trackTemplate.content, true).firstElementChild;
        trackElement.querySelector('.track-name').textContent = file.name;
        
        // Set up track controls
        const volumeSlider = trackElement.querySelector('.volume-slider');
        const volumeValue = trackElement.querySelector('.volume-value');
        const startTimeInput = trackElement.querySelector('.start-time');
        const trimLengthInput = trackElement.querySelector('.trim-length');
        const removeButton = trackElement.querySelector('.remove-track');
        const waveformCanvas = trackElement.querySelector('.waveform-canvas');

        // Draw waveform
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const arrayBuffer = await file.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        track.audioBuffer = audioBuffer;
        track.audioContext = audioContext;
        
        drawWaveformToCanvas(waveformCanvas, audioBuffer);
        trimLengthInput.value = audioBuffer.duration.toFixed(1);

        // Set up event listeners
        volumeSlider.addEventListener('input', () => {
            volumeValue.textContent = volumeSlider.value + '%';
            if (track.gainNode) {
                track.gainNode.gain.value = volumeSlider.value / 100;
            }
        });

        removeButton.addEventListener('click', () => {
            const index = tracks.indexOf(track);
            if (index > -1) {
                tracks.splice(index, 1);
                trackElement.remove();
                stopPreview();
            }
        });

        // Add track to list
        tracks.push(track);
        trackList.appendChild(trackElement);
    }

    // Preview mix
    previewMixButton.addEventListener('click', async () => {
        if (isPreviewPlaying) {
            stopPreview();
        } else {
            await playPreview();
        }
    });

    async function playPreview() {
        stopPreview();
        isPreviewPlaying = true;
        previewMixButton.textContent = 'Stop Preview';

        for (const track of tracks) {
            const trackElement = trackList.children[tracks.indexOf(track)];
            const volumeSlider = trackElement.querySelector('.volume-slider');
            const startTimeInput = trackElement.querySelector('.start-time');
            
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const gainNode = audioContext.createGain();
            const sourceNode = audioContext.createBufferSource();
            
            sourceNode.buffer = track.audioBuffer;
            sourceNode.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            gainNode.gain.value = volumeSlider.value / 100;
            sourceNode.start(0, parseFloat(startTimeInput.value));
            
            track.audioContext = audioContext;
            track.gainNode = gainNode;
            track.sourceNode = sourceNode;
        }
    }

    function stopPreview() {
        isPreviewPlaying = false;
        previewMixButton.textContent = 'Preview Mix';

        for (const track of tracks) {
            if (track.sourceNode) {
                track.sourceNode.stop();
                track.audioContext.close();
                track.sourceNode = null;
                track.gainNode = null;
                track.audioContext = null;
            }
        }
    }

    // Download mix
    downloadMixButton.addEventListener('click', async () => {
        if (tracks.length === 0) {
            alert('Please add some tracks to mix');
            return;
        }

        try {
            downloadMixButton.disabled = true;
            downloadMixButton.textContent = 'Processing...';

            const formData = new FormData();
            
            tracks.forEach((track, i) => {
                const trackElement = trackList.children[i];
                const volumeSlider = trackElement.querySelector('.volume-slider');
                const startTimeInput = trackElement.querySelector('.start-time');
                const trimLengthInput = trackElement.querySelector('.trim-length');
                
                formData.append(`track_${i}`, track.file);
                formData.append(`volume_${i}`, volumeSlider.value);
                formData.append(`start_time_${i}`, startTimeInput.value);
                formData.append(`trim_length_${i}`, trimLengthInput.value);
            });

            const response = await fetch('http://localhost:5005/api/mix', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to mix tracks');
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            const a = document.createElement('a');
            a.href = url;
            a.download = 'mixed_track.mp3';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            alert('Error mixing tracks: ' + error.message);
        } finally {
            downloadMixButton.disabled = false;
            downloadMixButton.textContent = 'Download Mix';
        }
    });

    // Helper function to draw waveform
    function drawWaveformToCanvas(canvas, audioBuffer) {
        const ctx = canvas.getContext('2d');
        const data = audioBuffer.getChannelData(0);
        const step = Math.ceil(data.length / canvas.width);
        const amp = canvas.height / 2;

        ctx.fillStyle = 'rgba(0, 136, 255, 0.2)';
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (let i = 0; i < canvas.width; i++) {
            let min = 1.0;
            let max = -1.0;

            for (let j = 0; j < step; j++) {
                const datum = data[(i * step) + j];
                if (datum < min) min = datum;
                if (datum > max) max = datum;
            }

            ctx.fillRect(i, (1 + min) * amp, 1, Math.max(1, (max - min) * amp));
        }
    }
});