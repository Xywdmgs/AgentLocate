# Quickstart

AgentLocate exposes one main SDK class: `Locator`.

```python
from agent_locate import Locator

locator = Locator(
    backend="remote_api",
    backend_kwargs={"endpoint": "http://localhost:8000/locate"},
)

response = locator.locate("screenshot.png", "the submit button")
print(response.result.bbox)
print(response.result.click)
```

The local `LocateAnythingBackend` is intentionally an adapter stub. It does not download or include `nvidia/LocateAnything-3B` weights.

## Run Tests

```bash
python -m unittest discover -s tests
```

## Run Server

```bash
pip install -e ".[server]"
uvicorn agent_locate.server:app --port 8000
```

