import unittest
import importlib.resources
import os
from pathlib import Path
from unittest.mock import patch

from agent_locate.backends.mock import MockBackend
from agent_locate.backends.base import Backend
from agent_locate.backends.locateanything import LocateAnythingBackend, parse_locateanything_output
from agent_locate.backends.remote_api import RemoteAPIBackend
from agent_locate.locator import Locator
from agent_locate.server import _locator_from_env
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

    def test_mock_backend_makes_package_runnable_without_model(self):
        locator = Locator(backend="mock", backend_kwargs={"bbox": [5, 10, 45, 50]})

        response = locator.locate("screen.png", "demo button")

        self.assertEqual(response.result.backend, "mock")
        self.assertEqual(response.result.label, "demo button")
        self.assertEqual(response.result.click, (25, 30))

    def test_parse_locateanything_box_output_scales_to_pixels(self):
        result = parse_locateanything_output(
            "target <box><100><200><500><800></box>",
            image_width=1000,
            image_height=500,
            label="button",
        )

        self.assertEqual(result.bbox.x1, 100)
        self.assertEqual(result.bbox.y1, 100)
        self.assertEqual(result.bbox.x2, 500)
        self.assertEqual(result.bbox.y2, 400)
        self.assertEqual(result.label, "button")

    def test_parse_locateanything_point_output_creates_small_click_box(self):
        result = parse_locateanything_output(
            "<box><500><250></box>",
            image_width=200,
            image_height=100,
            label="search icon",
            point_box_size=10,
        )

        self.assertEqual(result.click, (100, 25))
        self.assertEqual(result.bbox.x1, 95)
        self.assertEqual(result.bbox.y1, 20)
        self.assertEqual(result.bbox.x2, 105)
        self.assertEqual(result.bbox.y2, 30)

    def test_parse_locateanything_output_rejects_missing_coordinates(self):
        with self.assertRaises(ValueError):
            parse_locateanything_output("no box here", image_width=100, image_height=100)

    def test_locateanything_backend_uses_injected_worker_without_loading_model(self):
        class FakeWorker:
            def ground_gui(self, image, phrase, output_type="box", **kwargs):
                self.image_size = image.size
                self.phrase = phrase
                self.output_type = output_type
                return {"answer": "<box><100><200><500><800></box>"}

        image_path = Path("tests") / "fake_image.png"
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is required for this test")
        Image.new("RGB", (100, 50), color="white").save(image_path)
        self.addCleanup(lambda: image_path.unlink(missing_ok=True))

        worker = FakeWorker()
        backend = LocateAnythingBackend(model=worker)

        result = backend.locate(LocateRequest(image_path=image_path, query="login button"))

        self.assertEqual(worker.image_size, (100, 50))
        self.assertEqual(worker.phrase, "login button")
        self.assertEqual(worker.output_type, "box")
        self.assertEqual(result.click, (30, 25))

    def test_server_defaults_to_mock_backend_for_smoke_testing(self):
        with patch.dict(os.environ, {}, clear=True):
            locator = _locator_from_env()

        self.assertIsInstance(locator.backend, MockBackend)

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

    def test_remote_api_can_include_image_base64_payload(self):
        sent_payloads = []

        class FakeResponse:
            def raise_for_status(self):
                return None

            def json(self):
                return {
                    "bbox": {"x1": 1, "y1": 2, "x2": 11, "y2": 22},
                    "label": "ok button",
                    "confidence": 0.75,
                }

        class FakeClient:
            def __init__(self, timeout):
                self.timeout = timeout

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def post(self, endpoint, json, headers):
                sent_payloads.append(json)
                return FakeResponse()

        image_path = Path("tests") / "tiny.bin"
        image_path.write_bytes(b"abc")
        self.addCleanup(lambda: image_path.unlink(missing_ok=True))

        backend = RemoteAPIBackend("https://api.example.test/locate", include_image=True)

        with patch("agent_locate.backends.remote_api.httpx.Client", FakeClient):
            backend.locate(LocateRequest(image_path=image_path, query="ok button"))

        metadata = sent_payloads[0]["metadata"]
        self.assertEqual(metadata["image_base64"], "YWJj")
        self.assertEqual(metadata["image_mime_type"], "application/octet-stream")


if __name__ == "__main__":
    unittest.main()
