# 首版知识库清单 V1

适用范围：本科生生物医学信号处理教学智能体。

本清单基于当前工作区中已有的 `materials/` 与 `materials/open-resources/` 资料生成，目标是让智能体优先检索“可直接用于教学解释、实验指导、方法入门”的资料，而不是一开始就落到泛化背景书籍。

## 一、分层原则

- A层：高优先级核心资料
  用于概念解释、实验流程、方法入门、工具上手。优先返回。
- B层：中优先级专题资料
  用于补充某一信号类型或方法的细节。A层不足时再补。
- C层：低优先级背景资料
  用于生理学、运动控制、神经科学背景补充，不作为首选答案来源。
- D层：排除或严格降权资料
  来源不明、版权风险高、或不适合作为教学智能体主依据的资料。

## 二、A层：高优先级核心资料

### A1. 通用信号处理核心

1. [MIT-OCW-ch1_adc.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-ch1_adc.pdf)
   主题：数据采集、采样、量化、混叠
   用途：采样定理、A/D 转换、离散化基础讲解

2. [MIT-OCW-ch2_dfilt.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-ch2_dfilt.pdf)
   主题：数字滤波
   用途：FIR/IIR、滤波器设计、截止频率解释

3. [MIT-OCW-ch5_samp.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-ch5_samp.pdf)
   主题：采样理论
   用途：本科生采样、频谱映射、频率归一化教学

4. [MIT-OCW-ch7_stft.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-ch7_stft.pdf)
   主题：短时傅里叶变换
   用途：时频分析、窗长选择、分辨率权衡

5. [MIT-OCW-tutorial.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-tutorial.pdf)
   主题：课程型 tutorial
   用途：面向课堂和实验的综合引导

### A2. ECG 教学核心

6. [MIT-OCW-ecg_ch1.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-ecg_ch1.pdf)
   主题：ECG 入门
   用途：ECG 基础讲解、波形解释、课程导入

7. [MIT-OCW-l3_ecg_reisner.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-l3_ecg_reisner.pdf)
   主题：ECG 分析专题
   用途：QRS、RR、心率估计、ECG 处理案例

8. [MIT-OCW-lab1_ecg.pdf](D:/NJMU/生物医学信号处理/materials/open-resources/mit-ocw/MIT-OCW-lab1_ecg.pdf)
   主题：ECG 实验
   用途：实验流程、实验问答、报告指导

9. [PhysioNet-Tutorial.html](D:/NJMU/生物医学信号处理/materials/open-resources/tutorial-pages/PhysioNet-Tutorial.html)
   主题：PhysioNet 官方教程
   用途：生理信号数据库、信号分析实践入口

### A3. EEG / fNIRS / 工具链教学核心

10. [EEGLAB-Tutorials.html](D:/NJMU/生物医学信号处理/materials/open-resources/tutorial-pages/EEGLAB-Tutorials.html)
    主题：EEGLAB 官方教程总入口
    用途：EEG 预处理、事件相关分析、工具操作指导

11. [EEGLAB-Tutorial-Data.html](D:/NJMU/生物医学信号处理/materials/open-resources/tutorial-pages/EEGLAB-Tutorial-Data.html)
    主题：EEGLAB 数据教程
    用途：EEG 数据导入和基础流程

12. [MNE-Preprocessing-Index.html](D:/NJMU/生物医学信号处理/materials/open-resources/tutorial-pages/MNE-Preprocessing-Index.html)
    主题：MNE 预处理教程
    用途：Python 版 EEG/MEG 预处理流程参考

13. [MNE-fNIRS-Processing-Tutorial.html](D:/NJMU/生物医学信号处理/materials/open-resources/tutorial-pages/MNE-fNIRS-Processing-Tutorial.html)
    主题：MNE fNIRS 教程
    用途：fNIRS 处理流程、Python 上手、实验解释

14. [EPOS-EEG-Processing-Open-Source-Scripts.html](D:/NJMU/生物医学信号处理/materials/open-resources/pmc/EPOS-EEG-Processing-Open-Source-Scripts.html)
    主题：EEG 开源处理脚本
    用途：EEG 流程标准化、脚本结构、可复现分析

15. [fNIRS-POTATo-Tutorial.html](D:/NJMU/生物医学信号处理/materials/open-resources/pmc/fNIRS-POTATo-Tutorial.html)
    主题：fNIRS 教程
    用途：fNIRS 预处理、功能信号提取、结果可视化

