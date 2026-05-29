from agent_locate import Locator


def main() -> None:
    locator = Locator(
        backend="mock",
        backend_kwargs={"bbox": [100, 120, 260, 200]},
    )

    response = locator.locate("screenshot.png", "the login button")
    print(response.model_dump_json(indent=2))
    print(response.codegen.playwright)


if __name__ == "__main__":
    main()
