from DrissionPage import ChromiumPage

from agent_locate import Locator


def main() -> None:
    page = ChromiumPage()
    page.get("https://example.com")
    screenshot_path = "page.png"
    page.get_screenshot(path=screenshot_path)

    locator = Locator(
        backend="remote_api",
        backend_kwargs={"endpoint": "http://localhost:8000/locate"},
    )
    response = locator.locate(screenshot_path, "the More information link")

    x, y = response.result.click
    page.actions.click(x, y)


if __name__ == "__main__":
    main()

