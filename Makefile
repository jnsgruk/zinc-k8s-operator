PROJECT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

SRC := $(PROJECT)src
TESTS := $(PROJECT)tests
ALL := $(SRC) $(TESTS)

export PYTHONPATH = $(PROJECT):$(PROJECT)/lib:$(SRC)

update-dependencies:
	uv lock -U --no-cache
	uv pip compile -q --no-cache pyproject.toml -o requirements.txt
	uv pip compile -q --no-cache --all-extras pyproject.toml -o requirements-dev.txt

generate-requirements:
	uv pip compile -q --no-cache $(PROJECT)pyproject.toml \
		-o $(PROJECT)requirements.txt
	uv pip compile -q --no-cache --all-extras $(PROJECT)pyproject.toml \
		-o $(PROJECT)requirements-dev.txt

lint:
	uv tool run ruff check $(ALL)
	uv tool run ruff format --check --diff $(ALL)

fmt:
	uv tool run ruff check --fix $(ALL)
	uv tool run ruff format $(ALL)

unit:
	uv tool run --with-requirements $(PROJECT)requirements-dev.txt \
		coverage run \
		--source=$(SRC) \
		-m pytest \
		--ignore=$(TESTS)/integration \
		--tb native \
		-v \
		-s \
		$(ARGS)
	uv tool run --with-requirements $(PROJECT)requirements-dev.txt coverage report

integration:
	uv tool run --with-requirements $(PROJECT)requirements-dev.txt \
		pytest -v \
		-s \
		--tb native \
		--ignore=$(TESTS)/unit \
		--log-cli-level=INFO \
		$(ARGS)
