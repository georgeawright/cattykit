"""Filesystem locations used by every Copycat reproduction stage."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATASETS = ROOT / "datasets" / "copycat-reproduction"
PAPER = ROOT / "papers" / "copycat-reproduction"
FIGURES = PAPER / "figures"
TABLES = PAPER / "tables"
TEMPLATE_PATH = DATASETS / "original_copycat_results.template.json"
GOLD_PATH = DATASETS / "original_copycat_results.json"
