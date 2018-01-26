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

DEPOSIT_DIR = "../deposit"
EXTRACT_DIR = "../extract"
INGEST_DIR = "../ingest"

DOI_BASE = "http://www.nrcresearchpress.com/doi/abs/"
DATESTAMP = datetime.now().strftime("%Y_%m_%d")
DATE = datetime.now().strftime("%A %B %d %Y")

class DSpaceDSAMaker:	
  def __init__(self, zipname):
    os.mkdir(DEPOSIT_DIR)
    os.mkdir(EXTRACT_DIR)
    z = ZipFile(DEPOSIT_DIR + zipname)		
    z.extractall(EXTRACT_DIR)

    self.filename = zipname.split(".zip")[0]
    self.work_dir = os.path.join(EXTRACT_DIR, self.filename)
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
    base = open(glob.glob("*.xml")[0])
    soup = makesoup(base, 'xml')
    newsoup = makesoup('<dublin_core schema="dc"></dublin_core>', 'xml')
    tag_list = []		
    tag_list.append(makesoup("<dcvalue element='publisher'>NRC Research Press (a division of Canadian Science Publishing)</dcvalue>", 'xml').contents[0])

    if soup.Replaces.string:
      tag_list.append(makesoup("<dcvalue element='replaces'>" + soup.Replaces.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])

    # publication name
    tag_list.append(makesoup("<dcvalue element='publication' qualifier='journal'>" + soup.JournalTitle.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])

    # issn
    tag_list.append(makesoup("<dcvalue element='identifier' qualifier='issn'>" + soup.Issn.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])

    # titles
    no_tag_title = soup.ArticleTitle.string.replace('<b>', '').replace('<i>', '').replace('</i>', '').replace('</b>','').replace('<sub>','').replace('</sub>','').replace('<sup>','').replace('</sup>','');
    tag_list.append(makesoup("<dcvalue element='title'>" + no_tag_title + "</dcvalue>", 'xml').contents[0])
    if soup.VernacularTitle.string:                        
      tag_list.append(makesoup("<dcvalue element='title' qualifier='vernacular'>" + soup.VernacularTitle.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])

    # authors
    for author in soup.find_all("Author"):			
      middle_name = " " + author.MiddleName.string if author.MiddleName.string else ''
      new_tag = newsoup.new_tag("dcvalue", element='contributor', qualifier='author')
      new_tag.string = author.LastName.string.encode('utf8') + ", " + author.FirstName.string.encode('utf8') + " " + middle_name.encode('utf8')
      newsoup.dublin_core.append(new_tag)

    if author.Affiliation and author.Affiliation.string: 
      tag_list.append(makesoup("<dcvalue element='affiliation' qualifier='institution'>" + author.Affiliation.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
      tag_list.append(makesoup("<dcvalue element='type'>" + soup.PublicationType.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])		
      tag_list.append(makesoup("<dcvalue element='identifier' qualifier='doi'>" + DOI_BASE + soup.find(IdType="doi").string.encode('utf8') + "</dcvalue>", 'xml').contents[0])

    # dates
    year = soup.find(PubStatus="received").find("Year").string 
    month = soup.find(PubStatus="received").find("Month").string
    day = soup.find(PubStatus="received").find("Day").string
    if year is None:
      year = ''
    if month is None:
      month = ''
    if day is None:
      day = ''
    tag_list.append(makesoup("<dcvalue element='date' qualifier='submitted'>" + year + "-" + month + "-" + day + "</dcvalue>", 'xml').contents[0])

    year = soup.find(PubStatus="revised").find("Year").string
    month = soup.find(PubStatus="revised").find("Month").string
    day = soup.find(PubStatus="revised").find("Day").string
    if year is None:
      year = ''
    if month is None:
      month = ''
    if day is None:
      day = ''
    tag_list.append(makesoup("<dcvalue element='date' qualifier='revised'>" + year + "-" + month + "-" + day + "</dcvalue>", 'xml').contents[0])

    year = soup.find(PubStatus="accepted").find("Year").string
    self.year = year
    month = soup.find(PubStatus="accepted").find("Month").string
    day = soup.find(PubStatus="accepted").find("Day").string            
    if year is None:
      year = ''
    if month is None:
      month = ''
    if day is None:
      day = ''
    tag_list.append(makesoup("<dcvalue element='date' qualifier='issued'>" + year + "-" + month + "-" + day + "</dcvalue>", 'xml').contents[0])
    tag_list.append(makesoup("<dcvalue element='date' qualifier='accepted'>" + year + "-" + month + "-" + day + "</dcvalue>", 'xml').contents[0])
  
    # url
    if soup.FullTextURL.string: 
      tag_list.append(makesoup("<dcvalue element='identifier' qualifier='uri'>" + soup.FullTextURL.string + "</dcvalue>", 'xml').contents[0])
  
    # abstract
    no_tag_abstract = soup.Abstract.string.replace('<b>', '').replace('<i>', '').replace('</i>', '').replace('</b>','').replace('<sub>','').replace('</sub>','');
    tag_list.append(makesoup("<dcvalue element='description' qualifier='abstract'>" + no_tag_abstract.encode('utf8') + "</dcvalue>", 'xml').contents[0])
    tag_list.append(makesoup("<dcvalue element='description' qualifier='disclaimer'>The accepted manuscript in pdf format is listed with the files at the bottom of this page. The presentation of the authors' names and (or) special characters in the title of the manuscript may differ slightly between what is listed on this page and what is listed in the pdf file of the accepted manuscript; that in the pdf file of the accepted manuscript is what was submitted by the author.</dcvalue>", "xml").contents[0])

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
    mkdir(INGEST_DIR)
    ingest_path = os.path.join(INGEST_DIR, self.journal_name, self.year)
    if not os.path.exists(ingest_path):
      os.mkdir(ingest_path)                             		
    target = os.path.join(ingest_path, self.filename)
    if os.path.exists(target):
      shutil.rmtree(target)
    shutil.move(self.work_dir, os.path.join(ingest_path, self.filename))				                  

if __name__ == "__main__":
  for original_zip in os.listdir(DEPOSIT_DIR):
    if original_zip.endswith('.zip'):
      dsa_maker = DSpaceDSAMaker(original_zip)
      dsa_maker.supplementary_files()
      dsa_maker.crosswalk()
      dsa_maker.contents()            
      dsa_maker.ingest_prep()
