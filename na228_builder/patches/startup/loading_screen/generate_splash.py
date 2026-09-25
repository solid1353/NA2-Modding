"""Derive the standalone boot splash CCS from the 4:3 artwork."""

from __future__ import annotations

import gzip
from pathlib import Path

from PIL import Image

from na228_builder.infrastructure.orchestration.source_media import cvm_members
from scripts.lib.paths import load_paths
from scripts.research.ui_translation.texture_derivation import parse_ccs, sha256


SOURCE_LOGO_SHA256 = "101A7F51FFC92476AE47D56C205C111DA99709EF98109E9784BB45152B1ED1D9"
SOURCE_SPLASH_SHA256 = "EB878A42F07B4F965A2400803FE9A100BD378A5078EAD5EC9BEB54D211358810"
TARGET_TEXTURES = (
    "d\\logo\\tex\\logo_bn_pss.bmp",
    "d\\logo\\tex\\logo_b_pss.bmp",
    "x\\logo\\logo_adx_pss.bmp",
)
OUTPUT_PATH = Path("na228_builder/patches/startup/loading_screen/228SPL.ccs.gz")


def main() -> None:
    paths = load_paths(Path(__file__).resolve().parents[4])
    source, _header = cvm_members(paths.path("source_na2"))
    original = source.read_file(source.by_path["LOGO.CCS"])
    if sha256(original) != SOURCE_LOGO_SHA256:
        raise ValueError("Clean NA2 LOGO.CCS differs from the verified source")

    splash_path = paths.repository / "assets/artwork/splash.png"
    if sha256(splash_path.read_bytes()) != SOURCE_SPLASH_SHA256:
        raise ValueError("NA2.28 splash differs from the approved artwork")

    payload = bytearray(gzip.decompress(original))
    entries = parse_ccs(payload)
    image = Image.open(splash_path).convert("RGB").resize(
        (1024, 768), Image.Resampling.LANCZOS
    )
    # Each existing 512x512 texture stores one 1024x256 image row as four
    # 256x256 tiles. The three rows use separate 256-color palettes.
    for row, name in enumerate(TARGET_TEXTURES):
        entry = entries[name.casefold()]
        if len(entry.textures) != 1 or len(entry.palettes) != 1:
            raise ValueError(f"{name}: expected one texture and palette")
        texture, palette = entry.textures[0], entry.palettes[0]
        if texture.data_size != 262168 or palette.data_size != 1040:
            raise ValueError(f"{name}: expected a 512x512 8-bit texture")

        strip = image.crop((0, row * 256, 1024, (row + 1) * 256))
        indexed = strip.quantize(
            colors=256, method=Image.Quantize.MEDIANCUT,
            kmeans=1, dither=Image.Dither.NONE
        )
        atlas = Image.new("P", (512, 512))
        atlas.putpalette(indexed.getpalette())
        for column in range(4):
            atlas.paste(
                indexed.crop((column * 256, 0, (column + 1) * 256, 256)),
                ((column % 2) * 256, (column // 2) * 256),
            )

        pixels = atlas.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
        colors = atlas.getpalette()[:768]
        if len(pixels) != 512 * 512 or len(colors) != 256 * 3:
            raise ValueError(f"{name}: derived atlas has the wrong size")
        texture_start = texture.data_offset + 0x18
        palette_start = palette.data_offset + 0x10
        payload[texture_start:texture_start + len(pixels)] = pixels
        payload[palette_start:palette_start + 1024] = bytes(
            component
            for index in range(256)
            for component in (*colors[index * 3:index * 3 + 3], 0x80)
        )

    result = gzip.compress(bytes(payload), compresslevel=9, mtime=0)
    output = paths.repository / OUTPUT_PATH
    output.write_bytes(result)
    print(f"{output.relative_to(paths.repository)}\t{len(result)}\t{sha256(result)}")


if __name__ == "__main__":
    main()
