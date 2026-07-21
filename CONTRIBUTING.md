## Contributing to ThingFlash

Thanks for your interest in contributing to ThingFlash!

## How to contribute

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Run the tests
5. Submit a pull request

## Installation

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the package in editable mode with dev dependencies
pip install -e ".[dev]"

# 3. Verify the CLI works
thingflash --help
```

## Running the tests

```bash
python3 -m pytest        # Run Tests
python3 -m ruff check .  # Lint 
```
