"""
Database module for anyplot.

Provides database connection, models, and repositories.
"""

from core.database.connection import (
    AsyncSessionLocal,
    Base,
    close_db,
    engine,
    get_db,
    get_db_context,
    init_db,
    is_db_configured,
)
from core.database.models import (
    AGENT_CASE_EXPECTED,
    CASE_ID_LENGTH,
    FEEDBACK_REACTIONS,
    FEEDBACK_STATUSES,
    LANGUAGES_SEED,
    LIBRARIES_SEED,
    AgentFeedback,
    Feedback,
    Impl,
    Language,
    Library,
    Spec,
)
from core.database.repositories import (
    AgentFeedbackRepository,
    BaseRepository,
    FeedbackRepository,
    ImplRepository,
    LanguageRepository,
    LibraryRepository,
    SpecRepository,
)


__all__ = [
    # Connection
    "engine",
    "AsyncSessionLocal",
    "Base",
    "get_db",
    "get_db_context",
    "init_db",
    "close_db",
    "is_db_configured",
    # Models
    "Spec",
    "Library",
    "Language",
    "Impl",
    "Feedback",
    "FEEDBACK_REACTIONS",
    "FEEDBACK_STATUSES",
    "AgentFeedback",
    "AGENT_CASE_EXPECTED",
    "CASE_ID_LENGTH",
    "LIBRARIES_SEED",
    "LANGUAGES_SEED",
    # Repositories
    "BaseRepository",
    "SpecRepository",
    "LibraryRepository",
    "LanguageRepository",
    "ImplRepository",
    "FeedbackRepository",
    "AgentFeedbackRepository",
]
