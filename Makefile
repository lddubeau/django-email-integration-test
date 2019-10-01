VENV_NAME=.venv
PYTHON=$(VENV_NAME)/bin/python

.PHONY: venv
venv:
	[ -e $(VENV_NAME) ] || python3 -m venv $(VENV_NAME)

.PHONY: dev-venv
dev-venv: venv
	$(VENV_NAME)/bin/pip install -r dev_requirements.txt


.PHONY: test
test:
	$(PYTHON) manage.py test -v 2
	$(PYTHON) -m mypy django_email_integration_test
