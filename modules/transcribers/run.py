import sys
from pathlib import Path

# Add project root directory to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from modules.transcribers.faster_whisper import FasterWhisperTranscriber

def main():
    input_dir = Path(__file__).resolve().parent / "input"
    output_dir = Path(__file__).resolve().parent / "output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Initializing FasterWhisperTranscriber (large-v3-turbo)...")
    transcriber = FasterWhisperTranscriber(model_size="large-v3-turbo", device="auto", compute_type="int8")
    
    audio_files = list(input_dir.glob("*.mp3")) + list(input_dir.glob("*.wav")) + list(input_dir.glob("*.m4a"))
    
    # Filter by command line arguments if specified
    if len(sys.argv) > 1:
        specified = sys.argv[1:]
        audio_files = [
            f for f in audio_files 
            if any(s.lower() in f.name.lower() or s.lower() in f.stem.lower() for s in specified)
        ]
        
    if not audio_files:
        print(f"No audio files found matching criteria in {input_dir}")
        return
        
    print(f"Found {len(audio_files)} audio files to transcribe: {[f.name for f in audio_files]}")
    for audio_path in audio_files:
        output_path = output_dir / f"{audio_path.stem}.txt"
        
        # Only skip if not explicitly requested via command line args
        if len(sys.argv) <= 1 and output_path.exists():
            print(f"Skipping {audio_path.name} (already transcribed).")
            continue
            
        print(f"\nTranscribing {audio_path.name}...")
        initial_prompt = "Agoda, Eco Voyage, Binjai Consulting Group, solo travelers, Ago Local, travel bookers."
        try:
            transcript = transcriber.transcribe(
                audio_path,
                language="en",
                initial_prompt=initial_prompt
            )
            output_path.write_text(transcript.raw_text, encoding="utf-8")
            print(f"Saved transcript to {output_path}")
        except Exception as e:
            print(f"Error transcribing {audio_path.name}: {e}")

if __name__ == "__main__":
    main()
