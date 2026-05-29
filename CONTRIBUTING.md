# Contributing

Thanks for helping improve AgentLocate.

## Development Setup

```bash
git clone https://github.com/agent-locate/agent-locate.git
cd agent-locate
python -m pip install -e ".[dev]"
```

## Run Checks

```bash
python -m unittest discover -s tests
python -m compileall agent_locate examples
ruff check .
```

`ruff` is part of the `dev` extra. The standard-library test suite is intentionally runnable without `pytest`.

## Backend Contributions

Backends should implement `agent_locate.backends.base.Backend` and convert provider-specific output into `LocateResult`. Keep model loading, credentials, and heavyweight dependencies out of the default install path.

## Model Weights

Do not commit model weights, checkpoints, or large generated artifacts. AgentLocate is an SDK repository.

