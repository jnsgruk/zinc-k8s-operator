set quiet # Recipes are silent by default
set export # Just variables are exported to the environment

PROJECT := invocation_directory()

SRC := PROJECT + "/src"
TESTS := PROJECT + "/tests"
ALL := SRC + " " + TESTS

PYTHONPATH := PROJECT + ":" + \
  SRC + ":" + \
  PROJECT + "/lib"

# List the available recipes
[private]
default:
  just --list

# Update uv.lock with the latest deps
lock:
  uv lock --upgrade --no-cache

# Generate requirements.txt from pyproject.toml
generate-requirements:
  uv export --frozen --no-hashes --format=requirements-txt -o requirements.txt

# Lint the code
lint:
  uv tool run ruff check $ALL
  uv tool run ruff format --check --diff $ALL

# Format the code
fmt:
  uv tool run ruff check --fix-only $ALL
  uv tool run ruff format $ALL

# Run unit tests
unit *args='':
  uv run --frozen --isolated --all-extras \
    coverage run \
    --source=$SRC \
    -m pytest \
    --ignore=$TESTS/integration \
    --tb native \
    -v \
    -s \
    "$@"
  uv run --all-extras coverage report

# Run integration tests
integration *args='':
  uv run --frozen --isolated --all-extras \
    pytest \
    -v \
    -x \
    -s \
    --tb native \
    --ignore=$TESTS/unit \
    --log-cli-level=INFO \
    "$@"

# Cleanup transient files
clean:
	rm -rf .coverage
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .venv
	rm -rf *.charm
	rm -rf *.rock
	rm -rf **/__pycache__
	rm -rf **/*.egg-info
	rm -rf requirements*.txt
