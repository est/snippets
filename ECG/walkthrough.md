# ECG Sound Simulator Walkthrough

I have completed the single-page ECG Sound Simulator. This application uses the Web Audio API for sound synthesis and HTML5 Canvas for real-time visualization.

## Key Features

- **High-Fidelity Audio**: Synthesizes medical-grade "beeps" with precise timing and volume control.
- **Dynamic Visualizer**: A scrolling ECG monitor that pulses in sync with the audio.
- **Adjustable Heart Rate**: Control BPM (40-180) in real-time.
- **Sleek Interface**: A premium "medical pro" dark theme with neon green accents and glassmorphism.
- **All-in-One**: A single HTML file with no external dependencies (custom SVG favicon included).

## Implementation Details

- **Audio**: Uses `AudioContext` and `OscillatorNode` with a sharp gain envelope to mimic the authentic sound of a cardiac monitor.
- **Visuals**: A custom `getECGValue` function simulates the organic P-QRS-T waveform of a human heartbeat.
- **Synchronization**: The sound scheduler triggers the visual pulse state, ensuring perfect audio-visual alignment.

## How to Test

1. Open the [index.html](file:///Users/lambdaq/.gemini/antigravity/scratch/ecg_simulator/index.html) file in any modern web browser (Chrome, Safari, Edge).
2. Click **"Start Monitor"** to begin the simulation.
3. Use the sliders to adjust the heart rate and volume.

---

### Code Structure Preview

```html
<!-- One-file architecture -->
<style>
  /* Medical Pro Theme */
</style>

<canvas id="ecgCanvas"></canvas>

<script>
  // Web Audio Context & Oscillator logic
  // Canvas drawing loop (P-QRS-T wave simulation)
</script>
```
