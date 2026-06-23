import sys
import logging
from pathlib import Path

# Add the project root directory to python path
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from modules.transcribers.faster_whisper import FasterWhisperTranscriber

def main() -> None:
    # Setup simple console logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    if len(sys.argv) < 2:
        print("Error: Missing audio file path.")
        print("\nUsage:")
        print("  python scratch/test_transcribe.py <path_to_audio_file> [model_size] [device]")
        print("\nExample:")
        print("  python scratch/test_transcribe.py my_meeting.mp3 tiny cpu")
        sys.exit(1)

    audio_path = Path(sys.argv[1])
    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"
    device = sys.argv[3] if len(sys.argv) > 3 else "cpu"

    if not audio_path.exists():
        print(f"Error: Audio file not found at '{audio_path}'")
        sys.exit(1)

    print("-" * 60)
    print(f"Initializing FasterWhisperTranscriber...")
    print(f"  Model Size: {model_size}")
    print(f"  Device:     {device}")
    print("-" * 60)

    try:
        transcriber = FasterWhisperTranscriber(model_size=model_size, device=device)
        transcript = transcriber.transcribe(audio_path)

        print("\n" + "=" * 60)
        print("TRANSCRIPTION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Detected Language: {transcript.language}")
        print(f"Total Segments:    {len(transcript.segments)}")
        print("-" * 60)
        print(f"Raw Combined Text:\n{transcript.raw_text}")
        print("-" * 60)
        print("Segment Breakdown:")
        for i, segment in enumerate(transcript.segments, start=1):
            print(f"  [{segment.start_time:05.2f}s -> {segment.end_time:05.2f}s]: {segment.text}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FATAL] Transcription failed with error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
