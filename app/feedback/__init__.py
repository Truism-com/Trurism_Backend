"""
Feedback Module

This package handles customer feedback functionality:
- Feedback submission (public/authenticated)
- Admin feedback management
- Feedback analytics (future scope)
"""

# Export commonly used components for easier imports

from .models import Feedback
from .schemas import (
    FeedbackCreate,
    FeedbackResponse,
    FeedbackListResponse,
)
from .services import FeedbackService