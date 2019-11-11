SHELL=/usr/bin/env bash
.PHONY: venv

venv:
	virtualenv venv
	source venv/bin/activate && pip install -r requirements.txt -t venv/lib
