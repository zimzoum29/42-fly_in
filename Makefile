install:
	uv sync

# Usage: make run
#        make run ARGS="maps/hard/01_maze_nightmare.txt"
#        make run ARGS="--no-gui"
run:
	uv run python3 -m src $(ARGS)

debug:
	uv run python3 -m pdb -m src $(ARGS)

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache .pytest_cache data/output

lint:
	uv run python3 -m flake8 src
	uv run python3 -m mypy src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

lint-strict:
	uv run python3 -m flake8 src
	uv run python3 -m mypy src --strict
