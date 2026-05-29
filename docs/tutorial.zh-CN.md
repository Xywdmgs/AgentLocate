# AgentLocate 中文教程

AgentLocate 是一个面向 AI Agent、LangChain、RPA、GUI 自动化和数据标注的视觉定位 SDK/框架。

它做的事情是：用户传入图片或截图路径，以及自然语言描述，例如“登录按钮”“右上角设置图标”，AgentLocate 返回目标位置：

- `bbox`: 目标框，格式为 `x1, y1, x2, y2`
- `center`: 目标中心点
- `click`: 推荐点击坐标
- `codegen`: Playwright、DrissionPage、Appium、PyAutoGUI 点击代码

重要说明：AgentLocate 是框架和 SDK，不是模型权重仓库。它不内置 LocateAnything-3B 或其他模型权重。你需要接入远程推理服务、本地模型后端，或者自己实现一个后端。

## 安装

从 GitHub 安装：

```bash
pip install git+https://github.com/Xywdmgs/AgentLocate.git
```

本地开发安装：

```bash
git clone https://github.com/Xywdmgs/AgentLocate.git
cd AgentLocate
pip install -e .
```

可选依赖：

```bash
pip install -e ".[server]"      # FastAPI 服务端
pip install -e ".[langchain]"   # LangChain StructuredTool
pip install -e ".[local]"       # Pillow 等本地图像工具
pip install -e ".[locateanything]"  # 本地 LocateAnything-3B 推理依赖
```

## 5 分钟自测：不需要模型也能跑通

AgentLocate 内置了 `mock` 后端，专门用于测试安装、导入、schema、点击代码生成、LangChain 和 FastAPI 链路。

注意：`mock` 不做真实视觉定位，它只返回固定 bbox。真实定位需要换成 `remote_api`、本地 LocateAnything-3B 后端，或你自己的 Backend。

```python
from agent_locate import Locator

locator = Locator(
    backend="mock",
    backend_kwargs={"bbox": [100, 120, 260, 200]},
)

response = locator.locate("screenshot.png", "登录按钮")

print(response.result.bbox)
print(response.result.click)
print(response.codegen.playwright)
```

运行示例：

```bash
python examples/basic_locate.py
```

## 接入真实推理服务

如果你已经有一个远程视觉定位服务，可以使用 `remote_api`：

```python
from agent_locate import Locator

locator = Locator(
    backend="remote_api",
    backend_kwargs={"endpoint": "http://localhost:8000/locate"},
)

response = locator.locate("screenshot.png", "登录按钮")

print(response.result.bbox)
print(response.result.center)
print(response.result.click)
print(response.codegen.playwright)
```

输出示例：

```python
BBox(x1=100, y1=200, x2=180, y2=240)
(140, 220)
(140, 220)
await page.mouse.click(140, 220)
```

## remote_api 后端协议

`remote_api` 是通用远程后端。它会向你的远程服务发送 JSON：

```json
{
  "image_path": "screenshot.png",
  "query": "登录按钮",
  "top_k": 1,
  "context": null,
  "metadata": {}
}
```

如果远程服务无法读取你的本地图片路径，可以让 SDK 把图片内容一起发送：

```python
locator = Locator(
    "remote_api",
    backend_kwargs={
        "endpoint": "http://your-gpu-server/locate",
        "include_image": True,
    },
)
```

这时请求里的 `metadata` 会包含：

- `image_base64`
- `image_mime_type`

你的服务需要返回：

```json
{
  "bbox": {"x1": 100, "y1": 200, "x2": 180, "y2": 240},
  "label": "登录按钮",
  "confidence": 0.92,
  "backend": "your-model"
}
```

也可以返回：

```json
{
  "result": {
    "bbox": {"x1": 100, "y1": 200, "x2": 180, "y2": 240},
    "label": "登录按钮",
    "confidence": 0.92
  }
}
```

## 启动 FastAPI 服务

安装服务端依赖：

```bash
pip install -e ".[server]"
```

启动服务：

```bash
uvicorn agent_locate.server:app --host 0.0.0.0 --port 8000
```

默认服务使用 `mock` 后端，所以安装服务端依赖后可以直接启动并测试接口。真实推理时再设置 `AGENT_LOCATE_BACKEND=remote_api` 或 `AGENT_LOCATE_BACKEND=locateanything`。

如果你希望这个服务转发到另一个远程推理服务：

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

## LangChain 使用

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
    "query": "设置按钮",
    "context": "用户想打开设置页"
})

print(result)
```

## DrissionPage 点击

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
response = locator.locate(screenshot_path, "More information 链接")

x, y = response.result.click
page.actions.click(x, y)
```

## 自定义后端

如果你有自己的模型，只需要实现 `Backend`：

```python
from agent_locate.backends.base import Backend
from agent_locate.schema import BBox, LocateRequest, LocateResult

class MyBackend(Backend):
    name = "my_backend"

    def locate(self, request: LocateRequest) -> LocateResult:
        # 在这里调用你的模型
        return LocateResult(
            bbox=BBox(x1=100, y1=200, x2=180, y2=240),
            label=request.query,
            confidence=0.9,
            backend=self.name,
        )
```

然后：

```python
from agent_locate import Locator

locator = Locator(backend=MyBackend())
response = locator.locate("screenshot.png", "登录按钮")
```

## LocateAnything-3B 说明

AgentLocate 已经提供 `LocateAnythingBackend`，用于接入本地 `nvidia/LocateAnything-3B`。

但是本项目不提供模型权重，不重新分发模型，也不改变模型许可证。LocateAnything-3B 的下载、使用、商用和分发规则，以 NVIDIA 官方仓库和官方许可证为准。

CPU 跑通示例：

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

response = locator.locate("screenshot.png", "登录按钮")
print(response.result.bbox)
print(response.result.click)
print(response.codegen.pyautogui)
```

也可以直接运行仓库里的 CPU 示例：

```bash
python examples/local_locateanything_cpu.py
```

CPU 可以跑通，但会比 GPU 慢很多。生产环境建议把模型部署在 GPU 机器上，然后通过 `remote_api` 调用。
