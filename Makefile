.PHONY: pdf pdf-print check

pdf:
	cd nwputhesis && latexmk graduate.tex

pdf-print:
	cd nwputhesis && latexmk graduate-print.tex

check:
	python3 scripts/verify_transfer.py
