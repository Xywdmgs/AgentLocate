from pathlib import Path

from PIL import Image, ImageDraw

from agent_locate import Locator


def main() -> None:
    model_path = r"D:\models\LocateAnything-3B"
    image_path = Path("red_square.png")

    image = Image.new("RGB", (224, 224), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle([70, 80, 150, 160], fill="red")
    image.save(image_path)

    locator = Locator(
        "locateanything",
        backend_kwargs={
            "model_path": model_path,
            "device": "cpu",
            "dtype": "float32",
            "generation_mode": "slow",
            "max_new_tokens": 128,
            "temperature": 0.0,
            "do_sample": False,
            "verbose": False,
        },
    )

    response = locator.locate(str(image_path), "the red square")
    print(response.model_dump_json(indent=2))
    print(response.codegen.pyautogui)


if __name__ == "__main__":
    main()
