#!/usr/bin/python
# coding=utf8
from bs4 import BeautifulSoup as makesoup
from zipfile import ZipFile
import os, shutil, glob, sys
from datetime import datetime

#dev = "/opt/dspace"
dev = ""

DEPOSIT_DIR = dev + "/tspace_scratch/nrc/deposit/"
DEPOSIT_2016_DIR = dev + "/tspace_scratch/nrc/deposit_2016/"
INGEST_DIR = dev + "/tspace_scratch/nrc/ingest/"
EXTRACT_DIR = dev + "/tspace_scratch/nrc/extract/"

DOI_BASE = "http://www.nrcresearchpress.com/doi/abs/"

DATESTAMP = datetime.now().strftime("%Y_%m_%d")
DATE = datetime.now().strftime("%A %B %d %Y")

class NRCZipParser:	
	
	def __init__(self, zipname):
		z = ZipFile(DEPOSIT_DIR + zipname)		
		z.extractall(EXTRACT_DIR)
                self.filename = zipname.split(".zip")[0]
                self.work_dir = os.path.join(EXTRACT_DIR, self.filename)
                self.journal_abbrv = zipname.split("-")[0]

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
		tag_list.append(makesoup("<dcvalue element='publication' qualifier='journal'>" + soup.JournalTitle.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='identifier' qualifier='issn'>" + soup.Issn.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
		if soup.Replaces.string:
			tag_list.append(makesoup("<dcvalue element='replaces'>" + soup.Replaces.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
		no_tag_title = soup.ArticleTitle.string.replace('<b>', '').replace('<i>', '').replace('</i>', '').replace('</b>','').replace('<sub>','').replace('</sub>','').replace('<sup>','').replace('</sup>','');
		tag_list.append(makesoup("<dcvalue element='title'>" + no_tag_title + "</dcvalue>", 'xml').contents[0])

		if soup.VernacularTitle.string:                        
			tag_list.append(makesoup("<dcvalue element='title' qualifier='vernacular'>" + soup.VernacularTitle.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
                
		for author in soup.find_all("Author"):			
		        middle_name = " " + author.MiddleName.string if author.MiddleName.string else ''
                        new_tag = newsoup.new_tag("dcvalue", element='contributor', qualifier='author')
                        new_tag.string = author.LastName.string.encode('utf8') + ", " + author.FirstName.string.encode('utf8') + " " + middle_name.encode('utf8')
                        newsoup.dublin_core.append(new_tag)
 
			if author.Affiliation and author.Affiliation.string: 
				tag_list.append(makesoup("<dcvalue element='affiliation' qualifier='institution'>" + author.Affiliation.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
		tag_list.append(makesoup("<dcvalue element='type'>" + soup.PublicationType.string.encode('utf8') + "</dcvalue>", 'xml').contents[0])		
		tag_list.append(makesoup("<dcvalue element='identifier' qualifier='doi'>" + DOI_BASE + soup.find(IdType="doi").string.encode('utf8') + "</dcvalue>", 'xml').contents[0])
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
		if soup.FullTextURL.string: 
			tag_list.append(makesoup("<dcvalue element='identifier' qualifier='uri'>" + soup.FullTextURL.string + "</dcvalue>", 'xml').contents[0])
		no_tag_abstract = soup.Abstract.string.replace('<b>', '').replace('<i>', '').replace('</i>', '').replace('</b>','').replace('<sub>','').replace('</sub>','');
		tag_list.append(makesoup("<dcvalue element='description' qualifier='abstract'>" + no_tag_abstract.encode('utf8') + "</dcvalue>", 'xml').contents[0])
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
    
        def ingest_prep(self):
		ingest_path = os.path.join(INGEST_DIR, self.journal_abbrv, self.year)
		if not os.path.exists(ingest_path):
			os.mkdir(ingest_path)                             		
		target = os.path.join(ingest_path, self.filename)
		if os.path.exists(target):
			shutil.rmtree(target)
		shutil.move(self.work_dir, os.path.join(ingest_path, self.filename))				                  

        def email(message):
            '''Send the report to the list of recipients'''

            jerry = smtplib.SMTP('mailer.library.utoronto.ca')

            fp = open(last_report)
            body = MIMEText(fp.read())
            fp.close()

            newman = 'tspace@library.utoronto.ca'
            hawaii = ['xiaofeng.zhao@utoronto.ca'] 

            body['Subject'] = 'Email from step1.py of tspace.library.utoronto.ca'
            body['From'] = newman
            body['To'] = ", ".join(hawaii)

            jerry.sendmail(newman, hawaii, body.as_string())

for nrc_zip in os.listdir(DEPOSIT_DIR):
    if nrc_zip.endswith('.zip'):
        parser = NRCZipParser(nrc_zip)
        parser.reorganize()
        parser.make_dc()
        parser.make_contents()            
        parser.ingest_prep()
