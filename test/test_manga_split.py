# pylint: disable=redefined-outer-name,missing-docstring
import logging
import pathlib
import zipfile
from typing import Callable

import pytest

import manga_split
from manga_split._manga_split import folders_split, main

# factories have function scope to give
# unique folder per test


@pytest.fixture(scope="function")
def mock_manga_page_factory(
    tmp_path: pathlib.Path,
) -> Callable[[str], pathlib.Path]:
    def _factory(filename: str) -> pathlib.Path:
        page = tmp_path / filename
        if not page.parent.exists():
            page.parent.mkdir(parents=True, exist_ok=True)
        page.touch()
        return page

    return _factory


@pytest.fixture(scope="function")
def mock_manga_zip_factory(
    tmp_path: pathlib.Path,
    mock_manga_page_factory: Callable[[str], pathlib.Path],
) -> Callable[[str, list[str]], pathlib.Path]:

    def _factory(zip_name: str, page_names: list[str]) -> pathlib.Path:
        zip_path = tmp_path / zip_name
        with zipfile.ZipFile(zip_path, "w") as manga_zip:
            for page_name in page_names:
                page = mock_manga_page_factory(page_name)
                manga_zip.write(page, arcname=page.name)
                page.unlink()  # Remove the original file after adding to zip
        return zip_path

    return _factory


@pytest.fixture
def mock_multiple_chapter_manga_volume(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
) -> pathlib.Path:
    return mock_manga_zip_factory(
        "multi_chapter_manga.cbz",
        [
            "c001_page1.jpg",
            "c001_page2.jpg",
            "c002_page1.jpg",
            "c002_page2.jpg",
        ],
    )


@pytest.fixture
def mock_single_chapter_manga_volume(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
) -> pathlib.Path:
    return mock_manga_zip_factory(
        "single_chapter_manga.cbz",
        [
            "c001_page1.jpg",
            "c001_page2.jpg",
        ],
    )


@pytest.fixture
def mock_manga_no_matching_chapter_volume(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
) -> pathlib.Path:
    return mock_manga_zip_factory(
        "no_matching_chapter_manga.cbz",
        [
            "page1.jpg",
            "page2.jpg",
        ],
    )


@pytest.fixture
def mock_manga_subfolders(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
) -> pathlib.Path:
    return mock_manga_zip_factory(
        "subfolder_manga.cbz",
        [
            "c001/c001_page1.jpg",
            "c001/c001_page2.jpg",
            "c002/c002_page1.jpg",
            "c002/c002_page2.jpg",
        ],
    )


@pytest.fixture
def mock_multiple_manga_volumes(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
) -> list[pathlib.Path]:
    manga1 = mock_manga_zip_factory(
        "manga1.cbz",
        [
            "c001_page1.jpg",
            "c001_page2.jpg",
            "c002_page1.jpg",
            "c002_page2.jpg",
        ],
    )
    manga2 = mock_manga_zip_factory(
        "manga2.cbz",
        [
            "c003_page1.jpg",
            "c003_page2.jpg",
            "c003_page3.jpg",
        ],
    )
    return [manga1, manga2]


def test_create_zip(
    mock_manga_zip_factory: Callable[[str, list[str]], pathlib.Path],
):
    zip_path = mock_manga_zip_factory(
        "test_manga.cbz", ["page1.jpg", "page2.jpg"]
    )
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path, "r") as manga_zip:
        namelist = manga_zip.namelist()
        assert "page1.jpg" in namelist
        assert "page2.jpg" in namelist


def test_split_manga_single_chapter_volume(
    mock_single_chapter_manga_volume: pathlib.Path,
):
    manga_dir = mock_single_chapter_manga_volume.parent
    manga_split.run_manga_split(manga_dir, cbz=True)
    expected_output_file = manga_dir / "single_chapter_manga ch001.cbz"
    assert expected_output_file.exists(), (
        f"{expected_output_file} does not exist."
        f" Existing files: {list(manga_dir.iterdir())}"
    )


