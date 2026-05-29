from __future__ import annotations

from .schema import ClickCode, LocateResult


def generate_click_code(result: LocateResult) -> ClickCode:
    """Generate click snippets for common browser/mobile/desktop automation tools."""

    x, y = result.click
    return ClickCode(
        playwright=f"await page.mouse.click({x}, {y})",
        drissionpage=f"page.actions.click({x}, {y})",
        appium=f"driver.tap([({x}, {y})])",
        pyautogui=f"pyautogui.click({x}, {y})",
    )

