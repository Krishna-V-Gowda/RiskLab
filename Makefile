.PHONY: test verify experiment clean

PYTHON ?= python3
export PYTHONPATH := src

test:
	$(PYTHON) -m unittest discover -s tests -v

verify:
	bash scripts/verify.sh

experiment:
	$(PYTHON) -m risklab.cli run --output-dir evidence/final --bootstrap-resamples 500

clean:
	rm -rf .verification build dist src/*.egg-info evidence/run-* evidence/final
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
