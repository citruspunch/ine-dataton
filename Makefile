PY := .venv/bin/python

.PHONY: setup demo seed test serve mcp validate verify export clean

setup:
	python3 -m venv .venv
	.venv/bin/pip install --quiet --upgrade pip
	.venv/bin/pip install --quiet -r requirements.txt -r requirements-dev.txt
	@echo "listo: 'make demo' prepara los datos y arranca la interfaz"

demo: setup seed serve

seed:
	$(PY) tools/run_demo.py --reset

test:
	$(PY) -m pytest -q

serve:
	$(PY) app.py

mcp:
	$(PY) mcp_server.py

validate:
	$(PY) -m idt validate

verify:
	$(PY) -m idt verify

export:
	$(PY) -m idt export ipc_empalme

clean:
	rm -rf .venv
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
