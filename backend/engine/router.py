import os
import re
import shutil
from pathlib import Path
from typing import Optional

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

def route_file(
    source_file: Path,
    destination_root: Path,
    owner: str,
    doc_type: str,
    target_folder: Optional[str] = None,
    template: str = "{owner}/{doc_type}/",
    is_unsorted: bool = False,
    mode: str = "copy"
) -> Path:
    """
    Safely routes a source file to destination hierarchy with collision avoidance.
    Supports 'copy' (safe default) and 'move'.
    """
    source_file = Path(source_file)
    destination_root = Path(destination_root)
    clean_owner = sanitize_path_component(owner)
    folder_name = sanitize_path_component(target_folder or doc_type)

    if is_unsorted or doc_type.lower() == "unsorted":
        target_dir = destination_root / "Unsorted" / clean_owner
    else:
        # Build relative folder using template
        rel_path_str = template.replace("{owner}", clean_owner).replace("{doc_type}", folder_name)
        # Clean relative path parts
        parts = [sanitize_path_component(p) for p in Path(rel_path_str).parts if p.strip()]
        target_dir = destination_root.joinpath(*parts)

    target_dir.mkdir(parents=True, exist_ok=True)
    final_dest_path = get_unique_destination_path(target_dir, source_file.name)

    if mode.lower() == "move":
        shutil.move(str(source_file), str(final_dest_path))
    else:
        shutil.copy2(str(source_file), str(final_dest_path))

    return final_dest_path
