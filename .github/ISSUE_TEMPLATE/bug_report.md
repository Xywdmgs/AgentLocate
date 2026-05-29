---
name: Bug report
about: Report a reproducible problem in AgentLocate
title: "[Bug]: "
labels: bug
assignees: ""
---

## What happened?

Describe the issue clearly.

## Minimal reproduction

```python
from agent_locate import Locator

locator = Locator("mock")
response = locator.locate("screen.png", "button")
print(response)
```

## Expected behavior

What did you expect to happen?

## Environment

- OS:
- Python version:
- AgentLocate install method:
- Backend: `mock` / `remote_api` / `locateanything` / custom
- If using `locateanything`, model path:

## Logs or error output

Paste the full traceback or relevant logs.

