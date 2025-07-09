# Makefile

# Format code using Ruff (like Black)
format:
	ruff format .

# Lint and fix issues that can be safely auto-fixed
fix:
	ruff check . --fix

# Full lint check without fixing
lint:
	ruff check .

# Fix everything including unsafe fixes (use carefully)
unsafe-fix:
	ruff check . --fix --unsafe-fixes


make format      # for formatting
make fix         # safe auto-fixes
make lint        # only check, don't fix
make unsafe-fix  # fix everything including unsafe ones
