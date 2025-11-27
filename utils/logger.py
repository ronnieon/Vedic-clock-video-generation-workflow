"""
Logging Utility
===============
Centralized logging for tracking all operations in the pipeline.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Any


# Create logs directory
LOGS_DIR = Path('logs')
LOGS_DIR.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger('vedic_clock_content_generation_pipeline')
logger.setLevel(logging.DEBUG)

# Remove existing handlers
logger.handlers.clear()

# File handler - detailed logs
log_file = LOGS_DIR / f'pipeline_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
file_handler = logging.FileHandler(log_file, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler - important logs only
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    '%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


def log_user_action(action: str, pdf_stem: str, details: Optional[dict] = None):
    """Log user interface actions."""
    msg = f"USER ACTION: {action} | PDF: {pdf_stem}"
    if details:
        msg += f" | Details: {details}"
    logger.info(msg)


def log_stage_start(stage: str, pdf_stem: str, **kwargs):
    """Log the start of a pipeline stage."""
    msg = f"STAGE START: {stage} | PDF: {pdf_stem}"
    if kwargs:
        msg += f" | Params: {kwargs}"
    logger.info(msg)


def log_stage_complete(stage: str, pdf_stem: str, duration: Optional[float] = None):
    """Log the completion of a pipeline stage."""
    msg = f"STAGE COMPLETE: {stage} | PDF: {pdf_stem}"
    if duration:
        msg += f" | Duration: {duration:.2f}s"
    logger.info(msg)


def log_stage_error(stage: str, pdf_stem: str, error: Exception):
    """Log errors during pipeline stages."""
    logger.error(f"STAGE ERROR: {stage} | PDF: {pdf_stem} | Error: {str(error)}", exc_info=True)


def log_file_operation(operation: str, file_path: Path, success: bool = True):
    """Log file operations (read, write, delete)."""
    status = "SUCCESS" if success else "FAILED"
    logger.debug(f"FILE OP: {operation} | {status} | Path: {file_path}")


def log_api_call(api: str, model: str, input_length: int, success: bool = True):
    """Log API calls to external services."""
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"API CALL: {api} | Model: {model} | Input: {input_length} chars | {status}")


def log_overwrite_warning(files: list, confirmed: bool):
    """Log overwrite warnings and user confirmation."""
    logger.warning(f"OVERWRITE WARNING: {len(files)} file(s) | Confirmed: {confirmed}")
    for file in files[:10]:  # Log first 10 files
        logger.debug(f"  - {file}")


def log_session_info(key: str, value: Any, action: str = "SET"):
    """Log session state changes."""
    logger.debug(f"SESSION {action}: {key} = {value}")


def get_current_log_file() -> Path:
    """Get the path to the current log file."""
    return log_file


# Log startup
logger.info("="*80)
logger.info("VEDIC CLOCK CONTENT GENERATION PIPELINE LOGGING INITIALIZED")
logger.info(f"Log file: {log_file}")
logger.info("="*80)
