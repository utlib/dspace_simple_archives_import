#!/bin/bash
/tspace_scratch/nrc/scripts/prep_metadata.py
rc=$?;
if [[ $rc !=0 ]];
    then exit $rc;
fi     
/tspace_scratch/nrc/scripts/upload_archive.py
