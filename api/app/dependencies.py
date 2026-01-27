"""
Dependency Injection
Shared dependencies for FastAPI routes
"""

from functools import lru_cache


import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db
from processor import Processor


@lru_cache
def get_processor() -> Processor:
    """Get cached Processor instance"""
    return Processor()


# Re-export get_db for convenience
__all__ = ["get_db", "get_processor"]
