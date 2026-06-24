# Transcriber Models Evaluation Results

This document presents the performance results of different transcription models evaluated against Southeast Asian accented English speech (mainly Singaporean English / Singlish, with Vietnamese and Indonesian speech patterns). 

The test data consists of four audio recordings:
1. **Cassie** (Singaporean accent)
2. **Nicholas** (Singaporean accent)
3. **Suzanne** (Singaporean accent)
4. **Yangxu** (Singaporean accent)

---

## 1. Accuracy and Performance Comparison

The following table summarizes the Word Error Rate (WER) and Approximate Accuracy for each tested configuration.

| Model / Metric | Whisper `base` (Default) | Whisper `base` (Optimized)* | Whisper `small` (Local) | Whisper `medium` (Local) | Whisper `large-v3` (Local) | Gemini API (`gemini-2.5-flash`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cassie Accuracy** | 78.85% | 82.69% | 76.92% | 80.77% | 78.85% | **84.62%** |
| **Nicholas Accuracy** | 6.67% | 90.00% | 85.00% | 91.67% | **98.33%** | 90.00% |
| **Suzanne Accuracy** | 59.65% | 77.19% | 87.72% | **91.23%** | **91.23%** | 84.21% |
| **Yangxu Accuracy** | 58.62% | 44.83% | **93.10%** | 89.66% | 91.38% | 87.93% |
| **Average Accuracy** | **50.95%** | **73.68%** | **85.69%** | **88.33%** | **89.95%** | **86.69%** |
| **Average WER** | 49.05% | 26.32% | 14.31% | 11.67% | **10.05%** | **13.31%** |
| **Execution Type** | Local | Local | Local | Local | Local | Cloud API |
| **Model Size** | ~140 MB | ~140 MB | ~461 MB | ~1.5 GB | ~3.0 GB | N/A (Serverless) |

*\*Optimized denotes forcing `language="en"` and supplying a contextual prompt `initial_prompt` with spelling hints for brand names.*

---

## 2. Pros and Cons of Each Model

| Model | Pros | Cons | Best Used For |
| :--- | :--- | :--- | :--- |
| **Whisper `base`** | • Very fast CPU transcription<br>• Tiny memory footprint (~140MB)<br>• Ideal for low-resource environments | • High rate of language misdetection on accents<br>• Struggles with context and complex pronunciations | Ultra-fast local testing on clean, unaccented speech. |
| **Whisper `small`** | • Great accuracy / speed trade-off<br>• Modest disk usage (~461MB)<br>• Captures accented English much better | • Slightly higher CPU latency than `base` | General-purpose offline transcription on standard machines. |
| **Whisper `medium`** | • Very high accuracy locally (**88.33%**)<br>• Robust segmentation and spelling | • Large download (~1.5GB)<br>• High CPU utilization and memory overhead | Offline transcription where accuracy is preferred over speed. |
| **Whisper `large-v3`** | • **Highest accuracy overall** (**89.95%**)<br>• Near-perfect transcription of accents<br>• Handles overlapping words and noise | • Very heavy disk requirement (~3.0GB)<br>• Slow on CPUs (requires GPU acceleration for speed)<br>• Large RAM footprint | Production local systems with dedicated GPU resources. |
| **Gemini API (`gemini-2.5-flash`)** | • Strong multilingual & accent context (**86.69%**)<br>• Serverless (no local model downloads or memory usage)<br>• Native multimodal audio support | • Requires active internet connection<br>• Subject to network latency and API usage costs<br>• Lacks timestamps/segment timings in basic mode | Multi-accented team environments, cloud deployments, and lightweight clients. |

---

## 3. Conclusions and Recommendations

1. **For Accented Speech (Singaporean/Vietnamese/Indonesian English)**:
   - **Forcing the language parameter (`language="en"`) is mandatory**. Accents can easily trick automatic detectors into transcribing in Malay, Indonesian, or Chinese.
   - **Using context prompts (`initial_prompt`)** resolves phonetic errors for business-specific keywords like *Agoda*, *Binjai*, or *Eco Voyage*.

2. **Deployment Choice**:
   - **Cloud**: Choose **Gemini API** for instant setup, zero local memory load, and great context accuracy.
   - **Local CPU (Standard PC)**: Choose **Whisper `small`** to keep latency low while retaining high accuracy.
   - **Local GPU (Workstation)**: Choose **Whisper `large-v3`** for the absolute highest transcription fidelity.
