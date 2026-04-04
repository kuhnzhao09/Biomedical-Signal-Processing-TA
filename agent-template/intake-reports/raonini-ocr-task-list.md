# Raonini OCR Task List

## Summary

- Source directory: `materials/raonini/pdf-export`
- Current `needs_ocr` files: `6`
- Current suggested source group: `theory_core`
- Recommended workflow: `OCR -> rerun intake scan -> update retrieval config if promoted to ready_pdf`

## Priority Rules

- `P1`: foundational theory or method-core slides that should enter the knowledge base early
- `P2`: useful supporting theory that can follow after the mainline topics are searchable
- `P3`: narrower application material that can wait until the core OCR backlog is cleared

## OCR Tasks

| Priority | File | Suggested Group | OCR Signal | Why Process Early | Next Step |
|---|---|---|---|---|---|
| `P1` | `第5章第2讲有限脉冲响应法求解维纳-霍夫方程.pdf` | `theory_core` | `6 pages, 701 chars, 2 text pages` | Wiener-Hopf solving methods connect directly to the filtering sequence already entering the corpus. | Run OCR, confirm formulas and headings are extractable, rerun intake, then review for `theory_core`. |
| `P1` | `第8章第1讲自适应滤波基本原理.pdf` | `theory_core` | `6 pages, 465 chars, 2 text pages` | Adaptive filtering is a method-core topic and supports later noise-cancellation explanations. | Run OCR, export searchable PDF, rerun intake, then consider merge into `theory_core`. |
| `P1` | `第8章第2讲自适应噪声抵消器.pdf` | `theory_core` | `6 pages, 236 chars, 0 text pages` | This is the strongest OCR candidate because it appears almost fully image-based and directly follows the adaptive-filtering basics. | Run OCR with page-level text verification, rerun intake, then merge only if promoted to `ready_pdf`. |
| `P2` | `第3章第1讲随机信号.pdf` | `theory_core` | `6 pages, 603 chars, 2 text pages` | Random-signal material supports later spectral and stochastic-signal questions, but can follow the filtering mainline. | Run OCR, rerun intake, then merge if extraction quality is acceptable. |
| `P2` | `第4章第2讲线性相关.pdf` | `theory_core` | `6 pages, 371 chars, 2 text pages` | Correlation theory is useful for signal-analysis explanations, but less urgent than the adaptive-filtering sequence. | Run OCR, rerun intake, then merge after verifying terminology quality. |
| `P3` | `第8章第4讲自适应滤波增强胃电测量.pdf` | `theory_core` | `6 pages, 691 chars, 2 text pages` | Application-focused slide deck with narrower reuse than the core adaptive-filtering lectures. | Run OCR after `P1/P2`, rerun intake, then decide whether to keep in `theory_core` or defer. |

## Batch Order

1. Finish all `P1` files first.
2. Re-run the intake scanner on the OCR outputs and confirm they become `ready_pdf`.
3. Add qualified `P1` files into `retrieval-priority-v1.json`.
4. Continue with `P2`, then `P3`.

## Suggested Verification

- Check whether OCR preserved formulas, Greek letters, and filter names instead of only body text.
- Verify at least the title slide and one content slide per file produce meaningful extracted text.
- Keep the original exported PDF and save OCR results as a separate searchable copy if quality is uncertain.
