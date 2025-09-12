"""Safe ZIP extraction utilities to prevent zip-slip attacks."""

import zipfile
from pathlib import Path


def safe_extract(
    zip_path: Path,
    dest_dir: Path,
    max_members: int = 5000,
    max_total_bytes: int = 300 * 1024 * 1024,
):
    """Safely extract a ZIP file with security checks.

    Args:
        zip_path: Path to the ZIP file to extract
        dest_dir: Destination directory for extraction
        max_members: Maximum number of files allowed in the ZIP
        max_total_bytes: Maximum total size of extracted content

    Raises:
        ValueError: If ZIP contains too many files, is too large, or contains illegal paths
    """
    dest_dir = dest_dir.resolve()

    with zipfile.ZipFile(zip_path) as z:
        infos = z.infolist()

        # Check file count
        if len(infos) > max_members:
            raise ValueError(f"ZIP has too many files ({len(infos)} > {max_members})")

        # Check total size and validate paths
        total = 0
        for info in infos:
            total += info.file_size
            if total > max_total_bytes:
                raise ValueError(
                    f"ZIP contents too large ({total} > {max_total_bytes} bytes)"
                )

            # Prevent zip-slip attacks
            target = (dest_dir / info.filename).resolve()
            if not str(target).startswith(str(dest_dir)):
                raise ValueError(f"Illegal path in ZIP entry: {info.filename}")

        # Safe to extract
        z.extractall(dest_dir)
