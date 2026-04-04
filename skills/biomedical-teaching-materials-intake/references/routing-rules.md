# Routing Rules

## Folder Placement

Use these folders when organizing new materials:

- `materials/course-slides/`: chapter slides and lecture decks
- `materials/lecture-notes/`: chapter notes, summaries, concept sheets
- `materials/lab-guides/`: experiment manuals, procedures, result interpretation guides
- `materials/assignments/`: assignment prompts and instructions
- `materials/faq/`: repetitive questions and software usage notes
- `materials/rubrics/`: grading rules and report expectations

## Normalized File Names

Prefer names that expose topic and purpose directly.

Examples:

- `2026s_ch03_ecg_qrs_detection.pdf`
- `2026s_lab02_ecg_preprocessing.pdf`
- `2026s_ch05_eeg_artifact_removal.pdf`
- `faq_assignment1_sampling_aliasing.md`

Avoid names such as:

- `final.pdf`
- `new-version2.pdf`
- `lecture revised latest.pdf`

## Source Group Mapping

Use these mappings unless the project later changes its routing schema:

- general DSP and methods -> `theory_core`
- ECG topics -> `ecg_core`
- EMG topics -> `emg_core`
- HDsEMG topics -> `hdsemg_core`
- EEG topics -> `eeg_core`
- PPG topics -> `ppg_core`
- fNIRS topics -> `fnirs_core`
- assignments, rubrics, FAQ -> `assignment_support`
- lab manuals -> `lab_core` if available; otherwise the signal-specific core group plus a note

## Refresh Decisions

Recommend `rebuild_index` when:

- local vector index exists and new content was added
- existing documents changed materially
- routing depends on the indexed corpus

Recommend `redeploy_cloud` when:

- the Streamlit Cloud app reads files from the repository and those files changed
- secrets changed or provider defaults changed

Recommend `no_refresh_needed` only when:

- no new retrieval source was added
- only a report or plan document changed
- no app behavior or corpus selection changed
