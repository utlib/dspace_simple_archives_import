#
# dspace_ingest.py - invoke DSpace Import script on the prepared DSpace Simple Archives
#   and archive the original zip files and DSpace Simple Archives
#
# Copyright 2018 University of Toronto Libraries
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/python
import os
from subprocess import call
from datetime import datetime
import shutil
import smtplib
from email.mime.text import MIMEText
import sys

class DSpaceDSAIngest:
  def __init__(self):
    """Make the working directories and DSpace collection handles dictionary.
    """
    print("Launching DSpace DSA Ingest.\nPreparing work directories.")

    self.root = os.getcwd()
    self.deposit = os.path.join(self.root, '../deposit/')
    self.extract = os.path.join(self.root, '../extract/')
    self.ingest = os.path.join(self.root, '../ingest/')
    self.mapfiles = os.path.join(self.root, '../mapfiles/')
    self.reports = os.path.join(self.root, '../reports/')
    self.dsa_archive = os.path.join(self.root, '../dsa_archive/')
    self.zip_archive = os.path.join(self.root, '../zip_archive/')

    for current_dir in [self.mapfiles, self.reports, self.dsa_archive, self.zip_archive]:
      if not os.path.isdir(current_dir):
        os.mkdir(current_dir)
        print("Made " + current_dir)

    self.date = datetime.now().strftime("_%B_%d_%Y")
    self.date_human = datetime.now().strftime("%B %d %Y")
    self.time = datetime.now().strftime("_%-I%p_%-M_%-S")
    self.time_human = datetime.now().strftime("%-I:%-M%p")

    self.collection_handles = {
      "test_collections_2017" : {
        "test_collection3" : "1234/123458",
        "test_collection4" : "1234/123459",
      },
      "test_collections_2018" : {
        "test_collection1" : "1234/123456",
        "test_collection2" : "1234/123457",
      }
    }
  
    if os.listdir(self.deposit):
      self.upload()
      self.archive()

  def archive(self):
    """Run after upload(). Move items from the ingest directories into 
       The archive directories for preservation/re-ingestion purpose.
       You can skip this step or redefine the archive location.
    """
    os.chdir(self.ingest)
    destination = os.path.join(self.dsa_archive, self.date)
    if not os.path.exists(destination):
      os.mkdir(destination)

    for journal in os.listdir("."):
      for year in os.listdir(os.path.join(self.ingest, journal)):                
        for item in os.listdir(os.path.join(self.ingest, journal, year)):
          try:		
            shutil.move(os.path.join(self.ingest, journal, year, item), destination)
          except shutil.Error:				
            shutil.rmtree(os.path.join(self.ingest, journal, year, item))

    os.chdir(self.deposit)
    for zipfile in os.listdir("."):
      try:
        shutil.move(zipfile, self.zip_archive)
      except shutil.Error, e:
        if "already exists" in str(e):
          os.remove(zipfile)
        else:
          pass

  def upload(self):
    """Use DSpace's import script on the ingest directories, matched with the
      collection handles dictionary.
    """
    os.chdir(self.ingest)
    indent = "\t"
    total_ingested = 0

    # initialize the report file for this ingest
    this_report_dir = os.path.join(self.reports, self.date)
    this_report_path = os.path.join(this_report_dir, self.time)
    try:
      os.mkdir(this_report_dir)
    except OSError, detail:
      pass
    report = open(this_report_path, 'w')
    report.write("DSpace ingestion report\n\n")
    report.write("The time of ingestion is " + self.date_human + ", " + self.time_human + "\n\n")

    # iterate through all journal directories to ingest into corresponding collections
    total_ingested = 0
    for journal_folder in os.listdir("."):
      for year_folder in os.listdir(journal_folder):
        count = 1
        for folder in os.listdir(os.path.join(journal_folder, year_folder)):
          count += 1
          total_ingested += 1
          report.write("Ingested " + folder + " for journal " + journal_folder + " for year " + year_folder + " \n\n")

          if count > 1:    
            user = "yourname@yourdspace.com"
            source = os.path.join(self.ingest, journal_folder, year_folder)
            collection = self.collection_handles["test_collections_" + year_folder][journal_folder]
            mapfile = self.mapfiles + journal_folder + "_" + year_folder + self.date + self.time
            status = call(["/dspace_root/bin/dspace", "import", "-a", "-e", user, "-s", source, "-c", collection, "-m", mapfile])
            if status != 0:
              report.close()
              os.remove(this_report_path)
              sys.exit(1)
            report.write("Sincerely, \n\nDSpace admin")
            report.close()

    if total_ingested == 0:
      os.remove(this_report_path)
    else:
      last_report = this_report_path
      email(last_report)

  def email(self, last_report):
    """Send the report to the list of recipients
    """
    if last_report == '':
      sys.exit(1)
    server = smtplib.SMTP('smtp.yourdspace.com')
    fp = open(last_report)
    body = MIMEText(fp.read())
    fp.close()

    sender = 'dspace@library.utoronto.ca'
    recipients = ['yourname@yourdspace.com']
    body['Subject'] = 'DSpace ingestion report'
    body['From'] = sender 
    body['To'] = ", ".join(recipients)
    server.sendmail(sender, recipients, body.as_string()) 

if __name__ == "__main__":
  DSpaceDSAIngest()
