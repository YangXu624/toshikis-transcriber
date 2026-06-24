import sys
import os
import json
from pathlib import Path

# Add project root directory to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

from modules.summarizers.gemini import GeminiSummarizer

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
    
    print("Initializing GeminiSummarizer...")
    summarizer = GeminiSummarizer()
    
    # Look for structured Q&A files from structurizer output
    qa_files = list(input_dir.glob("*_q_and_a.txt"))
    
    # Filter by command line arguments if specified
    if len(sys.argv) > 1:
        specified = sys.argv[1:]
        qa_files = [
            f for f in qa_files 
            if any(s.lower() in f.name.lower() or s.lower() in f.stem.lower() for s in specified)
        ]
        
    if not qa_files:
        print(f"No Q&A transcript files found matching criteria in {input_dir}")
        return
        
    print(f"Found {len(qa_files)} Q&A transcripts to summarize: {[f.name for f in qa_files]}")
    for qa_path in qa_files:
        # Extract clean base filename (remove '_q_and_a')
        base_name = qa_path.stem
        if base_name.endswith("_q_and_a"):
            base_name = base_name[:-8]
            
        txt_out = output_dir / f"{base_name}_summary.txt"
        json_out = output_dir / f"{base_name}_summary.json"
        
        # Only skip if not explicitly requested via command line args
        if len(sys.argv) <= 1 and txt_out.exists() and json_out.exists():
            print(f"Skipping {qa_path.name} (already summarized).")
            continue
            
        print(f"\nSummarizing {qa_path.name}...")
        try:
            qa_text = qa_path.read_text(encoding="utf-8")
            summary = summarizer.summarize(qa_text)
            
            # Write plain text summary
            summary_lines = [
                f"SUMMARY:\n{summary.content}\n",
                "KEY POINTS:",
                "\n".join(f"- {pt}" for pt in summary.key_points),
                "\nACTION ITEMS:",
                "\n".join(f"- {item}" for item in summary.action_items),
                "\nTOPICS:",
                ", ".join(summary.topics)
            ]
            txt_out.write_text("\n".join(summary_lines), encoding="utf-8")
            
            # Write structured JSON
            json_data = {
                "content": summary.content,
                "key_points": summary.key_points,
                "action_items": summary.action_items,
                "topics": summary.topics
            }
            json_out.write_text(json.dumps(json_data, indent=4, ensure_ascii=False), encoding="utf-8")
            
            print(f"Saved summary to:\n  - {txt_out}\n  - {json_out}")
        except Exception as e:
            print(f"Error summarizing {qa_path.name}: {e}")

if __name__ == "__main__":
    main()
