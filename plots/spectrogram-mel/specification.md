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

## What a good version looks like

- A good version shows: time in seconds on the x axis and mel-scaled frequency on the y axis with Hz labels at key mel band edges, as the Notes ask, so equal steps in Hz take less room toward the top of the axis.
- A good version shows: power on a decibel scale in a sequential colormap, with a color bar labeled in dB, as the Notes ask.
- A good version shows: the mel bands as contiguous rows and the frames as contiguous columns, each cell at its time and band, tiling the image.
- A good version shows: a dynamic range in which harmonics, formants or note onsets stand out against the quieter background, instead of a nearly uniform field.
- Expected, not a defect: low frequencies stretched and high frequencies compressed compared with a linear spectrogram, harmonics that crowd together toward the top, fine high-frequency detail blurred by the wider upper bands, and dark regions where the signal has no energy.
