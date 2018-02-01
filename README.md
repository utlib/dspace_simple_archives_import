# DSpace DSA Maker
## Intro
This script combo extracts article zip files that are transferred unto a server, crosswalks their metadata, prepares DSpace Simple Archive and ingest each article into DSpace.
The scripts should be accessible to the server where zip files are being received, as well as the server where DSpace import can be accessed.
The article zip files currently supported is PubMed Central.

## Details
There are two scripts: DSpace DSA Maker and DSpace DSA Ingest.
You must run DSA Maker first.
The DSA Maker does the following:
1. Unzips all zip files in deposit directory
2. Crosswalks all XMLs into Dublin Core for DSpace
3. Package all bitstreams and Dublin Core into individual directories and writes the contents file

The DSA Ingest does the following:
1. Invoke DSpace master script for DSpace import
2. Moves original zip files and DSAs into archives directories.
3. Writes emails and reports

## Server requirements
* Python 2
* Pip
* BeautifulSoup4
* Python XML parser

## Installation
### Mac
1. Install Python 2.7
2. pip install BeautifulSoup4
3. pip install lxml

### Linux
TODO

## License
This project is licensed under the terms of the GNU GPLv3 license.
