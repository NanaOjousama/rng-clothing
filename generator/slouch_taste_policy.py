"""Backward-compatible slouch import for the generator-wide taste engine."""
from .taste_policy import RARITY_RANK, TasteReport, evaluate_recipe, report_dict

__all__ = ["RARITY_RANK", "TasteReport", "evaluate_recipe", "report_dict"]
