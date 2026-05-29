# Publishing

This project is ready to publish as a normal Python package.

## Build

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

## Publish To TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

## Publish To PyPI

```bash
python -m twine upload dist/*
```

Before publishing, update:

- `pyproject.toml` version
- `agent_locate/__init__.py` `__version__`
- `CHANGELOG.md`

