#
# dspace_dsa_maker.py - crosswalk PubMed metadata to DSpace Dublin Core 
#   and prepare DSpace Simple Archives (DSA) for ingestion.
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
# coding=utf8
from bs4 import BeautifulSoup as makesoup
from zipfile import ZipFile
import os, shutil, glob, sys
from datetime import datetime

class DSpaceDSAMaker:	
  def __init__(self):    
    print("Launching DSpace DSA Maker. \nPreparing work directories.")

    self.root = os.getcwd()
    self.deposit = os.path.join(self.root, '../deposit/')
    self.extract = os.path.join(self.root, '../extract/')    
    self.ingest = os.path.join(self.root, '../ingest/')

    # purge the extract directory of failed ingests
    if os.path.isdir(self.extract):
      shutil.rmtree(self.extract)

    # make deposit, extract and ingest work directories
    for current_dir in [self.deposit, self.extract, self.ingest]:
      if not os.path.isdir(current_dir):
        os.mkdir(current_dir)
        print("Made " + current_dir)

    self.datetime = datetime.now().strftime("%Y_%m_%d")
    self.date = datetime.now().strftime("%A %B %d %Y")

    # Set the year of publication based on metadata
    self.year = ''

    self.iterate()

  def iterate(self):
    if not os.listdir(self.deposit):
      print("Nothing to ingest. Please check " + self.deposit)
    else:
      print("Checking " + self.deposit + " for new items to ingest.")
      for original_zip in os.listdir(self.deposit):
        if original_zip.endswith('.zip'):
          print("Found " + original_zip)
          self.extract_zip(original_zip)
          self.supplementary_files()
          self.crosswalk()
          self.contents()
          self.ingest_prep()

  def extract_zip(self, zipname):
    z = ZipFile(self.deposit + zipname)
    z.extractall(self.extract)
    self.filename = zipname.split(".zip")[0]
    self.work_dir = os.path.join(self.extract, self.filename)
    self.journal_name = zipname.split("-")[0]

  def supplementary_files(self):
    """Extract supplementary files into DSA.
    Remove irrelevant files.
    Set main PDF filename.
    """
    os.chdir(self.work_dir)

    for f in os.listdir("."):
      if f.endswith("manifest.html") or f == "PubMed.dtd":
        os.remove(f)
      elif os.path.isdir(f):
        os.chdir(f)        
        for pdf in glob.glob("*"):
          shutil.move(pdf, "../")
        os.chdir("../")
        shutil.rmtree(f)

    for f in os.listdir("."):
      if f.endswith(".pdf"):
        self.manuscript = f			

  def crosswalk(self):
    """Convert original XML into DSpace DC - Tag by tag
    """
    os.chdir(self.work_dir)

    # assume the main metadata is the only XML file in the original directory
    base = open(glob.glob("*.xml")[0])
    soup = makesoup(base, 'xml')

    # make a container soup, and make smaller soups for each field, which are inserted into the container.
    newsoup = makesoup('<dublin_core schema="dc"></dublin_core>', 'xml')
    tag_list = []

    # title
    tag_list.append(makesoup("<dcvalue element='title'>" + soup.find('article-title').string + "</dcvalue>", 'xml').contents[0])

    # author(s)
    for author_container in soup.find_all('contrib', {'contrib-type' : 'author'}):
      tag_list.append(makesoup("<dcvalue element='contributor' qualifier='author'>" + author_container.surname.string + ", " + author_container.find('given-names').string  + "</dcvalue>", 'xml').contents[0])

    for author_container in soup.find_all('contrib', {'contrib-type' : 'editor'}):
      tag_list.append(makesoup("<dcvalue element='contributor' qualifier='editor'>" + author_container.surname.string + ", " + author_container.find('given-names').string  + "</dcvalue>", 'xml').contents[0])

    # abstract
    tag_list.append(makesoup("<dcvalue element='abstract'>" + soup.abstract.p.string + "</dcvalue>", 'xml').contents[0])

    # date(s)
    date_accepted = soup.find('date', {'date-type' : 'accepted'})    
    tag_list.append(makesoup("<dcvalue element='date' qualifier='accepted'>" + "-".join((date_accepted.year.string, date_accepted.month.string, date_accepted.day.string)) + "</dcvalue>", 'xml').contents[0])
    self.year = date_accepted.year.string

    date_revised = soup.find('date', {'date-type' : 'rev-recd'})
    tag_list.append(makesoup("<dcvalue element='date' qualifier='revised'>" + "-".join((date_revised.year.string, date_revised.month.string, date_revised.day.string)) + "</dcvalue>", 'xml').contents[0])

    date_received = soup.find('date', {'date-type' : 'received'})
    tag_list.append(makesoup("<dcvalue element='date' qualifier='received'>" + "-".join((date_received.year.string, date_received.month.string, date_received.day.string)) + "</dcvalue>", 'xml').contents[0])
    
    tag_list.append(makesoup("<dcvalue element='date' qualifier='issued'>" + "-".join((date_accepted.year.string, date_accepted.month.string, date_accepted.day.string)) + "</dcvalue>", 'xml').contents[0])

    # publisher
    tag_list.append(makesoup("<dcvalue element='publisher'>" + soup.find('publisher-name').string + "</dcvalue>", 'xml').contents[0])

    # issn
    tag_list.append(makesoup("<dcvalue element='identifier' qualifier='issn'>" + soup.find("issn", {'pub-type' : 'ppub'}).string + "</dcvalue>", 'xml').contents[0])
  
    # essn
    tag_list.append(makesoup("<dcvalue element='identifier' qualifier='issn'>" + soup.find("issn", {'pub-type' : 'epub'}).string + "</dcvalue>", 'xml').contents[0]) 

    # DOI
    tag_list.append(makesoup("<dcvalue element='identifier' qualifier='doi'>https://dx.doi.org/" + soup.find('article-id', {'pub-id-type' : 'doi'}).string + "</dcvalue>", 'xml').contents[0])
  
    # insert all created tags from taglist into the container soup
    dc = newsoup.find('dublin_core')
    for tag in tag_list:
      dc.append(tag)
    self.soup = newsoup

    # write out the complete DSpace DC
    dublin_core = open("dublin_core.xml", 'w')
    dublin_core.write(str(newsoup))
    dublin_core.close()
    os.chdir("../")

  def contents(self):
    """The contents file is required by DSA.
    This file simply lists all bitstreams that will be ingested in an DSA.
    """    
    os.chdir(self.work_dir)
    contents = open('contents', 'w')
    contents.write(self.manuscript + "\n")
    for f in os.listdir("."):
      if f not in ['dublin_core.xml', 'contents', self.manuscript] and not f.endswith("metadata.xml"):
        contents.write(f + '\n')
    contents.close()

  def ingest_prep(self):
    """Move completed DSA into ingestion directory,
    divided by journal name. Each journal corresponds with one collection.
    """
    ingest_path = os.path.join(self.ingest, self.journal_name, self.year)
    if not os.path.exists(ingest_path):
      os.makedirs(ingest_path)                             		
    target = os.path.join(ingest_path, self.filename)
    if os.path.exists(target):
      shutil.rmtree(target)
    shutil.move(self.work_dir, os.path.join(ingest_path, self.filename))				                  

if __name__ == "__main__":
  DSpaceDSAMaker()
