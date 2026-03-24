"""
Skills package for Phoenix Coworker

Task-specific capabilities that can be registered with the kernel.
"""

from .organize_files import OrganizeFilesSkill
from .summarize import SummarizeSkill
from .morning_briefing import MorningBriefingSkill
from .code_review import CodeReviewSkill

__all__ = [
    "OrganizeFilesSkill",
    "SummarizeSkill",
    "MorningBriefingSkill",
    "CodeReviewSkill",
]
