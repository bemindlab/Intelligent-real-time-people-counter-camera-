# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Test/Lint Commands

- Install for development: `pip install -e ".[dev]"` or `pip install -r requirements-dev.txt`
- Run app: `python3 camera/main.py`
- Run all tests: `pytest tests/`
- Run specific tests: `pytest tests/camera/` or `pytest tests/camera/test_camera.py::test_function`
- Run tests on macOS: `python tests/run_tests_macos.py`
- Install pre-commit hooks: `pre-commit install`
- Run linting manually: `pre-commit run --all-files`

## Code Style Guidelines

- Follow PEP 8 for formatting (100 char line length)
- Use Google docstring style in Thai
- Type hints recommended for all functions and methods
- Commit format: `type(scope): description` (e.g., `feat(detection): add new feature`)
- Error handling with specific exception types and informative messages
- Import order: stdlib, third-party, local modules (alphabetically within groups)
- Naming: snake_case for variables/functions, CamelCase for classes
- All files should include header docstrings explaining their purpose
- Code is automatically formatted with Black and isort through pre-commit hooks

## D2 Diagrams

- Generate SVG diagrams: `./scripts/generate_diagrams.sh`
- D2 documentation: [D2 Documentation](https://d2lang.com/tour/intro)
- When updating system components, update the corresponding D2 diagram in `docs/d2/`
- After modifying D2 files, generate SVG files for documentation

## Documents Links

- [Raspberry Pi](https://www.raspberrypi.com/documentation/)
- [n8n](https://docs.n8n.io/)
- [D2](https://d2lang.com/)

# Company Infomation

- Bemind Technology Co., Ltd.
- Email: info@bemind.tech
- GitHub: https://github.com/bemindlab