def test_split_manga_single_volume(
    mock_multiple_chapter_manga_volume: pathlib.Path,
):
    manga_dir = mock_multiple_chapter_manga_volume.parent
    manga_split.run_manga_split(manga_dir, cbz=True)
    expected_output_files = [
        manga_dir / "multi_chapter_manga ch001.cbz",
        manga_dir / "multi_chapter_manga ch002.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )


def test_plit_manga_no_compression(
    mock_multiple_chapter_manga_volume: pathlib.Path,
):
    manga_dir = mock_multiple_chapter_manga_volume.parent
    manga_split.run_manga_split(manga_dir, cbz=False)
    expected_output_dirs = [
        manga_dir / "multi_chapter_manga" / "001",
        manga_dir / "multi_chapter_manga" / "002",
    ]
    for output_dir in expected_output_dirs:
        assert output_dir.exists() and output_dir.is_dir(), (
            f"{output_dir} does not exist or is not a directory."
            f" Existing files: {list(manga_dir.rglob('*'))}"
        )
        assert len(list(output_dir.iterdir())) == 2, (
            f"Expected 2 files in {output_dir},"
            f" found {len(list(output_dir.iterdir()))}.)"
        )


def test_split_manga_no_matching_chapter(
    mock_manga_no_matching_chapter_volume: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
):
    manga_dir = mock_manga_no_matching_chapter_volume.parent
    with caplog.at_level(logging.WARNING, logger="manga_split"):
        manga_split.run_manga_split(manga_dir, cbz=True)
    assert any(
        "No chapter found in page" in record.message
        for record in caplog.records
    ), "Expected warning about no matching chapters not found."
    # No output files should be created
    output_files = list(manga_dir.glob("no_matching_chapter_manga *.cbz"))
    assert (
        len(output_files) == 0
    ), f"Expected no output files, but found: {output_files}"


def test_split_manga_subfolders(
    mock_manga_subfolders: pathlib.Path,
):
    manga_dir = mock_manga_subfolders.parent
    manga_split.run_manga_split(manga_dir, cbz=True)
    expected_output_files = [
        manga_dir / "subfolder_manga ch001.cbz",
        manga_dir / "subfolder_manga ch002.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )


def test_split_multiple_manga_volumes(
    mock_multiple_manga_volumes: list[pathlib.Path],
):
    manga_dir = mock_multiple_manga_volumes[0].parent
    manga_split.run_manga_split(manga_dir, cbz=True)
    expected_output_files = [
        manga_dir / "manga1 ch001.cbz",
        manga_dir / "manga1 ch002.cbz",
        manga_dir / "manga2 ch003.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )


def test_mock_commandline(
    mock_multiple_chapter_manga_volume: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    manga_dir = mock_multiple_chapter_manga_volume.parent

    # Mock command-line arguments
    monkeypatch.setattr(
        "sys.argv",
        [
            "manga_split",  # script name
            "-i",
            str(manga_dir),
            "-c",
        ],
    )
    main()
    expected_output_files = [
        manga_dir / "multi_chapter_manga ch001.cbz",
        manga_dir / "multi_chapter_manga ch002.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )


def test_mock_commandline_verbose(
    mock_multiple_chapter_manga_volume: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
):
    manga_dir = mock_multiple_chapter_manga_volume.parent

    # Mock command-line arguments
    monkeypatch.setattr(
        "sys.argv",
        [
            "manga_split",  # script name
            "-i",
            str(manga_dir),
            "-c",
            "-v",
        ],
    )
    with caplog.at_level(logging.INFO, logger="manga_split"):
        main()
    expected_output_files = [
        manga_dir / "multi_chapter_manga ch001.cbz",
        manga_dir / "multi_chapter_manga ch002.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )
    # Check for info log about finishing processing
    assert any(
        "Time taken:" in record.message for record in caplog.records
    ), "Expected info log about time taken not found."


def test_mock_commandline_custom_regex(
    mock_multiple_chapter_manga_volume: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    manga_dir = mock_multiple_chapter_manga_volume.parent

    # Mock command-line arguments with custom regex
    monkeypatch.setattr(
        "sys.argv",
        [
            "manga_split",  # script name
            "-i",
            str(manga_dir),
            "-c",
            "-r",
            r"c(\d+)",  # same as default but testing custom regex handling
        ],
    )
    main()
    expected_output_files = [
        manga_dir / "multi_chapter_manga ch001.cbz",
        manga_dir / "multi_chapter_manga ch002.cbz",
    ]
    for output_file in expected_output_files:
        assert output_file.exists(), (
            f"{output_file} does not exist."
            f" Existing files: {list(manga_dir.iterdir())}"
        )


def test_folders_split_unexpected_subfolder(
    tmp_path: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
):
    # Create a mock directory structure with unexpected subfolder
    manga_dir = tmp_path / "manga"
    manga_dir.mkdir()
    subfolder = manga_dir / "unexpected_folder"
    subfolder.mkdir()
    (subfolder / "c001_page1.jpg").touch()

    with caplog.at_level(logging.WARNING, logger="manga_split"):
        folders_split(manga_dir)

    assert any(
        "Found unexpected subfolders" in record.message
        for record in caplog.records
    ), "Expected warning about unexpected subfolders not found."
