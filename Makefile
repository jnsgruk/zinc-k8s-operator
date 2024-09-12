PROJECT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))

SRC := $(PROJECT)src
TESTS := $(PROJECT)tests
ALL := $(SRC) $(TESTS)

export PYTHONPATH = $(PROJECT):$(PROJECT)/lib:$(SRC)

update-dependencies:
	uv lock -U --no-cache

generate-requirements:
	uv pip compile -q --no-cache pyproject.toml -o requirements.txt
	uv pip compile -q --no-cache --all-extras pyproject.toml -o requirements-dev.txt

lint:
	uv tool run ruff check $(ALL)
	uv tool run ruff format --check --diff $(ALL)

fmt:
	uv tool run ruff check --fix $(ALL)
	uv tool run ruff format $(ALL)

unit:
	uv run --all-extras \
		coverage run \
		--source=$(SRC) \
		-m pytest \
		--ignore=$(TESTS)/integration \
		--tb native \
		-v \
		-s \
		$(ARGS)
	uv run --all-extras coverage report

integration:
	uv run --all-extras \
		pytest -v \
		-s \
		--tb native \
		--ignore=$(TESTS)/unit \
		--log-cli-level=INFO \
		$(ARGS)
