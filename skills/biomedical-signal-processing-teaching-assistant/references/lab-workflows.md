# Lab Workflows

Use this file when the request is about experiment design, data analysis, report guidance, or debugging a processing pipeline.

## Shared Lab Workflow

Apply this sequence unless the lab already defines a stricter protocol:

1. Inspect the raw waveform and confirm units, sampling rate, channel meaning, and recording duration.
2. Remove obvious acquisition artifacts or mark unusable segments.
3. Apply only the minimum necessary preprocessing.
4. Plot the intermediate result after each major step.
5. Extract features tied to the experiment goal.
6. Validate with summary statistics and qualitative inspection.
7. Explain limitations before drawing conclusions.

## ECG

Typical tasks:

- Baseline wander removal
- Power-line suppression
- QRS detection
- Heart-rate or interval estimation

Suggested pipeline:

1. Detrend or high-pass to reduce baseline drift.
2. Apply notch filtering only if line noise is visible or documented.
3. Band-limit for QRS enhancement if detection is the goal.
4. Detect peaks and compute RR intervals.
5. Review missed beats and false positives visually.

Common pitfalls:

- Using a cutoff that distorts ST or T-wave morphology
- Reporting heart rate from too short or artifact-heavy segments
- Ignoring refractory-period constraints in peak detection

## EMG

Typical tasks:

- Muscle activation timing
- Envelope extraction
- Fatigue analysis
- Synergy or feature analysis

Suggested pipeline:

1. Remove DC offset.
2. Band-pass within an application-appropriate EMG band.
3. Rectify when envelope or amplitude features are required.
4. Low-pass or smooth to obtain the envelope.
5. Normalize if comparing muscles, trials, or subjects.

Common pitfalls:

- Treating rectified EMG as interchangeable with raw EMG
- Comparing amplitudes without normalization rules
- Using smoothing windows that hide activation timing

## HDsEMG

Typical tasks:

- Channel-grid visualization
- Spatial activation mapping
- Motor-unit decomposition discussion
- Region-based feature comparison

Suggested pipeline:

1. Confirm grid layout, missing channels, and electrode orientation.
2. Remove bad channels or mark them clearly.
3. Apply temporal preprocessing before any spatial summary.
4. Reshape channels back to the physical grid before plotting maps.
5. Report both temporal and spatial features.

Common pitfalls:

- Treating the channel vector as if spatial order does not matter
- Averaging across channels before checking bad electrodes
- Over-claiming motor-unit results without decomposition validation

## EEG

Typical tasks:

- Rhythm or band-power analysis
- Event-related analysis
- Artifact rejection
- Channel comparison

Suggested pipeline:

1. Set or verify the reference scheme.
2. Remove line noise and obvious motion or blink artifacts.
3. Epoch if the task is stimulus-locked.
4. Compute PSD, band power, or event-related averages.
5. Compare conditions with matched windows and channels.

Common pitfalls:

- Ignoring reference choice
- Mixing eyes-open and eyes-closed data without noting it
- Over-interpreting single-channel changes without context

## PPG

Typical tasks:

- Pulse detection
- Heart-rate estimation
- Pulse morphology comparison

Suggested pipeline:

1. Remove drift and motion-heavy segments where possible.
2. Smooth carefully without flattening peaks.
3. Detect pulses with adaptive thresholds if noise varies.
4. Check inter-beat interval plausibility.
5. Compare morphology only after aligning acquisition conditions.

Common pitfalls:

- Confusing motion artifacts with pulse peaks
- Reporting variability metrics from unstable peak detection
- Ignoring perfusion and sensor placement effects

## fNIRS

Typical tasks:

- Optical density conversion
- HbO and HbR trend analysis
- Task-evoked response comparison
- Channel-quality inspection

Suggested pipeline:

1. Verify source-detector layout and channel labeling.
2. Remove saturated or obviously corrupted channels.
3. Convert raw intensity to optical density if needed.
4. Apply motion-artifact handling and baseline correction.
5. Convert to HbO and HbR with the stated assumptions.
6. Compare task blocks with hemodynamic delay in mind.

Common pitfalls:

- Ignoring motion artifacts and slow drift
- Interpreting peak timing as if it were EEG-like
- Forgetting to state whether results are HbO, HbR, or total hemoglobin
