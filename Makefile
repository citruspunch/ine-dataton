PY := .venv/bin/python

.PHONY: setup demo test validate verify site export clean

setup:
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet -r requirements.txt
	@echo "listo: use 'make demo'"

demo: setup
	$(PY) tools/run_demo.py --reset

test:
	$(PY) -m unittest discover -s tests -v

validate:
	$(PY) -m idt validate

verify:
	$(PY) -m idt verify

site:
	$(PY) -m idt site

export:
	$(PY) -m idt export ipc_empalme

clean:
	rm -rf .venv
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
