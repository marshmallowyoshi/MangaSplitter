Split cbz format volumes into individual chapters for easier progress tracking in manga reading apps.

Requires python, uses only standard library so no extra packages required.


# USAGE:

*manga_split -i \<path\> -c*

*-i \<path\>*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;relative path to directory containing volume cbz files  
*-c*&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;include to compress chapters to cbz files after processing  
*-r \<regex pattern\>*&nbsp;&nbsp;&nbsp;custom regex for different naming conventions. Regex should match chapter number to first group (try "(\d{3})" if it fails on the default)
