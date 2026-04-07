"""This module sets up the logging configuration for the PayU Authentication Service. It defines a structured log format that includes the timestamp, log level, logger name, and message. The logging is configured to output to standard output (stdout) with an INFO log level. A logger instance named "payu-auth-service" is created for use throughout the application to log relevant information, errors, and debug messages in a consistent and structured manner. This configuration allows for better observability and easier debugging of the authentication service by providing clear and organized log entries."""

import logging
import sys

# Structured log format
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
logging.basicConfig(level=logging.INFO, stream=sys.stdout, format=LOG_FORMAT)

logger = logging.getLogger("payu-auth-service")
