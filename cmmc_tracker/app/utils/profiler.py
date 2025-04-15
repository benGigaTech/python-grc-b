"""Profiling utilities for the CMMC Tracker application."""

import time
import logging
import functools
from flask import g, request, current_app

# Avoid circular imports
# Do not import from app.services.database here

logger = logging.getLogger(__name__)

# Dictionary to store profiling data
_profiling_data = {}

def start_timer(name):
    """Start a timer for profiling."""
    if not hasattr(g, 'timers'):
        g.timers = {}
    g.timers[name] = time.time()

def stop_timer(name):
    """Stop a timer and return the elapsed time."""
    if hasattr(g, 'timers') and name in g.timers:
        elapsed = time.time() - g.timers[name]
        # Store in profiling data
        if name not in _profiling_data:
            _profiling_data[name] = []
        _profiling_data[name].append(elapsed)
        return elapsed
    return None

def get_average_time(name):
    """Get the average time for a named timer."""
    if name in _profiling_data and _profiling_data[name]:
        return sum(_profiling_data[name]) / len(_profiling_data[name])
    return None

def clear_profiling_data():
    """Clear all profiling data."""
    global _profiling_data
    _profiling_data = {}

def get_profiling_data():
    """Get all profiling data."""
    return _profiling_data

def profile(func=None, name=None):
    """Decorator to profile a function."""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            timer_name = name or f.__name__
            start_timer(timer_name)
            result = f(*args, **kwargs)
            elapsed = stop_timer(timer_name)
            logger.debug(f"Function {timer_name} took {elapsed:.4f} seconds")
            return result
        return wrapper

    if func:
        return decorator(func)
    return decorator

def init_app(app):
    """Initialize profiling middleware for the application."""
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            elapsed = time.time() - g.start_time
            logger.debug(f"Request {request.path} took {elapsed:.4f} seconds")

            # Only log slow requests in production
            if not app.debug and elapsed > 1.0:
                logger.warning(f"Slow request: {request.path} took {elapsed:.4f} seconds")

        return response
