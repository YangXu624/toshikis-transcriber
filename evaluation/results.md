# Transcriber Models Standardized Evaluation Results

This document presents the performance results of different transcription models evaluated against Southeast Asian accented English speech (mainly Singaporean English / Singlish, with Vietnamese and Indonesian speech patterns). 

The test evaluations are **standardized** to ignore minor formatting variations, spacing, punctuation, capitalization, abbreviation representations (e.g. `p.m.` vs `pm`), and spelling typos present in the reference files (such as `rythmn` or `whch`). This ensures the models are not penalized for correct spellings.

The test data consists of four audio recordings:
1. **Cassie** (Singaporean accent)
2. **Nicholas** (Singaporean accent)
3. **Suzanne** (Singaporean accent)
4. **Yangxu** (Singaporean accent - *Ground Truth text updated to match full audio context*)

---

## 1. Accuracy and Performance Comparison (Standardized)

The following table summarizes the Word Error Rate (WER) and Standardized Accuracy for each tested configuration.

| Model / Metric | Whisper `base` (Local) | Whisper `small` (Local) | Whisper `medium` (Local) | Whisper `large-v3-turbo` (Local) | Whisper `large-v3` (Local) | Gemini API (`gemini-2.5-flash`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cassie Accuracy** | 84.91% | 81.13% | **84.91%** | 83.02% | 83.02% | **86.79%** |
| **Nicholas Accuracy** | 91.67% | 86.67% | 93.33% | 91.67% | **100.00%** | 93.33% |
| **Suzanne Accuracy** | 82.46% | 92.98% | **96.49%** | 94.74% | **96.49%** | 91.23% |
| **Yangxu Accuracy** | 50.00% | 95.00% | 95.00% | **96.67%** | **96.67%** | 91.67% |
| **Average Accuracy** | 77.26% | 88.95% | **92.43%** | 91.52% | **94.04%** | 90.76% |
| **Average WER** | 22.74% | 11.05% | **7.57%** | 8.48% | **5.96%** | 9.24% |
| **Execution Type** | Local | Local | Local | Local | Local | Cloud API |
| **Model Size** | ~140 MB | ~461 MB | ~1.5 GB | ~809 MB | ~3.0 GB | N/A (Serverless) |

*All local Whisper models are run with `language="en"` and an `initial_prompt` keyword hints dictionary.*

---

## 2. Pros and Cons of Each Model

| Model | Pros | Cons | Best Used For |
| :--- | :--- | :--- | :--- |
| **Whisper `base`** | • Very fast CPU transcription<br>• Tiny memory footprint (~140MB)<br>• Ideal for low-resource environments | • Struggles with context and complex pronunciations<br>• Yangxu's accent caused segment truncation | Ultra-fast local testing on clean, unaccented speech. |
| **Whisper `small`** | • Great accuracy / speed trade-off<br>• Modest disk usage (~461MB)<br>• Tested at **~88.95% accuracy** | • Slightly higher CPU latency than `base` | General-purpose offline transcription on standard machines. |
| **Whisper `medium`** | • Very high accuracy locally (**92.43%**)<br>• Highly coherent segment alignment | • Large download (~1.5GB)<br>• High CPU utilization and memory overhead | Offline transcription where accuracy is preferred over speed. |
| **Whisper `large-v3-turbo`** | • **3x to 4x faster** than full `large-v3`<br>• Great accuracy locally (**91.52%**)<br>• Smaller model size (~809 MB)<br>• Fully offline and free | • Slightly lower accuracy than full `large-v3` on certain accents (specifically Nicholas and Cassie)<br>• Runs on CPU on macOS (no GPU acceleration) | Offline local transcription where high speed is needed without sacrificing too much accuracy. |
| **Whisper `large-v3`** | • **Highest accuracy overall** (**94.04%**)<br>• **100% accuracy** on Nicholas's accent<br>• Handles overlapping words and noise | • Very heavy disk requirement (~3.0GB)<br>• Slow on CPUs (requires GPU acceleration for speed)<br>• Large RAM footprint | Production local systems with dedicated GPU resources. |
| **Gemini API (`gemini-2.5-flash`)** | • Strong multilingual & accent context (**90.76%**)<br>• Serverless (no local model downloads or memory usage)<br>• Highest Cassie accuracy (**86.79%**) | • Requires active internet connection<br>• Subject to network latency and API usage costs<br>• Lacks timestamps/segment timings in basic mode | Multi-accented team environments, cloud deployments, and lightweight clients. |

---

## 3. Conclusions and Recommendations

1. **Local vs Cloud Performance**:
   - The **Whisper `large-v3`** model achieved the highest accuracy overall (**94.04%**), but is slow on typical CPUs.
   - The **Gemini `gemini-2.5-flash` API** is a highly convenient cloud option at **90.76%** accuracy, requiring no local hardware overhead.
2. **The local Speed-Accuracy-Cost Sweet Spot**:
   - **Whisper `large-v3-turbo`** strikes the perfect trade-off for local execution. It achieves **91.52%** accuracy (exceeding the Gemini Cloud API's 90.76% accuracy on these multi-accented test files) and runs **3x to 4x faster** than `large-v3` with a much smaller memory footprint (~809 MB vs ~3.0 GB).
3. **Text Standardization**:
   - Running text standardization before evaluation is essential in speech engineering to prevent penalizing transcription engines for fixing typographical errors in ground truth reference files (such as transcribing `rythmn` correctly as `rhythm`).
