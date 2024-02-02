import re
import os
import zipfile
import shutil
from argparse import ArgumentParser

VOLUME_RE = re.compile(r'.*\.cb[zr]')
CHAPTER_RE = re.compile(r'c(\d*)')

def main():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', help='Input manga directory', metavar='path', required=True)
    parser.add_argument('-c', '--compress', help='Compress manga', default=False, metavar='True/False', required=False)
    args = parser.parse_args()
    manga_dir = args.input
    if args.compress == 'True':
        cbz = True
    else:
        cbz = False
        
    manga_list = [x for x in os.listdir(manga_dir) if re.match(VOLUME_RE, x)]
    for manga in manga_list:
        split_manga(manga, manga_dir, cbz)

def split_manga(manga, manga_dir, cbz=bool):
    with zipfile.ZipFile(os.path.join(manga_dir, manga), 'r') as manga_zip:
        extract_dir = os.path.join(manga_dir, manga[:-4])
        if not os.path.isdir(extract_dir):
            os.mkdir(extract_dir)
        manga_zip.extractall(extract_dir)
    
    directory_list = [os.path.join(extract_dir, x) for x in os.listdir(extract_dir)]
    
    pages, _ = folders_split(directory_list)

    new_chapters = organise_chapters(pages, extract_dir)

    if cbz:
        for chapter, _ in new_chapters.items():
            compress_chapter(chapter, extract_dir, manga_dir)
        shutil.rmtree(extract_dir)

    print('Finished processing ', manga)

    return extract_dir

def folders_split(directory):
    files = []
    folders = []
    for item in directory:
        if os.path.isdir(item):
            folders.append(item)
        else:
            files.append(item)
    return files, folders

def organise_chapters(files, extract_dir):
    if len(files) != 0:
        chapters = {}
        for page in files:
            page_chapter = re.search(CHAPTER_RE, os.path.basename(page)).group(1)
            if page_chapter not in chapters:
                if not os.path.isdir(os.path.join(extract_dir, page_chapter)):
                    os.mkdir(os.path.join(extract_dir, page_chapter))
                    chapters[page_chapter] = []
            shutil.move(page, os.path.join(extract_dir, page_chapter))
            chapters[page_chapter].append(page)
    else:
        print('No pages found')

    return chapters

def compress_chapter(chapter_num, extract_dir, manga_dir):
    compress_paths = [os.path.join(extract_dir, chapter_num, x) for x in os.listdir(os.path.join(extract_dir, chapter_num))]
    compress_names = [x for x in os.listdir(os.path.join(extract_dir, chapter_num))]
    if not os.path.isdir(os.path.join(manga_dir, os.path.basename(manga_dir))):
        os.mkdir(os.path.join(manga_dir, os.path.basename(manga_dir)))
    with zipfile.ZipFile(os.path.join(manga_dir, os.path.basename(manga_dir), os.path.basename(extract_dir) + ' ch. ' + chapter_num + '.cbz'), 'w') as chapter_zip:
        for idx, path in enumerate(compress_paths):
            chapter_zip.write(path, compress_names[idx], compress_type=zipfile.ZIP_DEFLATED)

if __name__ == '__main__':
    main()