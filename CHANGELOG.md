# Changelog

## Unreleased

- Added `MockBackend` for zero-model smoke testing.
- Made the FastAPI server default to the mock backend so new users can test the route immediately.
- Added optional `remote_api` image payload support through `include_image=True`.
- Updated examples and bilingual tutorials with a runnable first path.

## 0.1.0

- Initial SDK skeleton.
- Added Pydantic request and response schemas.
- Added `Locator` orchestration API.
- Added `remote_api` backend.
- Added extensible `LocateAnythingBackend` placeholder for local `nvidia/LocateAnything-3B` integration.
- Added FastAPI server entry point.
- Added LangChain `StructuredTool` integration.
- Added Playwright, DrissionPage, Appium, and PyAutoGUI click code generation.
- Added YOLO and COCO exporters.
- Added examples and documentation.
