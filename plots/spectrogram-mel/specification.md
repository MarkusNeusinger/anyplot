# spectrogram-mel: Mel-Spectrogram for Audio Analysis

## Description

A mel-spectrogram displaying the power spectrum of an audio signal with the frequency axis warped to the mel scale, which approximates human auditory perception. Unlike a standard spectrogram with a linear frequency axis, the mel-spectrogram compresses higher frequencies and expands lower frequencies, making perceptually similar sounds visually closer together. This is the foundational input representation for modern audio machine learning pipelines including speech recognition, speaker identification, and music information retrieval.

## Applications

- Preprocessing audio features for neural network input in speech recognition (ASR) systems
- Visualizing and comparing timbral characteristics of musical instruments or vocal qualities
- Analyzing environmental sound classification datasets for acoustic scene detection
- Debugging and inspecting audio augmentation pipelines in ML training workflows

## Data

- `audio_signal` (numeric array) - raw audio waveform samples (mono)
- `sample_rate` (numeric) - sampling rate in Hz (e.g., 22050 or 16000)
- `n_mels` (integer) - number of mel filter banks (typically 64 or 128)
- Size: 1-10 seconds of audio (22050-220500 samples at 22050 Hz)
- Example: synthesized audio with a melody or speech-like signal combining multiple frequency components

## Notes

- Convert power spectrogram to decibel scale (log scale) for better visual dynamic range
- Use a sequential colormap (e.g., magma, inferno, or viridis) for clear intensity representation
- X-axis should show time in seconds, y-axis should show mel-scaled frequency with Hz labels at key mel band edges
- Include a colorbar labeled in dB
- Typical parameters: n_fft=2048, hop_length=512, n_mels=128
- Libraries like librosa provide mel-spectrogram computation; implementations should generate or synthesize audio data rather than loading external files
