# DSpace Simple Archives Importer

DSpace Simple Archives Importer is an utility that facilitates the importing of exported archive files into DSpace.
This utility extracts, crosswalks metadata, makes DSpace Simple Archives and invokes DSpace script to import.
This utility can be set up to run periodically to watch for new deposits and import as soon as possible.

## System requirements

* Python 2.7
* Pip
* BeautifulSoup4
* Python XML parser

## Installation

1. Clone the repository on the server running DSpace, or a space accessible by DSpace.
2. Run `scripts/dspace\_dsa\_maker.py`  
The maker script will initiate working directories.
The location of each working directory is specified in the two python scripts. The values can be adjusted as needed.

## Usage

### Depositing ZIP files

The utility looks for new zip archives in the deposit directory.
All zip files in the deposit directory will be imported during one run of the scripts. 
If you are automating the utility, make sure the deposit directory has the right permission.

### Running the scripts

Invoke `dspace_dsa_maker.py` and then `dspace_dsa_ingest.py`

#### dspace\_dsa\_maker.py

1. Extracts all zip archives in the deposit directory.
2. For each extracted item, attempt to crosswalk the metadata XML into `dublin_core.xml` using the mapping defined in `crosswalk()` in `dspace_dsa_maker.py`.  
This mapping uses the terms defined in DSpace's `dc` schema in the metadata schema registry.
3. For each, make the DSpace Simple Archive by combining the crosswalked `dublin_core.xml`, the list of bitstreams found in the zip archive, and the `contents` file, required by DSpace to distinguish bitstreams.
4. Put each finished DSpace Simple Archive directory into a parent directory corresponding to an existing collection in DSpace. The collection is derived from the filename of each zip archive.
 
#### dspace\_dsa\_ingest.py

1. Invoke DSpace's own import script on each collection directory, importing each DSpace Simple Archive into DSpace.
2. Move all files from deposit and ingest directories into the archive directories for backup. 
3. Send email notifications, listing the filenames that were processed during the current run.

## Author

University of Toronto Libraries (<tspace@library.utoronto.ca>)

## License

DSpace Simple Archives Importer is licensed under Apache License 2.0.
