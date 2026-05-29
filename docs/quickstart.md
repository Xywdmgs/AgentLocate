# Quickstart

AgentLocate exposes one main SDK class: `Locator`.

The quickest way to verify installation is the `mock` backend. It returns a fixed bbox and does not perform real visual grounding.

```python
from agent_locate import Locator

locator = Locator(
    backend="mock",
    backend_kwargs={"bbox": [100, 120, 260, 200]},
)

response = locator.locate("screenshot.png", "the submit button")
print(response.result.bbox)
print(response.result.click)
```

The local `LocateAnythingBackend` is intentionally an adapter stub. It does not download or include `nvidia/LocateAnything-3B` weights.

For real localization, switch to `remote_api`, a local LocateAnything-3B adapter, or a custom backend.

## Local LocateAnything-3B CPU Smoke Test

After downloading `nvidia/LocateAnything-3B` to `D:\models\LocateAnything-3B`, run:

```bash
pip install -e ".[locateanything]"
python examples/local_locateanything_cpu.py
```

CPU inference is intended for validation, not speed.

## Run Tests

```bash
python -m unittest discover -s tests
```

## Run Server

```bash
pip install -e ".[server]"
uvicorn agent_locate.server:app --port 8000
```
