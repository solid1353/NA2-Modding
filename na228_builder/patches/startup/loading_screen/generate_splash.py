"""Derive the standalone boot splash CCS from the 4:3 artwork."""

from __future__ import annotations

import gzip
from pathlib import Path

from PIL import Image

from na228_builder.infrastructure.orchestration.source_media import cvm_members
from scripts.lib.paths import load_paths
from scripts.research.ui_translation.texture_derivation import parse_ccs, sha256


SOURCE_LOGO_SHA256 = "101A7F51FFC92476AE47D56C205C111DA99709EF98109E9784BB45152B1ED1D9"
SOURCE_SPLASH_SHA256 = "02B29A27CBA8BC3843F324D15DE0FC4BF7334D4B2633FE615D4B51BB977DD466"
TARGET_TEXTURE = "d\\logo\\tex\\logo_bn_pss.bmp"
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
    entry = parse_ccs(payload)[TARGET_TEXTURE.casefold()]
    if len(entry.textures) != 1 or len(entry.palettes) != 1:
        raise ValueError("Boot splash target must have one texture and palette")
    texture, palette = entry.textures[0], entry.palettes[0]
    if texture.data_size != 262168 or palette.data_size != 1040:
        raise ValueError("Boot splash target is not a 512x512 8-bit texture")

    image = Image.open(splash_path).convert("RGB")
    # The 512x512 texture is drawn at 512x384, preserving the source's 4:3 shape.
    encoded = image.resize((512, 512), Image.Resampling.LANCZOS)
    indexed = encoded.quantize(colors=256, method=Image.Quantize.MEDIANCUT,
                               dither=Image.Dither.NONE)
    pixels = indexed.transpose(Image.Transpose.FLIP_TOP_BOTTOM).tobytes()
    colors = indexed.getpalette()[:768]
    if len(pixels) != 512 * 512 or len(colors) != 256 * 3:
        raise ValueError("Derived splash has the wrong image or palette size")

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
