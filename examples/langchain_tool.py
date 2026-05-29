from agent_locate import Locator
from agent_locate.integrations.langchain import create_langchain_tool


def main() -> None:
    locator = Locator(
        backend="mock",
        backend_kwargs={"bbox": [40, 60, 120, 140]},
    )
    tool = create_langchain_tool(locator)

    result = tool.invoke(
        {
            "image_path": "tests/fixtures/screenshot.png",
            "query": "the settings icon",
            "context": "Find the control the user should click next.",
        }
    )
    print(result)


if __name__ == "__main__":
    main()
