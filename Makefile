#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_NAME = tech_challenge_fase4
PYTHON_VERSION = 3.10
PYTHON_INTERPRETER = python

#################################################################################
# COMMANDS                                                                      #
#################################################################################


## Install Python dependencies
.PHONY: requirements
requirements:
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -r requirements.txt
	



## Delete all compiled Python files
.PHONY: clean
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete


## Lint using flake8, black, and isort (use `make format` to do formatting)
.PHONY: lint
lint:
	flake8 tech_challenge_fase4 tests
	isort --check --diff tech_challenge_fase4 tests
	black --check tech_challenge_fase4 tests

## Format source code with black
.PHONY: format
format:
	isort tech_challenge_fase4 tests
	black tech_challenge_fase4 tests





## Set up Python interpreter environment
.PHONY: create_environment
create_environment:
	poetry env use $(PYTHON_VERSION)
	@echo ">>> Poetry environment created. Activate with: "
	@echo '$$(poetry env activate)'
	@echo ">>> Or run commands with:\npoetry run <command>"




#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Run unit tests (no Gemini API calls)
.PHONY: test
test:
	$(PYTHON_INTERPRETER) -m pytest -q

## Build the ChromaDB vector store with Gemini embeddings (resumable)
.PHONY: vector_store
vector_store:
	$(PYTHON_INTERPRETER) -m tech_challenge_fase4.vector_store

## Evaluate retrieval quality with the test queries
.PHONY: avaliar
avaliar:
	$(PYTHON_INTERPRETER) -m tech_challenge_fase4.avaliacao



#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys; \
lines = '\n'.join([line for line in sys.stdin]); \
matches = re.findall(r'\n## (.*)\n[\s\S]+?\n([a-zA-Z_-]+):', lines); \
print('Available rules:\n'); \
print('\n'.join(['{:25}{}'.format(*reversed(match)) for match in matches]))
endef
export PRINT_HELP_PYSCRIPT

help:
	@$(PYTHON_INTERPRETER) -c "${PRINT_HELP_PYSCRIPT}" < $(MAKEFILE_LIST)
