import asyncio
import re
import os
import zipfile
import shutil
from argparse import ArgumentParser

VOLUME_RE = re.compile(r'.*\.cb[zr]')

async def main():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', help='Input manga directory', metavar='path', required=True, type=os.path.abspath)
    parser.add_argument('-c', '--compress', help='Compress manga', action='store_true')
    parser.add_argument('-r', '--regex', help='Specify alternative regex pattern for chapter number', metavar='regex', required=False)
    args = parser.parse_args()
    manga_dir = args.input
    cbz = args.compress
    
    # Compile regex once
    if args.regex:
        chapter_re = re.compile(args.regex)
    else:
        chapter_re = re.compile(r'c(\d+)')  # Pre-compile default regex

    manga_list = [x for x in os.listdir(manga_dir) if VOLUME_RE.match(x)]
    cors = [split_manga(manga, manga_dir, cbz, chapter_re) for manga in manga_list]
    await asyncio.gather(*cors)

async def split_manga(manga, manga_dir, cbz: bool, chapter_re):
    zip_path = os.path.join(manga_dir, manga)
    extract_dir = os.path.join(manga_dir, manga[:-4])
    
    # Extract ZIP in a thread
    await asyncio.to_thread(extract_zip, zip_path, extract_dir)
    
    # Process files and folders
    directory_list = await asyncio.to_thread(lambda: [os.path.join(extract_dir, x) for x in os.listdir(extract_dir)])
    files, _ = await asyncio.to_thread(folders_split, directory_list)
    
    # Organize chapters in a thread
    new_chapters = await organise_chapters(files, extract_dir, chapter_re)
    
    if cbz:
        # Compress all chapters concurrently
        compress_tasks = [asyncio.to_thread(compress_chapter, ch, extract_dir, manga_dir) for ch in new_chapters]
        await asyncio.gather(*compress_tasks)
        # Remove directory in a thread
        await asyncio.to_thread(shutil.rmtree, extract_dir)
    
    print('Finished processing', manga)
    return extract_dir

def extract_zip(zip_path, extract_dir):
    """Synchronous function to extract ZIP."""
    with zipfile.ZipFile(zip_path, 'r') as manga_zip:
        os.makedirs(extract_dir, exist_ok=True)
        manga_zip.extractall(extract_dir)

def folders_split(directory):
    """Synchronously split into files and folders."""
    files = []
    folders = []
    for item in directory:
        (folders if os.path.isdir(item) else files).append(item)
    return files, folders

async def organise_chapters(files, extract_dir, chapter_re):
    """Organize chapters using threads for I/O."""
    chapters = {}
    for page in files:
        match = chapter_re.search(os.path.basename(page))
        if not match:
            print(f'No chapter found in {page}')
            continue
        page_chapter = match.group(1)
        chapter_dir = os.path.join(extract_dir, page_chapter)
        # Create dir if needed
        if not await asyncio.to_thread(os.path.exists, chapter_dir):
            await asyncio.to_thread(os.makedirs, chapter_dir, exist_ok=True)
        # Move file
        dest = os.path.join(chapter_dir, os.path.basename(page))
        await asyncio.to_thread(shutil.move, page, dest)
        chapters.setdefault(page_chapter, []).append(page)
    return chapters

def compress_chapter(chapter_num, extract_dir, manga_dir):
    """Synchronous compression."""
    chapter_path = os.path.join(extract_dir, chapter_num)
    output_dir = os.path.join(manga_dir, os.path.basename(manga_dir))
    os.makedirs(output_dir, exist_ok=True)
    cbz_path = os.path.join(output_dir, f'{os.path.basename(extract_dir)} ch.{chapter_num}.cbz')
    with zipfile.ZipFile(cbz_path, 'w') as zf:
        for file in os.listdir(chapter_path):
            file_path = os.path.join(chapter_path, file)
            zf.write(file_path, arcname=file, compress_type=zipfile.ZIP_DEFLATED)

if __name__ == '__main__':
    asyncio.run(main())