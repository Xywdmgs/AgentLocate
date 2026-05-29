from agent_locate import Locator


def main() -> None:
    locator = Locator(
        backend="remote_api",
        backend_kwargs={"endpoint": "http://localhost:8000/locate"},
    )

    response = locator.locate("tests/fixtures/screenshot.png", "the login button")
    print(response.model_dump_json(indent=2))
    print(response.codegen.playwright)


if __name__ == "__main__":
    main()

