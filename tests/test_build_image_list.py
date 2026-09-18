import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "build_image_list",
    Path(__file__).resolve().parent.parent / "_transcription" / "build_image_list.py",
)
build_image_list = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_image_list)


def test_parse_frontmatter_longer_than_8kb(tmp_path):
    # Regression: the builder used to read only 8192 bytes, so a doc with a
    # long notable_* list never found its closing --- and was silently dropped.
    fm = "---\nomeka_id: 42438\nimages:\n- aaa.jpg\n- bbb.jpg\nnotable_items:\n"
    fm += "".join(f"- item number {i}\n" for i in range(600))
    fm += "---\n\nbody\n"
    assert len(fm) > 8192
    doc = tmp_path / "42438.md"
    doc.write_text(fm)
    parsed = build_image_list.parse_frontmatter(doc)
    assert parsed == {"omeka_id": "42438", "images": ["aaa.jpg", "bbb.jpg"]}
