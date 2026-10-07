.DEFAULT_GOAL := all

.PHONY: all baseline

all:
	uv run python 00_run_baseline.py
	uv run python 01_run_removal_methods.py
	uv run python 02_run_with_quantization.py
	uv run python 10_analyse_baseline.py
	uv run python 13_analyse_codelets_vs_temperature.py
	uv run python 14_analyse_codelets_vs_snags.py
	uv run python 11_analyse_removal_methods.py
	uv run python 12_analyse_quantisation.py
	uv run python 21_plot_basic_problems.py
	uv run python 23_plot_quantized_basic_problems.py

baseline:
	uv run python 00_run_baseline.py
	uv run python 10_analyse_baseline.py
	uv run python 13_analyse_codelets_vs_temperature.py
	uv run python 14_analyse_codelets_vs_snags.py
	uv run python 21_plot_basic_problems.py
