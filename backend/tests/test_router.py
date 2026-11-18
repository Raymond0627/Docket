import tempfile
import shutil
from pathlib import Path
import pytest
from backend.engine.router import route_file, sanitize_path_component

def test_sanitize_path_component():
    assert sanitize_path_component("Juan Dela Cruz: Driver's?") == "Juan Dela Cruz Driver's"
    assert sanitize_path_component("ACME * Corp <2026>") == "ACME Corp 2026"

def test_route_file_copy():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        src_path = Path(src_dir) / "license.jpg"
        src_path.write_text("dummy image data")

        dest = route_file(
            source_file=src_path,
            destination_root=Path(dest_dir),
            owner="Raymond Gudito",
            doc_type="Driver's License",
            target_folder="Driver License",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="copy"
        )

        assert dest.exists()
        assert "Raymond Gudito" in str(dest)
        assert "Driver License" in str(dest)
        assert src_path.exists()  # Source remains intact with copy
        assert dest.read_text() == "dummy image data"

def test_route_file_unsorted():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        src_path = Path(src_dir) / "unknown.pdf"
        src_path.write_text("random content")

        dest = route_file(
            source_file=src_path,
            destination_root=Path(dest_dir),
            owner="Raymond Gudito",
            doc_type="Unsorted",
            target_folder="Unsorted",
            template="{owner}/{doc_type}/",
            is_unsorted=True,
            mode="copy"
        )

        assert dest.exists()
        assert "Unsorted" in str(dest)
        assert "Raymond Gudito" in str(dest)

def test_route_file_collision_avoidance():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        # Create first file
        src1 = Path(src_dir) / "doc.pdf"
        src1.write_text("content 1")
        dest1 = route_file(
            source_file=src1,
            destination_root=Path(dest_dir),
            owner="Maria Santos",
            doc_type="Payslip",
            target_folder="Payslip",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="copy",
            allow_duplicates=True,
        )
        assert dest1.name == "doc.pdf"

        # Create second file with same name
        src2 = Path(src_dir) / "sub" / "doc.pdf"
        src2.parent.mkdir()
        src2.write_text("content 2")
        dest2 = route_file(
            source_file=src2,
            destination_root=Path(dest_dir),
            owner="Maria Santos",
            doc_type="Payslip",
            target_folder="Payslip",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="copy",
            allow_duplicates=True,
        )
        assert dest2.name == "doc_1.pdf"
        assert dest1.exists()
        assert dest2.exists()
        assert dest1.read_text() == "content 1"
        assert dest2.read_text() == "content 2"

def test_route_file_no_duplicates_replaces_existing():
    """allow_duplicates=False purges old copies (incl. _1, _2) and keeps the original name."""
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        target = Path(dest_dir) / "Maria Santos" / "Payslip"
        target.mkdir(parents=True)
        # Leftovers from previous runs
        (target / "doc.pdf").write_text("stale copy")
        (target / "doc_1.pdf").write_text("stale copy 1")
        (target / "doc_2.pdf").write_text("stale copy 2")
        # Unrelated file that must survive
        (target / "other.pdf").write_text("keep me")

        src = Path(src_dir) / "doc.pdf"
        src.write_text("fresh content")
        dest = route_file(
            source_file=src,
            destination_root=Path(dest_dir),
            owner="Maria Santos",
            doc_type="Payslip",
            target_folder="Payslip",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="copy",
            allow_duplicates=False,
        )

        assert dest.name == "doc.pdf"
        assert dest.read_text() == "fresh content"
        assert not (target / "doc_1.pdf").exists()
        assert not (target / "doc_2.pdf").exists()
        assert (target / "other.pdf").read_text() == "keep me"
        assert src.exists()  # copy mode leaves source untouched

def test_route_file_no_duplicates_ignores_similar_names():
    """Purge must only touch the exact base name, not e.g. doc_final.pdf."""
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        target = Path(dest_dir) / "Invoice"
        target.mkdir(parents=True)
        (target / "doc_final.pdf").write_text("different file")

        src = Path(src_dir) / "doc.pdf"
        src.write_text("fresh")
        dest = route_file(
            source_file=src,
            destination_root=Path(dest_dir),
            owner="General",
            doc_type="Invoice",
            target_folder="Invoice",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="copy",
            allow_duplicates=False,
        )

        assert dest.name == "doc.pdf"
        assert (target / "doc_final.pdf").read_text() == "different file"

def test_route_file_move():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        src_path = Path(src_dir) / "move_me.pdf"
        src_path.write_text("move content")

        dest = route_file(
            source_file=src_path,
            destination_root=Path(dest_dir),
            owner="Juan",
            doc_type="COE",
            target_folder="COE",
            template="{owner}/{doc_type}/",
            is_unsorted=False,
            mode="move"
        )

        assert dest.exists()
        assert not src_path.exists()  # Source is deleted with move

def test_route_file_general_owner_has_no_general_folder():
    with tempfile.TemporaryDirectory() as src_dir, tempfile.TemporaryDirectory() as dest_dir:
        src_path = Path(src_dir) / "mystery.pdf"
        src_path.write_text("content")
        dest = route_file(
            source_file=src_path, destination_root=Path(dest_dir),
            owner="General", doc_type="Invoice", target_folder="Invoice",
            template="{owner}/", is_unsorted=False, mode="copy",
        )
        assert dest.parent == Path(dest_dir)
        assert "General" not in str(dest)
