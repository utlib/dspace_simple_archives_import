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

## Usage
### Input
1. A directory of zip files with PDF, metadata of format corresponding to the scripts.
2. Put all zip files into the "deposit" directory. By default this directory resides in the root directory of the cloned Git repository.

## Server requirements
* Python 2.7
* Pip
* BeautifulSoup4
* Python XML parser

## Usage
* Run dspace\_dsa\_maker.py. This will make the deposit directory.
* Place all zip files into the made deposit directory.
* Run dspace\_dsa\_maker.py again. This will make DSAs into ingest directory.
* Edit dspace_dsa_ingest.py with the info of your DSpace instance.
* Run dspace_dsa_ingest.py

## Author
University of Toronto Libraries (<tspace@library.utoronto.ca>)

## License
This project is licensed under the terms of the GNU GPLv3 license.

