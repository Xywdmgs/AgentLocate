# AgentLocate Tutorial

AgentLocate is a visual localization SDK/framework for AI Agents, LangChain, RPA, GUI automation, and data annotation.

It accepts an image or screenshot path plus a natural-language target description, such as "the login button" or "the settings icon", then returns:

- `bbox`: target box in `x1, y1, x2, y2` format
- `center`: target center point
- `click`: recommended click coordinate
- `codegen`: click snippets for Playwright, DrissionPage, Appium, and PyAutoGUI

Important: AgentLocate is a framework and SDK, not a model weight repository. It does not include LocateAnything-3B or any other model weights. To perform real localization, connect a remote inference service, plug in a local model backend, or implement your own backend.

## Installation

Install from GitHub:

```bash
pip install git+https://github.com/Xywdmgs/AgentLocate.git
```

Install for local development:

```bash
git clone https://github.com/Xywdmgs/AgentLocate.git
cd AgentLocate
pip install -e .
```

Optional extras:

```bash
pip install -e ".[server]"      # FastAPI server
pip install -e ".[langchain]"   # LangChain StructuredTool
pip install -e ".[local]"       # Pillow and local image utilities
pip install -e ".[locateanything]"  # Local LocateAnything-3B inference dependencies
```

## 5-Minute Smoke Test Without A Model

AgentLocate includes a `mock` backend for testing installation, imports, schemas, click code generation, LangChain wiring, and the FastAPI route.

Important: `mock` does not perform real visual grounding. It returns a fixed bbox. For real localization, switch to `remote_api`, a local LocateAnything-3B adapter, or your own Backend.

```python
from agent_locate import Locator

locator = Locator(
    backend="mock",
    backend_kwargs={"bbox": [100, 120, 260, 200]},
)

response = locator.locate("screenshot.png", "the login button")

print(response.result.bbox)
print(response.result.click)
print(response.codegen.playwright)
```

Run the included example:

```bash
python examples/basic_locate.py
```

## Connect Real Inference

If you already have a visual localization service, use the `remote_api` backend:

```python
from agent_locate import Locator

locator = Locator(
    backend="remote_api",
    backend_kwargs={"endpoint": "http://localhost:8000/locate"},
)

response = locator.locate("screenshot.png", "the login button")

print(response.result.bbox)
print(response.result.center)
print(response.result.click)
print(response.codegen.playwright)
```

Example output:

```python
BBox(x1=100, y1=200, x2=180, y2=240)
(140, 220)
(140, 220)
await page.mouse.click(140, 220)
```

## remote_api Backend Contract

The `remote_api` backend sends this JSON payload to your remote service:

```json
{
  "image_path": "screenshot.png",
  "query": "the login button",
  "top_k": 1,
  "context": null,
  "metadata": {}
}
```

If the remote service cannot read your local image path, ask the SDK to send the image content:

```python
locator = Locator(
    "remote_api",
    backend_kwargs={
        "endpoint": "http://your-gpu-server/locate",
        "include_image": True,
    },
)
```

The request metadata then includes:

- `image_base64`
- `image_mime_type`

Your service should return:

```json
{
  "bbox": {"x1": 100, "y1": 200, "x2": 180, "y2": 240},
  "label": "the login button",
  "confidence": 0.92,
  "backend": "your-model"
}
```

It may also return:

```json
{
  "result": {
    "bbox": {"x1": 100, "y1": 200, "x2": 180, "y2": 240},
    "label": "the login button",
    "confidence": 0.92
  }
}
```

## FastAPI Server

Install server dependencies:

```bash
pip install -e ".[server]"
```

Run the server:

```bash
uvicorn agent_locate.server:app --host 0.0.0.0 --port 8000
```

By default, the server uses `mock`, so the route is runnable immediately after installing server dependencies. Set `AGENT_LOCATE_BACKEND=remote_api` or `AGENT_LOCATE_BACKEND=locateanything` for real inference.

To run a proxy server that forwards requests to another inference endpoint:

Windows PowerShell:

```powershell
$env:AGENT_LOCATE_BACKEND="remote_api"
$env:AGENT_LOCATE_REMOTE_ENDPOINT="http://your-gpu-server/locate"
uvicorn agent_locate.server:app --port 8000
```

Linux/macOS:

```bash
export AGENT_LOCATE_BACKEND=remote_api
export AGENT_LOCATE_REMOTE_ENDPOINT=http://your-gpu-server/locate
uvicorn agent_locate.server:app --port 8000
```

## LangChain Usage

```python
from agent_locate import Locator
from agent_locate.integrations.langchain import create_langchain_tool

locator = Locator(
    "remote_api",
    backend_kwargs={"endpoint": "http://localhost:8000/locate"},
)

tool = create_langchain_tool(locator)

result = tool.invoke({
    "image_path": "screenshot.png",
    "query": "the settings button",
    "context": "The user wants to open settings."
})

print(result)
```

## DrissionPage Click

```python
from DrissionPage import ChromiumPage
from agent_locate import Locator

page = ChromiumPage()
page.get("https://example.com")

screenshot_path = "page.png"
page.get_screenshot(path=screenshot_path)

locator = Locator(
    "remote_api",
    backend_kwargs={"endpoint": "http://localhost:8000/locate"},
)
response = locator.locate(screenshot_path, "the More information link")

x, y = response.result.click
page.actions.click(x, y)
```

## Custom Backend

If you have your own model, implement `Backend`:

```python
from agent_locate.backends.base import Backend
from agent_locate.schema import BBox, LocateRequest, LocateResult

class MyBackend(Backend):
    name = "my_backend"

    def locate(self, request: LocateRequest) -> LocateResult:
        # Call your model here.
        return LocateResult(
            bbox=BBox(x1=100, y1=200, x2=180, y2=240),
            label=request.query,
            confidence=0.9,
            backend=self.name,
        )
```

Then:

```python
from agent_locate import Locator

locator = Locator(backend=MyBackend())
response = locator.locate("screenshot.png", "the login button")
```

## LocateAnything-3B Note

AgentLocate includes `LocateAnythingBackend` for local `nvidia/LocateAnything-3B` inference.

This project does not provide model weights, redistribute model files, or modify model licensing. Download, usage, commercial use, and redistribution of LocateAnything-3B are governed by NVIDIA's official repository and license.

CPU smoke test:

```python
from agent_locate import Locator

locator = Locator(
    "locateanything",
    backend_kwargs={
        "model_path": r"D:\models\LocateAnything-3B",
        "device": "cpu",
        "dtype": "float32",
        "generation_mode": "slow",
        "max_new_tokens": 128,
        "temperature": 0.0,
        "do_sample": False,
    },
)

response = locator.locate("screenshot.png", "the login button")
print(response.result.bbox)
print(response.result.click)
print(response.codegen.pyautogui)
```

You can also run the included CPU example:

```bash
python examples/local_locateanything_cpu.py
```

CPU inference works for smoke testing, but it is much slower than GPU inference. For production, run the model on a GPU host and call it through `remote_api`.
