import sys
from pathlib import Path

# Add project root directory to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from modules.transcribers.faster_whisper import FasterWhisperTranscriber

def main():
    script_dir = Path(__file__).resolve().parent
    audio_path = script_dir / "agoda.mp3"
    output_path = script_dir / "agoda.txt"
    
    print(f"Loading Whisper large-v3-turbo model... (This will download ~3GB of files if run for the first time)")
    # We use CPU by default for macOS.
    transcriber = FasterWhisperTranscriber(model_size="large-v3-turbo", device="auto", compute_type="int8")
    
    print(f"Transcribing {audio_path}...")
    initial_prompt = "Agoda, Eco Voyage, Binjai Consulting Group, solo travelers, Ago Local, travel bookers."
    transcript = transcriber.transcribe(
        audio_path,
        language="en",
        initial_prompt=initial_prompt
    )
    
    print(f"Saving transcription to {output_path}...")
    output_path.write_text(transcript.raw_text, encoding="utf-8")
    print("Done!")

if __name__ == "__main__":
    main()
