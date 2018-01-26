#
# dspace_ingest.py - invoke DSpace Import script on the prepared DSAs
#   and archive the original ZIP files and DSAs into set locations
#
# Copyright (C) 2018 University of Toronto Libraries
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

#!/usr/bin/python
import os
from subprocess import call
from datetime import datetime
import shutil
import smtplib
from email.mime.text import MIMEText
import sys

DEPOSIT_DIR = "../deposit/"
INGEST_DIR = "../ingest/"
EXTRACT_DIR = "../extract/"
MAP_DIR = "../mapfiles/"
ARCHIVE_DSA_DIR = "../archive/dspace_simple_archives/"
ARCHIVE_ZIP_DIR = "../archive/original_zips/"
REPORT_DIR = "../reports/"

DATE = datetime.now().strftime("_%B_%d_%Y")
DATE_HUMAN = datetime.now().strftime("%B %d %Y")
CURRENT_TIME = datetime.now().strftime("_%-I%p_%-M_%-S")
CURRENT_TIME_HUMAN = datetime.now().strftime("%-I:%-M%p")

collection_handles = {
  "test_collections_2018" : {
    "test_collection1" : "1234/123456",
    "test_collection2" : "1234/123457",
  }
}

def archive():
  """Move generated DSAs into archive directory.
  Move original ZIP files into archive directory.
  """
  os.chdir(INGEST_DIR)
  destination = ARCHIVE_DSA_DIR + DATE
  if not os.path.exists(destination):
    os.mkdir(destination)

  for journal in os.listdir("."):
    for year in os.listdir(os.path.join(INGEST_DIR, journal)):                
      for item in os.listdir(os.path.join(INGEST_DIR, journal, year)):
        try:		
          shutil.move(os.path.join(INGEST_DIR, journal, year, item), destination)
        except shutil.Error:				
          shutil.rmtree(os.path.join(INGEST_DIR, journal, year, item))

  os.chdir(DEPOSIT_DIR)
  for zipfile in os.listdir("."):
    try:
      shutil.move(zipfile, ARCHIVE_ZIP_DIR)
    except shutil.Error, e:
      if "already exists" in str(e):
        os.remove(zipfile)
      else:
        pass

def upload():
  """Upload all dspace simple archives from WORK_DIR to each journal's target collection
  """
  os.chdir(INGEST_DIR)
  indent = "\t"
  total_ingested = 0

  # initialize the report file for this ingest
  this_report_dir = os.path.join(REPORT_DIR, DATE)
  this_report_path = os.path.join(this_report_dir, CURRENT_TIME)
  try:
    os.mkdir(this_report_dir)
  except OSError, detail:
    pass
  report = open(this_report_path, 'w')
  report.write("DSpace ingestion report\n\n")
  report.write("The time of ingestion is " + DATE_HUMAN + ", " + CURRENT_TIME_HUMAN + "\n\n")

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
          user = "xiaofeng.zhao@utoronto.ca"
          source = os.path.join(INGEST_DIR, journal_folder, year_folder)
          collection = collection_handles["test_collections_" + year_folder][journal_folder]
          mapfile = MAP_DIR + journal_folder + "_" + year_folder + DATE + CURRENT_TIME
          status = call(["sudo", "/opt/dspace/bin/dspace", "import", "-a", "-e", user, "-s", source, "-c", collection, "-m", mapfile])
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

def email(last_report):
  """Send the report to the list of recipients
  """
  if last_report == '':
    sys.exit(1)
  server = smtplib.SMTP('mailer.library.utoronto.ca')
  fp = open(last_report)
  body = MIMEText(fp.read())
  fp.close()

  sender = 'dspace@library.utoronto.ca'
  recipients = ['xiaofeng.zhao@utoronto.ca']
  body['Subject'] = 'DSpace ingestion report'
  body['From'] = sender 
  body['To'] = ", ".join(recipients)
  server.sendmail(sender, recipients, body.as_string()) 

if __name__ == "__main__":
  count = 0
  for nrc_zip in os.listdir(DEPOSIT_DIR):
    count += 1
    if count > 0:
      upload()
      archive()
