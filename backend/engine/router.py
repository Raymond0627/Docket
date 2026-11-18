import os
import re
import shutil
from pathlib import Path
from typing import Optional

from backend.config import load_settings

def sanitize_path_component(name: str) -> str:
    """Removes invalid filesystem characters for Windows/POSIX paths."""
    # Invalid characters in Windows file/folder names: \ / : * ? " < > |
    sanitized = re.sub(r'[\\/:*?"<>|]', "", name).strip()
    sanitized = " ".join(sanitized.split())
    return sanitized or "Unknown"

def get_unique_destination_path(target_dir: Path, original_filename: str) -> Path:
    """Finds an available file path in target_dir by appending _1, _2 if needed."""
    candidate = target_dir / original_filename
    if not candidate.exists():
        return candidate

    source_path = Path(original_filename)
    stem = source_path.stem
    suffix = source_path.suffix

    counter = 1
    while True:
        candidate = target_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1

def purge_existing_copies(
    target_dir: Path,
    original_filename: str,
    keep_path: Optional[Path] = None,
) -> None:
    """Deletes an existing file with the same name plus its _1, _2... variants.

    Used when allow_duplicates is off so re-running the same source folder
    replaces previous copies instead of accumulating duplicates.
    keep_path protects a file that must not be deleted (e.g. the source file
    itself when it already sits at the destination).
    """
    source_path = Path(original_filename)
    stem = source_path.stem
    suffix = source_path.suffix
    variant_re = re.compile(
        rf"^{re.escape(stem)}_\d+{re.escape(suffix)}$", re.IGNORECASE
    )

    keep_resolved = None
    if keep_path is not None:
        try:
            keep_resolved = Path(keep_path).resolve()
        except OSError:
            keep_resolved = None

    try:
        entries = list(target_dir.iterdir())
    except OSError:
        return

    for entry in entries:
        if not entry.is_file():
            continue
        is_same_name = entry.name.lower() == original_filename.lower()
        if not is_same_name and not variant_re.match(entry.name):
            continue
        try:
            if keep_resolved is not None and entry.resolve() == keep_resolved:
                continue
            entry.unlink()
        except OSError:
            pass

def route_file(
    source_file: Path,
    destination_root: Path,
    owner: str,
    doc_type: str,
    target_folder: Optional[str] = None,
    template: str = "{owner}/{doc_type}/",
    is_unsorted: bool = False,
    mode: str = "copy",
    allow_duplicates: Optional[bool] = None,
) -> Path:
    """
    Safely routes a source file to destination hierarchy with collision avoidance.
    Supports 'copy' (safe default) and 'move'.

    allow_duplicates:
      - True  -> append _1, _2 ... when the name is already taken (legacy).
      - False -> delete the existing copy (and its _1, _2 variants) first,
                then place the new file under its original name.
      - None  -> read the global "Allow duplicates" setting.
    """
    source_file = Path(source_file)
    destination_root = Path(destination_root)
    if allow_duplicates is None:
        allow_duplicates = load_settings().allow_duplicates
    clean_owner = sanitize_path_component(owner)
    folder_name = sanitize_path_component(target_folder or doc_type)

    if is_unsorted or doc_type.lower() == "unsorted":
        target_dir = destination_root / "Unsorted"
        if clean_owner.lower() != "general":
            target_dir = target_dir / clean_owner
    else:
        # Build relative folder using template
        rel_path_str = template.replace("{owner}", clean_owner).replace("{doc_type}", folder_name)
        if clean_owner.lower() == "general":
            rel_path_str = rel_path_str.replace(clean_owner, "")
        # Clean relative path parts
        raw = [p for p in Path(rel_path_str).parts if p.strip("\\/")]
        parts = [sanitize_path_component(p) for p in raw]
        target_dir = destination_root.joinpath(*parts)

    target_dir.mkdir(parents=True, exist_ok=True)

    if allow_duplicates:
        final_dest_path = get_unique_destination_path(target_dir, source_file.name)
    else:
        purge_existing_copies(target_dir, source_file.name, keep_path=source_file)
        final_dest_path = target_dir / source_file.name

    # The file already sits at its final destination (e.g. reclassify into the
    # same folder) — nothing to copy or move.
    try:
        if final_dest_path.exists() and final_dest_path.resolve() == source_file.resolve():
            return final_dest_path
    except OSError:
        pass

    if mode.lower() == "move":
        shutil.move(str(source_file), str(final_dest_path))
    else:
        shutil.copy2(str(source_file), str(final_dest_path))

    return final_dest_path
