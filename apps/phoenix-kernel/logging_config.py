# AUTO-FIXED IMPORT PATH
import sys
from pathlib import Path
_workers_dir = Path(__file__).parent.resolve()
if str(_workers_dir) not in sys.path:
    sys.path.insert(0, str(_workers_dir))
# END AUTO-FIX
# logging_config.py
"""Structured logging with rotation for Phoenix Kernel"""

import logging
import logging.handlers
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Create logs directory
Path("logs").mkdir(exist_ok=True)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread
        }
        
        # Add custom fields if present
        if hasattr(record, 'worker'):
            log_entry['worker'] = record.worker
        if hasattr(record, 'drift_lock'):
            log_entry['drift_lock'] = record.drift_lock
        if hasattr(record, 'trade_id'):
            log_entry['trade_id'] = record.trade_id
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/phoenix.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 10
) -> None:
    """
    Configure structured logging with rotation.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
    """
    # Convert string level to logging constant
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler (JSON, rotating)
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)
    
    # Create specific loggers for components
    loggers = {
        'kernel': logging.getLogger('phoenix.kernel'),
        'workers': logging.getLogger('phoenix.workers'),
        'exchange': logging.getLogger('phoenix.exchange'),
        'sce': logging.getLogger('phoenix.sce'),
        'memory': logging.getLogger('phoenix.memory'),
        'api': logging.getLogger('phoenix.api')
    }
    
    for logger in loggers.values():
        logger.setLevel(level)
    
    # Log startup
    logging.info(f"Logging configured: level={log_level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the phoenix prefix"""
    if name.startswith('phoenix.'):
        return logging.getLogger(name)
    return logging.getLogger(f'phoenix.{name}')


__all__ = ['setup_logging', 'get_logger', 'JSONFormatter']