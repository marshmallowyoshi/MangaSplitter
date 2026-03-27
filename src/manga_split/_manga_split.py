"""Manga Splitter main module."""

import asyncio
import logging
import os
import re
import shutil
import timeit
import zipfile
from argparse import ArgumentParser, Namespace
from pathlib import Path

VOLUME_RE = re.compile(r".*\.cb[zr]")
CHAPTER_RE = re.compile(r"c(\d+)")  # Default regex pattern


def main():
    """Main entrypoint for manga splitter CLI."""
    logger = logging.getLogger("manga_split")
    logger.addHandler(logging.StreamHandler())
    parser = ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input manga directory",
        metavar="path",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-c", "--compress", help="Compress manga", action="store_true"
    )
    parser.add_argument(
        "-r",
        "--regex",
        help="Specify alternative regex pattern for chapter number",
        metavar="regex",
        required=False,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Verbose output (includes time taken measurement)",
        action="store_true",
    )
    args = parser.parse_args()
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        time_taken = timeit.timeit(
            lambda: _parse_args_to_run_manga_split(args), number=1
        )
        logger.info("Time taken: %.2f seconds", time_taken)
    else:
        _parse_args_to_run_manga_split(args)


async def _run_manga_split_async(
    manga_dir: Path, cbz: bool, chapter_re: re.Pattern
) -> None:
    """Async layer of manga splitter main function."""
    manga_list = [
        manga_dir / x for x in os.listdir(manga_dir) if VOLUME_RE.match(x)
    ]
    if not manga_list:
        logging.getLogger("manga_split").warning(
            "No manga files ('*.cbz' or '*.cbr') found in %s", manga_dir
        )
        return
    split_coroutines = [
        split_manga(manga, manga_dir, cbz, chapter_re) for manga in manga_list
    ]
    await asyncio.gather(*split_coroutines)


def run_manga_split(
    manga_dir: Path, cbz: bool = False, chapter_re: re.Pattern = CHAPTER_RE
) -> None:
    """
    Splits the manga in the given directory into chapters.

    Args:
        manga_dir (Path): Path to the manga directory.
        cbz (bool): Whether to compress chapters into CBZ files.
        chapter_re (re.Pattern): Compiled regex pattern to identify
            chapter numbers.
    """
    asyncio.run(_run_manga_split_async(manga_dir, cbz, chapter_re))


def _parse_args_to_run_manga_split(args: Namespace) -> None:
    """Convert command line arguments to python objects."""
    manga_dir: Path = args.input
    cbz: bool = args.compress
    if args.regex:
        try:
            chapter_re = re.compile(args.regex)
        except re.error as e:
            logging.getLogger("manga_split").error(
                "Invalid regex pattern provided: %s", e
            )
            return None
    else:
        chapter_re = CHAPTER_RE

    return run_manga_split(manga_dir, cbz, chapter_re)


async def split_manga(
    manga: Path, manga_dir: Path, cbz: bool, chapter_re: re.Pattern
) -> Path:
    """Split a single manga volume into chapters.

    Args:
        manga (Path): Path to the manga ZIP file.
        manga_dir (Path): Directory where the manga is located.
        cbz (bool): Whether to compress chapters into CBZ files.
        chapter_re (re.Pattern): Compiled regex pattern to identify
            chapter numbers.

    Returns:
        Path: The path to the extracted manga directory.
    """

    extract_dir = manga_dir / manga.stem

    # Extract ZIP in a thread
    await asyncio.to_thread(extract_zip, manga, extract_dir)

    # Process files and folders
    files = await asyncio.to_thread(folders_split, extract_dir)

    # Organize chapters in a thread
    new_chapters = await organise_chapters(files, extract_dir, chapter_re)

    if cbz:
        # Compress all chapters concurrently
        compress_tasks = [
            asyncio.to_thread(compress_chapter, ch, extract_dir, manga_dir)
            for ch in new_chapters
        ]
        await asyncio.gather(*compress_tasks)
        # Remove directory in a thread
        await asyncio.to_thread(shutil.rmtree, extract_dir)

    logging.getLogger("manga_split").info("Finished processing %s", manga)
    return extract_dir


def safe_extract_zip(zip_file: zipfile.ZipFile, extract_dir: Path) -> None:
    """Safely extract zip file contents to extract_dir,
    preventing path traversal."""
    for member in zip_file.namelist():
        member_path = extract_dir / member
        # Resolve the absolute path and ensure it's within extract_dir
        abs_extract_dir = extract_dir.resolve()
        abs_member_path = member_path.resolve()
        if not str(abs_member_path).startswith(str(abs_extract_dir)):
            raise RuntimeError(
                f"Attempted Path Traversal in Zip File: {member}"
            )
        zip_file.extract(member, extract_dir)


def extract_zip(zip_path: Path, extract_dir: Path) -> None:
    """Extract a zipfile (`.cbz` or `.cbr`) to a target directory."""
    with zipfile.ZipFile(zip_path, "r") as manga_zip:
        os.makedirs(extract_dir, exist_ok=True)
        safe_extract_zip(manga_zip, extract_dir)


def folders_split(directory: Path) -> list[Path]:
    """Synchronously split into files."""
    files: list[Path] = []
    for dirpath, dirnames, filenames in directory.walk():
        if dirnames:
            logging.getLogger("manga_split").warning(
                "Found unexpected subfolders in %s: %s", dirpath, dirnames
            )
        for filename in filenames:
            files.append(dirpath / filename)
    return files


async def organise_chapters(
    files: list[Path], extract_dir: Path, chapter_re: re.Pattern
) -> dict[str, list[Path]]:
    """Organize chapters using threads for I/O."""
    chapters: dict[str, list[Path]] = {}
    for page in files:
        match = chapter_re.search(os.path.relpath(page, extract_dir))
        if not match:
            logging.getLogger("manga_split").warning(
                "No chapter found in page %s", page
            )
            continue
        page_chapter = match.group(1)
        chapter_dir = extract_dir / page_chapter
        await asyncio.to_thread(os.makedirs, chapter_dir, exist_ok=True)
        # Move file
        dest = chapter_dir / page.name
        await asyncio.to_thread(shutil.move, page, dest)
        chapters.setdefault(page_chapter, []).append(dest)
    return chapters


def compress_chapter(
    chapter_num: str, extract_dir: Path, manga_dir: Path
) -> None:
    """Synchronous compression."""
    chapter_path = extract_dir / chapter_num
    output_dir = manga_dir
    os.makedirs(output_dir, exist_ok=True)
    cbz_path = output_dir / f"{extract_dir.name} ch{chapter_num}.cbz"
    with zipfile.ZipFile(cbz_path, "w") as zf:
        for file in chapter_path.iterdir():
            zf.write(
                file, arcname=file.name, compress_type=zipfile.ZIP_DEFLATED
            )
