from pathlib import Path

from ....infrastructure.common import indexed_png_pixels
from ....infrastructure.modules.payload_builder.operations import PayloadFragment


def rematch_label_fragment(*, owner: str) -> PayloadFragment:
    return PayloadFragment(
        owner=owner,
        symbol="rematch_label_pixels",
        kind="rodata",
        alignment=16,
        payload=indexed_png_pixels(
            Path(__file__).with_name("rematch_label.png"), (96, 24), flip=True
        ),
    )
