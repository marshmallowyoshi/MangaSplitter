import re
import os
import zipfile
import shutil
import logging

def main():
    pass

if __name__ == '__main__':
    main()

MANGA_DIR = 'manga'
CBZ = True
VOLUME_RE = re.compile(r'.*\.cb[zr]')
CHAPTER_RE = re.compile(r'c(\d*)')
log = logging.getLogger(__name__)

manga_list = [x for x in os.listdir(MANGA_DIR) if re.match(VOLUME_RE, x)]

for manga in manga_list:
    with zipfile.ZipFile(os.path.join(MANGA_DIR, manga), 'r') as manga_zip:
        extract_dir = ''.join((MANGA_DIR, '/', manga[:-4]))
        if not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        manga_zip.extractall(extract_dir)
    
    files = [os.path.join(extract_dir, x) for x in os.listdir(extract_dir)]

    pages = []
    original_chapters = []

    for file in files:
        if os.path.isdir(file):
            original_chapters.append(file)
        else:
            pages.append(file)
    
    if len(pages) != 0:
        chapters = {}
        for page in pages:
            page_chapter = re.search(CHAPTER_RE, page).group(1)
            if page_chapter not in chapters:
                if not os.path.isdir(os.path.join(extract_dir, page_chapter)):
                    os.mkdir(os.path.join(extract_dir, page_chapter))
                chapters[page_chapter] = []
            shutil.move(page, os.path.join(extract_dir, page_chapter))
            chapters[page_chapter].append(page)
    else:
        print('No loose pages found in ', manga)
    if len(original_chapters) != 0:
        print('Found ', len(chapters), ' already organised chapters in ', manga)

    if CBZ:
        for chapter in chapters:
            shutil.make_archive(os.path.join(extract_dir, chapter), 'zip', os.path.join(extract_dir, chapter), chapter)
    
    print('Finished processing ', manga)