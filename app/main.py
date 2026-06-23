import logging
import sys
from pathlib import Path

from config.settings import load_settings
from core.factory import AdapterFactory
from core.orchestrator import SessionOrchestrator

def setup_logging(log_level: str) -> None:
    """Set up structured application-wide logging."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main() -> None:
    # 1. Load application settings and secrets
    try:
        settings = load_settings()
    except Exception as e:
        print(f"Error loading configuration: {e}", file=sys.stderr)
        sys.exit(1)

    # 2. Setup logging configuration
    setup_logging(settings.app.log_level)
    logger = logging.getLogger("app.main")
    logger.info("Initializing AI Session Capture & Summarisation Tool...")
    logger.info(f"Environment: {settings.app.environment}")

    # 3. Instantiate concrete adapters via Factory (No direct concrete imports!)
    try:
        transcriber = AdapterFactory.create_transcriber(
            provider=settings.transcriber.provider,
            settings=settings.transcriber.settings
        )
        summarizer = AdapterFactory.create_summarizer(
            provider=settings.summarizer.provider,
            settings=settings.summarizer.settings
        )
        storage = AdapterFactory.create_storage(
            provider=settings.storage.provider,
            settings=settings.storage.settings
        )
    except Exception as e:
        logger.exception("Failed to initialize system adapters:")
        sys.exit(1)

    # 4. Construct the pipeline Orchestrator injecting the concrete instances
    orchestrator = SessionOrchestrator(
        transcriber=transcriber,
        summarizer=summarizer,
        storage=storage
    )

    # 5. Execute demonstration pipeline
    # Create a temporary dummy audio path to demonstrate execution without real IO errors
    dummy_audio_file = Path("scratch/sample_meeting.wav")
    dummy_audio_file.parent.mkdir(parents=True, exist_ok=True)
    if not dummy_audio_file.exists():
        with open(dummy_audio_file, "w") as f:
            f.write("DUMMY AUDIO DATA")
        logger.info(f"Created dummy meeting recording for demonstration at {dummy_audio_file}")

    try:
        session = orchestrator.run_pipeline(
            audio_path=dummy_audio_file,
            title="Architecture Kickoff Meeting"
        )
        
        # Output summary details to console
        logger.info("\n" + "=" * 50)
        logger.info(f"Pipeline executed successfully!")
        logger.info(f"Session ID:  {session.session_id}")
        logger.info(f"Title:       {session.metadata.title}")
        logger.info(f"Transcript Preview:\n  {session.transcript.raw_text if session.transcript else 'N/A'}")
        logger.info("Summary Topics: " + ", ".join(session.summary.topics if session.summary else []))
        logger.info("Summary Content preview:\n  " + (session.summary.content if session.summary else "N/A"))
        logger.info("=" * 50)

    except Exception as e:
        logger.exception("An error occurred during pipeline execution:")
        sys.exit(1)

if __name__ == "__main__":
    main()
