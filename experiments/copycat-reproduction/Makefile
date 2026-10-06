.DEFAULT_GOAL := all

.PHONY: all baseline

all:
	uv run python 00_run_baseline.py
	uv run python 01_run_removal_methods.py
	uv run python 10_analyse_baseline.py
	uv run python 11_analyse_removal_methods.py
	uv run python 21_plot_basic_problems.py

baseline:
	uv run python 00_run_baseline.py
	uv run python 10_analyse_baseline.py
	uv run python 21_plot_basic_problems.py
