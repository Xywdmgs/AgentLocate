# LangChain Integration

AgentLocate provides a `StructuredTool` factory.

```python
from agent_locate import Locator
from agent_locate.integrations.langchain import create_langchain_tool

locator = Locator(
    "remote_api",
    backend_kwargs={"endpoint": "https://your-host/locate"},
)
tool = create_langchain_tool(locator)
```

The tool input schema is:

- `image_path`: screenshot or image path
- `query`: natural-language visual target
- `context`: optional task context

The tool returns JSON with bbox, center/click coordinates, and generated automation snippets.

