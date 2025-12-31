# ECG Sound Simulator Implementation Plan

A single-page web application that simulates the rhythmic "beep" of an ECG machine using the Web Audio API, accompanied by a matching visual monitor.

## Proposed Changes

### [Web Audio Engine]
- Use `AudioContext` for high-precision timing.
- Synthesize the "beep" using a `Sine` oscillator at ~1000Hz (typical ECG frequency).
- Use `GainNode` to apply a sharp envelope (quick rise, quick decay) to avoid clicking and mimic the "pip" sound.
- Implement a `Scheduler` to handle the rhythmic pulsing based on a BPM (Beats Per Minute) setting.

### [UI/UX Design]
- **Theme**: "Medical Pro" aesthetics. Deep obsidian background with neon emerald green accents.
- **Visualizer**: A scrolling canvas visualizer that draws the characteristic P-QRS-T wave of a heartbeat.
- **Controls**: 
    - Master Power Switch (Start/Stop).
    - BPM Slider (40 - 180 BPM).
    - Volume Slider.
- **Technology**: Vanilla HTML, CSS, and JS (no frameworks for this self-contained demo).

### [File Structure]
- `index.html`: all-in-one, no external js/css, even inline an svg favicon!

## Verification Plan

### Automated Tests
- N/A for this simple UI/Audio project.

### Manual Verification
1.  **Audio Check**: Verify the "beep" sounds authentic and doesn't click or lag.
2.  **Rhythm Check**: Adjust BPM and ensure the sound follows precisely.
3.  **Visual Check**: The ECG line should pulse in sync with the audio beep.
4.  **UI Check**: Test full responsiveness and interactability of sliders.
