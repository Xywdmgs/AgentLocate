import unittest
import importlib.resources
from pathlib import Path
from unittest.mock import patch

from agent_locate.backends.base import Backend
from agent_locate.backends.remote_api import RemoteAPIBackend
from agent_locate.locator import Locator
from agent_locate.schema import BBox, LocateRequest, LocateResult


class DummyBackend(Backend):
    name = "dummy"

    def locate(self, request: LocateRequest) -> LocateResult:
        return LocateResult(
            bbox=BBox(x1=10, y1=20, x2=50, y2=80),
            label=request.query,
            confidence=0.9,
            backend=self.name,
        )


class CoreTests(unittest.TestCase):
    def test_package_exposes_typed_marker_for_downstream_users(self):
        marker = importlib.resources.files("agent_locate").joinpath("py.typed")

        self.assertTrue(marker.is_file())

    def test_bbox_center_and_size_are_computed(self):
        bbox = BBox(x1=10, y1=20, x2=50, y2=80)

        self.assertEqual(bbox.width, 40)
        self.assertEqual(bbox.height, 60)
        self.assertEqual(bbox.center, (30, 50))

    def test_locator_returns_click_point_and_codegen(self):
        locator = Locator(backend=DummyBackend())

        response = locator.locate("screen.png", "submit button")

        self.assertEqual(response.result.center, (30, 50))
        self.assertEqual(response.result.click, (30, 50))
        self.assertIn("page.mouse.click(30, 50)", response.codegen.playwright)
        self.assertIn("page.actions.click(30, 50)", response.codegen.drissionpage)
        self.assertIn("driver.tap([(30, 50)])", response.codegen.appium)
        self.assertIn("pyautogui.click(30, 50)", response.codegen.pyautogui)

    def test_locator_accepts_backend_name_remote_api(self):
        locator = Locator(backend="remote_api", backend_kwargs={"endpoint": "https://example.test/locate"})

        self.assertEqual(locator.backend.name, "remote_api")

    def test_yolo_export_line(self):
        from agent_locate.exporters.yolo import to_yolo_line

        result = LocateResult(
            bbox=BBox(x1=10, y1=20, x2=50, y2=80),
            label="button",
            confidence=0.8,
            backend="dummy",
        )

        self.assertEqual(to_yolo_line(result, image_width=100, image_height=100, class_id=2), "2 0.300000 0.500000 0.400000 0.600000")

    def test_coco_annotation_contains_bbox_xywh(self):
        from agent_locate.exporters.coco import to_coco_annotation

        result = LocateResult(
            bbox=BBox(x1=10, y1=20, x2=50, y2=80),
            label="button",
            confidence=0.8,
            backend="dummy",
        )

        annotation = to_coco_annotation(result, image_id=1, category_id=3, annotation_id=9)

        self.assertEqual(annotation["bbox"], [10.0, 20.0, 40.0, 60.0])
        self.assertEqual(annotation["area"], 2400.0)

    def test_image_path_must_exist_when_validation_enabled(self):
        locator = Locator(backend=DummyBackend(), validate_images=True)

        with self.assertRaises(FileNotFoundError):
            locator.locate(Path("missing.png"), "target")

    def test_remote_api_backend_posts_request_and_parses_result(self):
        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "result": {
                        "bbox": {"x1": 1, "y1": 2, "x2": 11, "y2": 22},
                        "label": "ok button",
                        "confidence": 0.75,
                    }
                }

        class FakeClient:
            def __init__(self, timeout):
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, endpoint, json, headers):
                self.endpoint = endpoint
                self.payload = json
                self.headers = headers
                return FakeResponse()

        backend = RemoteAPIBackend("https://api.example.test/locate", api_key="secret", timeout=3)

        with patch("agent_locate.backends.remote_api.httpx.Client", FakeClient):
            result = backend.locate(LocateRequest(image_path="screen.png", query="ok button"))

        self.assertEqual(result.bbox.center, (6, 12))
        self.assertEqual(result.label, "ok button")
        self.assertEqual(result.backend, "remote_api")


if __name__ == "__main__":
    unittest.main()
