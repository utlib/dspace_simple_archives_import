#
# dspace_dsa_maker.py - crosswalk PubMed metadata to DSpace Dublin Core 
#   and prepare DSpace Simple Archives (DSA) for ingestion.
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
# coding=utf8
from bs4 import BeautifulSoup as makesoup
from zipfile import ZipFile
import os, shutil, glob, sys
from datetime import datetime

class DSpaceDSAMaker:	
  def __init__(self):    
    print("Launching DSpace DSA Maker. \nPreparing work directories.")

    self.root = os.path.dirname(os.path.abspath(__file__))
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
          self.current_zip = original_zip 
          self.extract_zip(original_zip)
          self.crosswalk()
          self.contents()
          self.move_to_ingest()

  def extract_zip(self, zipname):
    z = ZipFile(self.deposit + zipname)
    z.extractall(self.extract)
    self.filename = zipname.split(".zip")[0]
    self.extract_dir = os.path.join(self.extract, self.filename)
    self.journal_name = zipname.split("-")[0]

  def crosswalk(self):
    """Convert original XML into DSpace DC - Tag by tag
    """
    os.chdir(self.extract_dir)

    # assume the main metadata is the only XML file in the original directory
    base = open(glob.glob("*-metadata.xml")[0])
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
    os.chdir(self.extract_dir)

    # assuming dublin_core.xml has been successfully made. Old MD can be deleted.
    os.remove(glob.glob("*-metadata.xml")[0])
    # also delete the directories that were transferred but never used - ScholarOne sends these by default
    os.remove(glob.glob("*-manifest.html")[0])
    shutil.rmtree('pdf_renditions')
    shutil.rmtree('doc')

    # move the main PDF from its containing directory to the root directory we are working in
    if os.path.isdir('pdf'):
      self.manuscript = os.path.basename(glob.glob('pdf/*.pdf')[0])
      shutil.move('pdf/' + self.manuscript, '.')
      shutil.rmtree('pdf') 
    else:
      sys.exit("Unable to produce DSpaceSA for UTP zip file " + self.current_zip + "\nDirectory 'pdf' could not be found.")
    # in the same fashion, move any suppl files to the root directory
    if os.path.isdir('suppl_data'):
      for f in os.listdir('suppl_data'):
        shutil.move('suppl_data/' + f, '.')
      shutil.rmtree('suppl_data')

    # add all non-dspace files into the contents file list text file for dspace import
    # assuming we cleaned up all non-importable files such as pdf_renditions, doc and the manifest
    contents = open('contents', 'w')
    contents.write(self.manuscript + "\n")
    for f in os.listdir("."):
      if f not in ['dublin_core.xml', 'contents', self.manuscript]:
        contents.write(f + '\n')
    contents.close()

  def move_to_ingest(self):
    """Move completed DSA into ingestion directory,
    divided by journal name. Each journal corresponds with one collection.
    """
    ingest_path = os.path.join(self.ingest, self.journal_name, self.year)
    if not os.path.exists(ingest_path):
      os.makedirs(ingest_path)                             		
    target = os.path.join(ingest_path, self.filename)
    if os.path.exists(target):
      shutil.rmtree(target)
    shutil.move(self.extract_dir, os.path.join(ingest_path, self.filename))				                  

if __name__ == "__main__":
  DSpaceDSAMaker()
