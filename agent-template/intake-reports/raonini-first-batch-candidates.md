# Raonini First-Batch Knowledge-Base Candidates

## Summary

- Source directory: `materials/raonini/pdf-export`
- Total exported PDFs reviewed: `40`
- Directly usable `ready_pdf`: `34`
- `needs_ocr` before intake: `6`
- Recommended first batch size: `12`

## Selection Criteria

- Prefer files that are already `ready_pdf` and do not require OCR.
- Prefer chapter introductions and method-core slides that define the vocabulary of the course.
- Prefer materials that can replace generic public resources in `theory_core` or enrich `ecg_core`.
- Delay specialized slides with lower immediate reuse until the first batch is stable.

## First Batch

| File | Normalized Name | Suggested Group | Why Include First |
|---|---|---|---|
| `第1章第1讲本课程背景与信号的概念.pdf` | `course_1_1.pdf` | `theory_core` | Foundational course introduction and signal concepts; useful for many undergraduate entry questions. |
| `第1章第2讲典型生物医学信号.pdf` | `course_1_2.pdf` | `theory_core` | Introduces representative biomedical signal types and supports early-stage teaching dialogue. |
| `第2章第1讲傅立叶变换及其意义.pdf` | `course_2_1.pdf` | `theory_core` | Core entry point for Fourier analysis and frequency-domain reasoning. |
| `第2章第2讲傅里叶变换及其意义傅里叶变换的性质.pdf` | `course_2_2.pdf` | `theory_core` | Adds Fourier-transform properties that are frequently needed for explanations and derivations. |
| `第2章第3讲傅里叶变换的性质频域分析和谱图表示.pdf` | `course_2_3.pdf` | `theory_core` | Bridges transform properties to spectrum representation and frequency-domain interpretation. |
| `第2章第4讲频域分析和谱图表示、频率分辨率.pdf` | `course_2_4.pdf` | `theory_core` | Frequency resolution is a common student pain point and should be available early. |
| `第2章第5讲频率分辨率、数字滤波器的设计和实现.pdf` | `course_2_5.pdf` | `theory_core` | Connects frequency resolution to digital filter design, which is valuable for labs and homework hints. |
| `第2章第6讲数字滤波器的设计和实现.pdf` | `course_2_6.pdf` | `theory_core` | Digital filter design is a mainline topic and should outrank later specialized material. |
| `第4章第7讲相关函数和功率谱估计.pdf` | `course_4_7.pdf` | `theory_core` | Power spectral estimation is widely reused across later signal-analysis questions. |
| `第4章第8讲功率谱估计、相关技术的应用.pdf` | `course_4_8.pdf` | `theory_core` | Adds application-oriented context instead of only definitions and formulas. |
| `第5章第6讲维纳滤波器消除ECG中的噪声.pdf` | `course_5_6_ecg.pdf` | `ecg_core` | Most explicit ECG-specific lecture in this batch; should enrich ecg_core directly. |
| `第6章第2讲卡尔曼滤波方法及应用.pdf` | `course_6_2.pdf` | `theory_core` | Covers Kalman filtering methods and applications, which broadens modern filtering support. |

## Second Batch

These files are already `ready_pdf`, but can be added after the first batch is stable:

- `总复习第1讲.pdf` -> `theory_core` (`course_1.pdf`)
- `总复习第2讲.pdf` -> `theory_core` (`course_2.pdf`)
- `第3章第2讲广义的平稳随机过程.pdf` -> `theory_core` (`course_3_2.pdf`)
- `第3章第3讲随机信号的古典表示法.pdf` -> `theory_core` (`course_3_3.pdf`)
- `第3章第4讲典型的随机过程.pdf` -> `theory_core` (`course_3_4.pdf`)
- `第4章第1讲随机信号和线性相关.pdf` -> `theory_core` (`course_4_1.pdf`)
- `第4章第3讲循环相关.pdf` -> `theory_core` (`course_4_3.pdf`)
- `第4章第4讲相干函数.pdf` -> `theory_core` (`course_4_4.pdf`)
- `第4章第5讲复习线性相关、循环相关和相干函数.pdf` -> `theory_core` (`course_4_5.pdf`)
- `第4章第6讲线性卷积循环卷积相关函数功率谱估计.pdf` -> `theory_core` (`course_4_6.pdf`)
- `第5章第1讲维纳－霍夫方程.pdf` -> `theory_core` (`course_5_1.pdf`)
- `第5章第3讲预白化法求解维纳-霍夫方程.pdf` -> `theory_core` (`course_5_3.pdf`)
- `第5章第4讲维纳预测器.pdf` -> `theory_core` (`course_5_4.pdf`)
- `第5章第5讲维纳滤波器提取诱发电位.pdf` -> `theory_core` (`course_5_5.pdf`)
- `第6章第1讲卡尔曼滤波信号模型.pdf` -> `theory_core` (`course_6_1.pdf`)
- `第7章第1讲谱图分析和随机信号分析.pdf` -> `theory_core` (`course_7_1.pdf`)
- `第7章第2讲三种参数模型.pdf` -> `theory_core` (`course_7_2.pdf`)
- `第7章第3讲AR模型参数的估计.pdf` -> `theory_core` (`course_7_3_ar.pdf`)
- `第7章第4讲AR模型参数估计的几种算法.pdf` -> `theory_core` (`course_7_4_ar.pdf`)
- `第7章第5讲参数模型估计方法.pdf` -> `theory_core` (`course_7_5.pdf`)
- `第7章第6讲参数建模的应用.pdf` -> `theory_core` (`course_7_6.pdf`)
- `第8章第3讲自适应滤波增强心电监护.pdf` -> `theory_core` (`course_8_3.pdf`)

## OCR Required Before Intake

- `第3章第1讲随机信号.pdf` -> `theory_core` (`course_3_1.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.
- `第4章第2讲线性相关.pdf` -> `theory_core` (`course_4_2.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.
- `第5章第2讲有限脉冲响应法求解维纳-霍夫方程.pdf` -> `theory_core` (`course_5_2.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.
- `第8章第1讲自适应滤波基本原理.pdf` -> `theory_core` (`course_8_1.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.
- `第8章第2讲自适应噪声抵消器.pdf` -> `theory_core` (`course_8_2.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.
- `第8章第4讲自适应滤波增强胃电测量.pdf` -> `theory_core` (`course_8_4.pdf`): Likely scanned or image-dominant PDF. Run OCR before intake.

## Suggested Next Steps

1. Add the first 12 files to `retrieval-priority-v1.json` first.
2. Hold the 6 `needs_ocr` files out of the default corpus for now.
3. After the first batch is stable, continue with the remaining `ready_pdf` files by chapter order.
4. Improve Chinese filename normalization later so the system can generate better names than `course_2_3.pdf`.

