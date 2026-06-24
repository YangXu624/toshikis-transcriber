import sys
import os
from pathlib import Path

# Add project root directory to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from modules.structurizers.gemini import GeminiStructurizer
from domain.models import Transcript

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

    input_dir = Path(__file__).resolve().parent / "input"
    output_dir = Path(__file__).resolve().parent / "output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Initializing GeminiStructurizer...")
    structurizer = GeminiStructurizer()
    
    # Look for transcript txt files
    txt_files = list(input_dir.glob("*.txt"))
    # Filter out files that are already Q&A or presentation files
    txt_files = [f for f in txt_files if not f.stem.endswith("_presentation") and not f.stem.endswith("_q_and_a")]
    
    # Filter by command line arguments if specified
    if len(sys.argv) > 1:
        specified = sys.argv[1:]
        txt_files = [
            f for f in txt_files 
            if any(s.lower() in f.name.lower() or s.lower() in f.stem.lower() for s in specified)
        ]
    
    if not txt_files:
        print(f"No transcript files found matching criteria in {input_dir}")
        return
        
    print(f"Found {len(txt_files)} transcripts to structure: {[f.name for f in txt_files]}")
    for txt_path in txt_files:
        pres_out = output_dir / f"{txt_path.stem}_presentation.txt"
        qa_out = output_dir / f"{txt_path.stem}_q_and_a.txt"
        
        # Only skip if not explicitly requested via command line args
        if len(sys.argv) <= 1 and pres_out.exists() and qa_out.exists():
            print(f"Skipping {txt_path.name} (already structured).")
            continue

        print(f"\nStructuring {txt_path.name}...")
        try:
            raw_text = txt_path.read_text(encoding="utf-8")
            transcript = Transcript(raw_text=raw_text)
            
            pres_text, qa_text = structurizer.structurize(transcript)
            
            pres_out.write_text(pres_text, encoding="utf-8")
            qa_out.write_text(qa_text, encoding="utf-8")
            print(f"Saved structure to:\n  - {pres_out}\n  - {qa_out}")
            
            # Sleep to prevent hitting Gemini API Free Tier rate limits (5 requests / min)
            import time
            print("Sleeping 20 seconds to prevent rate limits...")
            time.sleep(20)
        except Exception as e:
            print(f"Error structuring {txt_path.name}: {e}")

if __name__ == "__main__":
    main()
