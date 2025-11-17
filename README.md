Split cbz format volumes into individual chapters for easier progress tracking in manga reading apps.

Requires python, uses only standard library so no extra packages required.

# INSTALLATION:

## Method 1: Using pip (recommended)
`pip install manga-split`

## Method 2: From source
1. Clone repository  
   `git clone <repository-url>`
2. Navigate to project directory
   `cd MangaSplitter`
3. Install package
   `pip install .`

# DEVELOPMENT SETUP:
1. Clone repository  
   `git clone <repository-url>`
2. Navigate to project directory
   `cd MangaSplitter`
3. (Optional) Create and activate virtual environment
   `python -m venv .venv`
   `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (MacOS/Linux)
4. Install package
    `pip install -e .`

# USAGE:

*manga_split -i \<path\> -c*

*-i \<path\>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;relative path to directory containing volume cbz files  
*-c*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;include to compress chapters to cbz files after processing  
*-r \<regex pattern\>*&nbsp;&nbsp;&nbsp;custom regex for different naming conventions. Regex should match chapter number to first group (try "(\d{3})" if it fails on the default)
