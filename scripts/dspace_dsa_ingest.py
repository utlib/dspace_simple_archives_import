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

class DSpaceDSAIngest:
  def __init__(self):
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
        "cjc" : "1234/123460",
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
    """Move generated DSAs into archive directory.
    Move original ZIP files into archive directory.
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
    """Upload all dspace simple archives from WORK_DIR to each journal's target collection
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
            user = "xiaofeng.zhao@utoronto.ca"
            source = os.path.join(self.ingest, journal_folder, year_folder)
            collection = self.collection_handles["test_collections_" + year_folder][journal_folder]
            mapfile = self.mapfiles + journal_folder + "_" + year_folder + self.date + self.time
            status = call(["/opt/dspace/bin/dspace", "import", "-a", "-e", user, "-s", source, "-c", collection, "-m", mapfile])
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
  DSpaceDSAIngest()
