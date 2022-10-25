<!-- PROJECT LOGO -->
<br/>
<p align="center">
  <a href="https://github.com/InBinaryWorld/DuplicateRemover">
    <img src="images/Duplicate_Remover.png" alt="Logo" width="500" height="500">
  </a>
</p>
<div align="center">

[![License][license-shield]][license-url]
![Top language][top-language-shield]
![Phyton version][python-shield]
![Contributors][contributors-shield]
![Last commit][last-commit-shield]
[![LinkedIn][linkedin-shield]][linkedin-url]

</div>
<h3 align="center">Duplicate Remover</h3>
<p align="center">
  Store files and photos without duplicates,
  <br>
  take care of disk space and save your time.
  <br/>
  <a href="https://github.com/InBinaryWorld/DuplicateRemover"><strong>Explore the docs »</strong></a>
  <br/>
  <br/>
  <a href="https://github.com/InBinaryWorld/DuplicateRemover/issues">Report Bug</a>
  ·
  <a href="https://github.com/InBinaryWorld/DuplicateRemover/issues">Request Feature</a>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
    * [How it started?](#how-it-started)
    * [Built With](#built-with)
* [Getting Started](#getting-started)
    * [Installation](#installation)
* [Usage](#usage)
    * [Remove duplicates](#remove-duplicates)
    * [Analyse and leave only new](#analyse-and-leave-only-new)
    * [Make flat dir](#make-flat-dir)
* [Roadmap](#roadmap)
* [License](#license)
* [Contact](#contact)

<!-- ABOUT THE PROJECT -->
## About The Project

All IT specialists know that people are divided into those who 
make backups and those who will do them. 

But backing up data not always is an easy process especially 
if you care about their quality, and you don't have unlimited 
space on your backup drives.

### How it started?

Making periodic backups of photos (and not only) from phone 
without cleaning memory (just moving DCIM directory to the 
backup disk) leads to storing multiple copies of the same images. 
The problem grows even when each family member wants to store
their data in one place with you. Your family shares images with 
each other and the copies again end up on backup disks.

Over time, a mess appears on the disk, you don't know what you can delete,
what not, how many copies of the same files you have, and you don't know 
how to find something usable. So you start merging all folders and manually 
browsing content to make some disk space and make files organized. But after 
an hour you realized that browsing thousands of files manually to remove 
duplicates seems impossible.

So I thought: "Why I waste my time doing it manually. Let's automate this process!"

And.... Here it is! Duplicate Remover improved with some useful functionalities!

### Built With

Project was created with pure python using only included modules.

* [hashlib](https://docs.python.org/3/library/hashlib.html?highlight=hashlib#module-hashlib)
* [filecmp](https://docs.python.org/3/library/filecmp.html?highlight=filecmp#module-filecmp)
* [tempfile](https://docs.python.org/3/library/tempfile.html)

<!-- GETTING STARTED -->

## Getting Started

Getting started with this tool is extremely easy, so enjoy!

To use this tool, you first need to get:

* [Python][python-download-url] in version 3.8 or newer.

### Installation

1. Clone the repo.

```sh
git clone https://github.com/InBinaryWorld/DuplicateRemover.git
```

2. Go for it! 

```sh
python ./DuplicateRemover/duplicate_remover.py
```

<!-- USAGE EXAMPLES -->
## Usage

This script will allow you to keep your data clean. 
Described bellow functionalities may intertwine in 
different scenarios to give the user the best 
impression. At end of process, the user can check 
the statistics of the performed operation.

### Remove duplicates

This tool allows you to clear your data from copies even if
file names are different. It looks deep in provided directory 
and looking for duplicate also in subdirectories.

NOTE: To improve performance and memory usage, MD5 hashes are 
used to find similar files.

NOTE: MD5 hashes don't guarantee that files are also the 
same, so before each remove action binary comparisons
of files with the same hashes are performed. That makes 
the tool safe.

### Analyse and leave only new

Script ask fot two directories and remove files from only 
one of them. It analyzes one directory and then remove
duplicated files from the other one.

It's especially useful when performing new backups and having
already backup data. This functionality allows you to analyze 
the current state of the backup and based on this clear the 
new data directory before it will be appended.

### Rename files

Support Tool - Useful when the user expects to standardize filenames.
The user is prompted for the preferred prefix (ex, "IMG"), to which 
a suffix based on the last modified date will be added.

Example output file name: IMG_2021-09-25_13_19_32.jpg

NOTE: It supports files with the same last modification date by adding 
additional sequential number.

### Make flat dir

Moves all files to root directory using Rename functionality.

<!-- ROADMAP -->
## Roadmap

See the [issues panel][project-issue-url] for a list of 
proposed features.

Waiting for better times:

* Live photo cleaner - Getting Apple Live Photos on the computer 
it creates two files (JPG and MOV). Sometimes it gets annoying 
when they're mixed with real movies causing a mess. The target is 
to remove .MOV files if found image with a corresponding name and 
.JPG extension.

* Support to perform backups easily. Copy and removes files in 
the destination directory to make a perfect copy of a source 
without removing and copying all data to save disk life and 
user time (Master-Slave model).

<!-- LICENSE -->
## License

Distributed under the [MIT License][license-url]. See `LICENSE`  for more information.


<!-- CONTACT -->
## Contact

Find me on:

[![LinkedIn][linkedin-shield]][linkedin-url]
[![Github][github-user-shield]][github-user-url]

<!-- MARKDOWN LINKS & IMAGES -->
[license-shield]: https://img.shields.io/github/license/InBinaryWorld/DuplicateRemover
[license-url]: https://github.com/InBinaryWord/DuplicateRemover/blob/master/LICENSE.txt
[top-language-shield]: https://img.shields.io/github/languages/top/InBinaryWorld/DuplicateRemover
[python-shield]: https://img.shields.io/github/pipenv/locked/python-version/InBinaryWorld/DuplicateRemover
[contributors-shield]: https://img.shields.io/github/contributors/InBinaryWorld/DuplicateRemover
[contributors-url]: https://github.com/InBinaryWord/DuplicateRemover/graphs/contributors
[last-commit-shield]:https://img.shields.io/github/last-commit/InBinaryWorld/DuplicateRemover
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=flat-square&logo=linkedin&color=175a7a
[linkedin-url]: https://linkedin.com/in/Krzysztof-Szafraniak
[github-user-shield]: https://img.shields.io/badge/-GitHub-black.svg?style=flat-square&logo=github&color=171515
[github-user-url]: https://github.com/InBinaryWorld
[python-download-url]: https://www.python.org/downloads
[project-url]: https://github.com/InBinaryWorld/DuplicateRemover
[project-issue-url]: https://github.com/InBinaryWorld/DuplicateRemover/issues

[img-logo]: images/Duplicate_Remover.png
