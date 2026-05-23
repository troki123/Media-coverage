import os
import logging
from logging.config import dictConfig
from datetime import datetime, timezone


def setup_logging():
    # Osiguranje foldera
    if not os.path.exists("logs"):
        os.makedirs("logs")

    date_str = datetime.now(timezone.utc).strftime("%d_%m_%Y_")

    # Globalna konfiguracija logiranja za cijelu aplikaciju
    dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
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
            'news_summary': {
                'level' : 'DEBUG',
                'handlers' : ['console', 'file'],
                'propagate': False,
            },
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