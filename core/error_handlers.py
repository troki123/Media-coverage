from flask import jsonify
from werkzeug.exceptions import HTTPException
import logging

# Getting logger for this module (already works on logging_config rules)
logger = logging.getLogger(__name__)


# receives a flask 'app' object and registers global exception handling on it
def register_error_handlers(app):
    # Catches all unhandled exceptions in the aplication
    @app.errorhandler(Exception)
    def handle_global_exception(e):
        
        # If there is a standard HTTP exception (example: 404 Not Found).
        # We want to keep its original HTTP status code
        if isinstance(e, HTTPException):
            app.logger.warning(f"HTTP Error caught by global handler: {e.description} (Status: {e.code})")
            return jsonify ({
                "error": e.name,
                "message": e.description
            }), e.code
        
        # If there is an unexpected code crash (Example: KeyError, AttributeError, 500...)
        # Log the entire Stack Trace (exc_info=True) in our app.log file
        app.logger.error(f"GENERIC CRITICAL ERROR: {str(e)}", exc_info=True)

        # Return to the user a clear and secure JSON (hide internal details for security reasons)
        return jsonify({
            "error": "Internal Server Error",
            "message": "There was an unexpected server error. Details are recorded in logfiles."
        }), 500
