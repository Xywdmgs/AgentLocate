# AgentLocate

[![CI](https://github.com/agent-locate/agent-locate/actions/workflows/ci.yml/badge.svg)](https://github.com/agent-locate/agent-locate/actions/workflows/ci.yml)

AgentLocate is an open-source Python SDK/framework for natural-language visual localization. It is built for AI Agents, LangChain tools, RPA workflows, GUI automation, and data annotation pipelines.

中文教程: [docs/tutorial.zh-CN.md](docs/tutorial.zh-CN.md)

English tutorial: [docs/tutorial.en.md](docs/tutorial.en.md)

Given an image or screenshot path plus a natural-language description, AgentLocate returns:

- target `bbox` in pixel coordinates
- center point and click coordinates
- ready-to-use click snippets for Playwright, DrissionPage, Appium, and PyAutoGUI

AgentLocate is a framework and SDK. It is not a model weight repository and does not ship model weights. To perform real localization, connect a `remote_api` inference service, plug in a local model backend, or implement your own backend.

## Model And License Note

AgentLocate can be extended to use `nvidia/LocateAnything-3B` as a local backend, but the first release does not include any model weights or vendored inference code. Download, use, and redistribute model artifacts only according to the official `nvidia/LocateAnything-3B` license and documentation.

This repository's SDK code is MIT licensed.

## Install As A Package

From PyPI after release:

```bash
pip install agent-locate
```

From GitHub before release:

```bash
pip install git+https://github.com/YOUR_NAME/AgentLocate.git
```

For local development:

```bash
pip install -e .
```

Optional extras:

```bash
pip install -e ".[server]"
pip install -e ".[langchain]"
pip install -e ".[local]"
```

## Basic Usage

```python
from agent_locate import Locator

locator = Locator(
    backend="remote_api",
    backend_kwargs={"endpoint": "https://your-gpu-host.example.com/locate"},
)

response = locator.locate("screenshot.png", "the blue submit button")

print(response.result.bbox)
print(response.result.click)
print(response.codegen.playwright)
```

Users import the Python package as `agent_locate`. The distributable package name is `agent-locate`.

## How Users Should Think About This Project

AgentLocate provides the stable SDK layer:

- typed request and response schemas
- backend interface
- remote inference client
- FastAPI service wrapper
- LangChain tool wrapper
- click code generation for automation tools
- annotation exporters

The actual visual grounding model lives behind a backend. For production use, run a model service and call it through `remote_api`, or implement `Backend` for your own inference stack.

## Backends

### `remote_api`

The remote API backend is the recommended first path for users without a local GPU. The endpoint receives a JSON `LocateRequest`:

```json
{
  "image_path": "screenshot.png",
  "query": "the blue submit button",
  "top_k": 1,
  "context": null,
  "metadata": {}
}
```

It should return either a raw result:

```json
{
  "bbox": {"x1": 10, "y1": 20, "x2": 120, "y2": 80},
  "label": "submit button",
  "confidence": 0.91,
  "backend": "locateanything"
}
```

or `{ "result": { ... } }`.

### `locateanything`

`LocateAnythingBackend` is a local integration stub for `nvidia/LocateAnything-3B`. It is intentionally written as an adapter class with TODO markers where the official model loading and inference pipeline should be connected.

## FastAPI Server

```bash
pip install -e ".[server]"
uvicorn agent_locate.server:app --host 0.0.0.0 --port 8000
```

For a proxy server that calls a remote inference endpoint:

```bash
set AGENT_LOCATE_BACKEND=remote_api
set AGENT_LOCATE_REMOTE_ENDPOINT=https://your-gpu-host.example.com/locate
uvicorn agent_locate.server:app --port 8000
```

## LangChain

```python
from agent_locate import Locator
from agent_locate.integrations.langchain import create_langchain_tool

locator = Locator("remote_api", backend_kwargs={"endpoint": "https://your-host/locate"})
tool = create_langchain_tool(locator)
```

## Examples

- `examples/basic_locate.py`
- `examples/langchain_tool.py`
- `examples/fastapi_client.py`
- `examples/drissionpage_click.py`

## Project Status

This is an early SDK skeleton focused on clean interfaces, testability, and extensibility. The public data schema and backend interface are intentionally small so additional backends can be added without changing agent-facing code.

## Development

```bash
python -m pip install -e ".[dev]"
python -m unittest discover -s tests
python -m compileall agent_locate examples
```

See `CONTRIBUTING.md` and `docs/publishing.md` for repository and release workflows.
