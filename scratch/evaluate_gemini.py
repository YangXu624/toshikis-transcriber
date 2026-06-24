import sys
import os
import re
from pathlib import Path

# Add project root to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from modules.transcribers.gemini_audio import GeminiAudioTranscriber

def normalize_text(text: str) -> list[str]:
    """Standardize text to remove formatting variations, typos in references, and punctuation."""
    text = text.lower()
    
    # 1. Correct spelling typos in reference files
    text = text.replace("rythmn", "rhythm")
    text = text.replace("whch", "which")
    text = text.replace("gonna", "going to")  # Standardize contraction
    
    # 2. Convert hyphens/dashes to spaces (so 'eco-friendly' matches 'eco friendly')
    text = text.replace("-", " ")
    
    # 3. Strip all punctuation except spaces and single quotes
    text = re.sub(r"[^\w\s\']", "", text)
    
    # 4. Standardize p.m. / a.m. formats
    text = re.sub(r"\b(p\s*m|p\.*m\.*)\b", "pm", text)
    text = re.sub(r"\b(a\s*m|a\.*m\.*)\b", "am", text)
    
    # 5. Clean up multiple whitespaces
    text = re.sub(r"\s+", " ", text).strip()
    
    return text.split()

def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate the Word Error Rate (WER) between reference and hypothesis text."""
    ref_words = normalize_text(reference)
    hyp_words = normalize_text(hypothesis)
    
    # Compute Levenshtein distance
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]
    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j
        
    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i-1] == hyp_words[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                substitution = d[i-1][j-1] + 1
                insertion = d[i][j-1] + 1
                deletion = d[i-1][j] + 1
                d[i][j] = min(substitution, insertion, deletion)
                
    if not ref_words:
        return 1.0 if hyp_words else 0.0
        
    return d[len(ref_words)][len(hyp_words)] / len(ref_words)

def main():
    # Load environment variables manually from .env
    env_path = project_root / ".env"
    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()

    scratch_dir = Path(__file__).parent
    test_cases = ["cassie", "nicholas", "suzanne", "yangxu"]

    model_name = "gemini-2.5-flash"
    print("=" * 70)
    print(f"Loading Gemini Audio Transcriber using '{model_name}'...")
    print("=" * 70)
    
    try:
        # Initialize transcriber
        transcriber = GeminiAudioTranscriber(model_name=model_name)
    except Exception as e:
        print(f"Failed to initialize GeminiAudioTranscriber: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print(f"RUNNING STANDARDIZED EVALUATION ON GEMINI API")
    print("=" * 70)

    overall_wer_sum = 0
    valid_cases = 0

    for name in test_cases:
        audio_file = scratch_dir / f"{name}.mp3"
        txt_file = scratch_dir / f"{name}.txt"

        if not audio_file.exists() or not txt_file.exists():
            continue

        print(f"\nProcessing: {name.upper()}")
        print("-" * 50)

        # Load reference text
        with open(txt_file, "r", encoding="utf-8") as f:
            reference_text = f.read().strip()

        # Run transcription
        try:
            transcript = transcriber.transcribe(audio_file)
            hyp_text = transcript.raw_text.strip()
        except Exception as e:
            print(f"Error transcribing {audio_file.name}: {e}")
            continue

        # Evaluate accuracy
        wer = calculate_wer(reference_text, hyp_text)
        accuracy = max(0.0, 1.0 - wer)
        overall_wer_sum += wer
        valid_cases += 1

        print(f"Ref Text:  {reference_text}")
        print(f"Hyp Text:  {hyp_text}")
        print(f"Word Error Rate (WER): {wer:.2%}")
        print(f"Standardized Accuracy: {accuracy:.2%}")
        print("-" * 50)

    if valid_cases > 0:
        avg_wer = overall_wer_sum / valid_cases
        avg_accuracy = max(0.0, 1.0 - avg_wer)
        print("\n" + "=" * 70)
        print(f"STANDARDIZED SUMMARY FOR GEMINI API")
        print("=" * 70)
        print(f"Average Word Error Rate (WER): {avg_wer:.2%}")
        print(f"Average System Accuracy:       {avg_accuracy:.2%}")
        print("=" * 70)

if __name__ == "__main__":
    main()
