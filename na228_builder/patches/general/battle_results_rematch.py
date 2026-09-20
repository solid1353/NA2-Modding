from pathlib import Path

from PIL import Image

from ...infrastructure.modules.payload_builder.operations import PayloadFragment


def rematch_label_fragment(*, owner: str) -> PayloadFragment:
    source = Path(__file__).with_name("rematch_label.png")
    with Image.open(source) as image:
        if image.size != (96, 24) or image.mode != "P":
            raise ValueError("rematch_label.png must be a 96x24 indexed PNG")
        pixels = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    return PayloadFragment(
        owner=owner,
        symbol="rematch_label_pixels",
        kind="rodata",
        alignment=16,
        payload=pixels,
    )
