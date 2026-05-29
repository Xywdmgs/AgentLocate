# Security Policy

AgentLocate is an SDK/framework and does not ship model weights.

## Reporting A Vulnerability

Please open a private security advisory on GitHub if the issue could expose credentials, execute untrusted code unexpectedly, or compromise users running AgentLocate services.

Do not include secrets, private screenshots, private model endpoints, or access tokens in public issues.

## Backend And Remote Code Notes

The local `locateanything` backend uses `trust_remote_code=True` because `nvidia/LocateAnything-3B` provides custom Transformers model code. Only run local model backends from sources you trust.

For `remote_api`, protect endpoints with authentication when exposing them outside a trusted network.

