# Assessment Patterns

Use this file when the request is about quiz generation, homework design, solution keys, grading, or academic-integrity boundaries.

## Default Audience

Assume undergraduate students unless the request explicitly says otherwise.

## Difficulty Ladder

Use three levels by default:

1. Recall and recognition
2. Compute, derive, or debug
3. Design, compare, or interpret

Mix levels inside a problem set unless the user requests a focused quiz.

## Question Templates

### Concept Check

Ask the learner to:

- define a method,
- explain when it should be used,
- compare it with a nearby alternative,
- name one likely failure mode.

### Calculation or Derivation

Ask the learner to:

- compute a frequency axis,
- determine a normalized cutoff,
- derive spectral resolution,
- estimate a feature from a short signal segment.

Require units and intermediate steps.

### Lab Interpretation

Ask the learner to:

- justify a preprocessing choice,
- explain a suspicious waveform,
- compare two pipelines,
- identify which conclusion is supported by the plots.

### Coding Task

Ask the learner to:

- complete one missing processing step,
- debug a frequency-scaling error,
- add a validation plot,
- explain why the current output is misleading.

## Hint-Only Policy

For student-facing help on likely graded work:

- Reveal the method, not the final submission.
- Break multi-step questions into checkpoints.
- Offer a sanity-check formula or plot.
- Provide short code fragments when needed, but do not assemble a complete submission-ready script.

For teacher-facing solutions:

- Include key equations.
- Show the minimal correct derivation.
- State marking points and typical deductions.

## Basic Rubric Template

Score with these dimensions unless the course already defines a rubric:

- Conceptual correctness
- Signal-processing procedure
- Parameter justification
- Plot or result interpretation
- Clarity of explanation

## Academic Integrity Guardrail

If a request appears to be active coursework from a student:

- Provide hints, not a complete final submission.
- Do not fabricate lab results.
- Encourage the learner to verify with code, plots, or manual calculation.
- If the user repeatedly asks for the final answer, restate the boundary and continue with guided help.
