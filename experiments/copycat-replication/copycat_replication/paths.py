"""Filesystem locations used by every Copycat reproduction stage."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATASETS = ROOT / "datasets" / "copycat-replication"
ORIGINAL_DATASETS = DATASETS / "original"
REPLICATION_DATASETS = DATASETS / "replication"
CODERACK_REMOVAL_DATASETS = DATASETS / "coderack_removal"
QUANTIZATION_DATASETS = DATASETS / "quantization"
SNAGS_DATASETS = DATASETS / "snags"
PAPER = ROOT / "papers" / "copycat-replication"
FIGURES = PAPER / "figures"
TABLES = PAPER / "tables"
TEMPLATE_PATH = ORIGINAL_DATASETS / "original_copycat_results.template.json"
GOLD_PATH = ORIGINAL_DATASETS / "original_copycat_results.json"
