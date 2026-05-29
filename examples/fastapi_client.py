import httpx


def main() -> None:
    payload = {
        "image_path": "tests/fixtures/screenshot.png",
        "query": "the primary action button",
        "top_k": 1,
        "context": None,
        "metadata": {},
    }

    response = httpx.post("http://localhost:8000/locate", json=payload, timeout=60)
    response.raise_for_status()
    print(response.json())


if __name__ == "__main__":
    main()

