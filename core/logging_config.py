import os
import logging
from logging.config import dictConfig
from datetime import datetime, timezone


def setup_logging():
    """
    Initializes and configures the centralized logging system for the entire application.
    Creates the log directory if missing and defines handlers for console and file outputs.
    """
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # File naming prefix based on the current UTC date
    date_str = datetime.now(timezone.utc).strftime("%d_%m_%Y_")

    # Global logging configuration for the entire app
    # as long as the file uses logger and is called by main.py, it automatically uses this configuration
    dictConfig({
        'version': 1,
        # Prevents Flask's debug mode from shutting down loggers initialized on startup
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                # Format of log lines, Year-month-day hour:minutes:seconds - logging level - [file name and line] - log message  
                'format': '%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            }
        },
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': f'logs/{date_str}app.log',
                'formatter': 'default',
                'level': 'DEBUG',
            },
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'default',
                'level': 'INFO',
            }
        },
        'loggers': {
            # Application internal modules - verbose tracking (DEBUG)
            'core': {
                'level' : 'DEBUG',
                'handlers' : ['console', 'file'],
                'propagate': False,
            }, 
            'news_summary': {
                'level' : 'DEBUG',
                'handlers' : ['console', 'file'],
                'propagate': False,
            },
            # Chatty external libraries - filtered to capture only warnings and errors
            'httpcore': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            'google': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False,
            },
            # Flask (Werkzeug) WSGI server - captures standard HTTP routing logs
            'werkzeug': {
                'level': 'INFO',
                'handlers': ['console', 'file'],
                'propagate': False,
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    })