## 三、B层：中优先级专题资料

### B1. EMG / HDsEMG

16. [Merletti 和 Farina - 2016 - Surface electromyography physiology, engineering .pdf](D:/NJMU/生物医学信号处理/materials/Merletti 和 Farina - 2016 - Surface electromyography physiology, engineering .pdf)
    主题：表面肌电基础与工程方法
    用途：EMG 基础理论、采集、预处理、解释

17. [表面肌电图诊断技术临床应用_13944011.pdf](D:/NJMU/生物医学信号处理/materials/表面肌电图诊断技术临床应用_13944011.pdf)
    主题：中文表面肌电资料
    用途：中文术语、临床关联背景、课堂辅助说明

18. [HDsEMG-65-Hand-Gestures-Database.html](D:/NJMU/生物医学信号处理/materials/open-resources/pmc/HDsEMG-65-Hand-Gestures-Database.html)
    主题：HDsEMG 数据库论文
    用途：HDsEMG 数据结构、通道布局、任务设计参考

### B2. PPG

19. [PPG-Best-Practices.html](D:/NJMU/生物医学信号处理/materials/open-resources/pmc/PPG-Best-Practices.html)
    主题：PPG 信号质量与实践建议
    用途：PPG 质量评估、预处理、教学案例

20. [Wearable-PPG-Review.html](D:/NJMU/生物医学信号处理/materials/open-resources/pmc/Wearable-PPG-Review.html)
    主题：可穿戴 PPG 综述
    用途：PPG 应用背景、局限性、算法任务介绍

### B3. 非线性与扩展主题

21. [Akay 和 IEEE Engineering in Medicine and Biology Society - 2000 - Nonlinear biomedical signal processing.pdf](D:/NJMU/生物医学信号处理/materials/Akay 和 IEEE Engineering in Medicine and Biology Society - 2000 - Nonlinear biomedical signal processing.pdf)
    主题：非线性生物医学信号处理
    用途：进阶专题、扩展阅读、课程拓展

## 四、C层：低优先级背景资料

22. [Knudson - 2007 - Fundamentals of biomechanics.pdf](D:/NJMU/生物医学信号处理/materials/Knudson - 2007 - Fundamentals of biomechanics.pdf)
    用途：生物力学背景补充

23. [Latash - 2012 - Fundamentals of motor control.pdf](D:/NJMU/生物医学信号处理/materials/Latash - 2012 - Fundamentals of motor control.pdf)
    用途：运动控制背景补充

24. [Latash 和 Lestienne - 2006 - Motor control and learning.pdf](D:/NJMU/生物医学信号处理/materials/Latash 和 Lestienne - 2006 - Motor control and learning.pdf)
    用途：运动学习背景补充

25. [Purves - 2004 - Neuroscience.pdf](D:/NJMU/生物医学信号处理/materials/Purves - 2004 - Neuroscience.pdf)
    用途：神经科学背景补充

## 五、D层：排除或严格降权

26. [Medical Books Free Neuroscience 6th Edition PDF.pdf](D:/NJMU/生物医学信号处理/materials/Medical Books Free Neuroscience 6th Edition PDF.pdf)
    处理建议：不作为主检索源。
    原因：文件名显示来源不清晰，可能存在版权或版本可靠性风险。

## 六、检索建议

- 概念题：先查 A1，再查 A2/A3，再补 B/C。
- ECG 实验题：先查 A2，再查 A1 和 PhysioNet。
- EEG 处理题：先查 A3 中 EEGLAB / MNE / EPOS。
- fNIRS 处理题：先查 MNE-fNIRS 与 POTATo。
- EMG / HDsEMG：先查 Merletti，再查 HDsEMG 数据论文，再补背景资料。
- PPG：先查 PPG 专题资料，再补 MIT 采样/滤波讲义。
- 作业题：允许检索方法与概念，但回答层必须保持“只给提示”。

## 七、当前缺口

当前知识库仍缺少：

- 本课程自己的章节目录
- MATLAB 示例代码
- Python 示例代码
- 实验指导书
- 作业与评分规则
- 本地数据样例

在这些内容补齐前，智能体适合做“通用版教学助教”，不适合假装成“本课程专属答案系统”。
