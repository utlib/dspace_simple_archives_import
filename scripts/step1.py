# coding=utf8
from bs4 import BeautifulSoup as makesoup
from zipfile import ZipFile
import os, shutil, glob, sys
from datetime import datetime

#dev = "/opt/dspace"
dev = ""

DEPOSIT_DIR = dev + "/tspace_scratch/nrc/deposit/"
REPORT_DIR = dev + "/tspace_scratch/nrc/reports/ingest_report"
WORK_DIR = dev + "/tspace_scratch/nrc/prepare/"

DOI_BASE = "http://www.nrcresearchpress.com/doi/abs/"

DATESTAMP = datetime.now().strftime("%Y_%m_%d")
DATE = datetime.now().strftime("%A %B %d %Y")

class NRCZipParser:	
	
	def __init__(self, zipname):
		# filename of the zipfile
		self.zipname = zipname		
		self.zipfile_path = DEPOSIT_DIR + zipname
		# find out which journal this belongs to
		self.journal_name = zipname.split("-")[0]		
		# Extract into the working directory for Simple Archive preparation
		z = ZipFile(DEPOSIT_DIR + zipname)
		z.extractall(WORK_DIR + self.journal_name)
		self.work_dir = WORK_DIR + self.journal_name + "/" + self.zipname[0:-4]

	def reorganize(self):
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
		
	def make_dc(self):
		os.chdir(self.work_dir)
		base = open(glob.glob("*.xml")[0])
		soup = makesoup(base, 'xml')
		newsoup = makesoup('<dublin_core schema="dc"></dublin_core>', 'xml')
				
		# map all the tags from the old soup
		tag_list = []		
		tag_list.append(makesoup("<dcvalue element='publisher'>NRC Research Press (a division of Canadian Science Publishing)</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='publication' qualifier='journal'>" + soup.JournalTitle.string + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='identifier' qualifier='issn'>" + soup.Issn.string + "</dcvalue>", 'xml').contents[0])
		if soup.Replaces.string:
			tag_list.append(makesoup("<dcvalue element='replaces'>" + soup.Replaces.string + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='title'>" + soup.ArticleTitle.string + "</dcvalue>", 'xml').contents[0])
		if soup.VernacularTitle.string:
			tag_list.append(makesoup("<dcvalue element='title' qualifier='vernacular'>" + soup.VernacularTitle.string + "</dcvalue>", 'xml').contents[0])
		for author in soup.find_all("Author"):			
			middle_name = " " + author.MiddleName.string if author.MiddleName.string else ''
			tag_list.append(makesoup("<dcvalue element='contributor' qualifier='author'>" + author.LastName.string + ", " + author.FirstName.string + middle_name + "</dcvalue>", 'xml').contents[0])
			if author.Affiliation.string: 
				tag_list.append(makesoup("<dcvalue element='affiliation' qualifier='institution'>" + author.Affiliation.string + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='type'>" + soup.PublicationType.string + "</dcvalue>", 'xml').contents[0])		
		tag_list.append(makesoup("<dcvalue element='identifier' qualifier='doi'>" + DOI_BASE + soup.find(IdType="doi").string + "</dcvalue>", 'xml').contents[0])
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
		if soup.FullTextURL.string: 
			tag_list.append(makesoup("<dcvalue element='identifier' qualifier='uri'>" + soup.FullTextURL.string + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='description' qualifier='abstract'>" + soup.Abstract.string + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='description' qualifier='disclaimer'>The accepted manuscript in pdf format is listed with the files at the bottom of this page. The presentation of the authors' names and (or) special characters in the title of the manuscript may differ slightly between what is listed on this page and what is listed in the pdf file of the accepted manuscript; that in the pdf file of the accepted manuscript is what was submitted by the author.</dcvalue>", "xml").contents[0])
		
		dc = newsoup.find('dublin_core')
		for tag in tag_list:
			dc.append(tag)
		self.soup = newsoup
		
		dublin_core = open("dublin_core.xml", 'w')
		dublin_core.write(str(newsoup))
		dublin_core.close()
	
		os.chdir("../")
		
	def make_contents(self):
		os.chdir(self.work_dir)
		contents = open('contents', 'w')
		contents.write(self.manuscript + "\n")
		for f in os.listdir("."):
			if f not in ['dublin_core.xml', 'contents', self.manuscript] and not f.endswith("metadata.xml"):
				contents.write(f + '\n')
		contents.close()

count = 0
for nrc_zip in os.listdir(DEPOSIT_DIR):
	if nrc_zip.endswith('.zip'): 
		print "Parsing " + nrc_zip
		parser = NRCZipParser(nrc_zip)
		parser.reorganize()
		parser.make_dc()
		parser.make_contents()
		count += 1
print "Parsed " + str(count) + " items in total"
