#!/usr/bin/python
import os
from subprocess import call
from datetime import datetime
import shutil
import smtplib
from email.mime.text import MIMEText
import sys

#dev = "/opt/dspace"
dev = ""

DEPOSIT_DIR = dev + "/tspace_scratch/nrc/deposit/"
INGEST_DIR = dev + "/tspace_scratch/nrc/ingest/"
EXTRACT_DIR = dev + "/tspace_scratch/nrc/extract/"
MAP_DIR = dev + "/tspace_scratch/mapfiles/nrc/"
ARCHIVE_DSA_DIR = dev + "/tspace_scratch/nrc/archive/dspace_simple_archives/"
ARCHIVE_ZIP_DIR = dev + "/tspace_scratch/nrc/archive/original_zips/"
REPORT_DIR = dev + "/tspace_scratch/nrc/reports/"
DATE = datetime.now().strftime("_%B_%d_%Y")
DATE_HUMAN = datetime.now().strftime("%B %d %Y")
CURRENT_TIME = datetime.now().strftime("_%-I%p_%-M_%-S")
CURRENT_TIME_HUMAN = datetime.now().strftime("%-I:%-M%p")

collection_handles = {
    "nrc_collections_2015" : {
        "apnm" : "1807/67550",
        "as" : "1807/67833",
        "bcb" : "1807/67552",
        "cjb" : "1807/67554",
        "cgj" : "1807/67556",
        "cjc" : "1807/67558",
        "cjce" : "1807/67560",
        "cjas" : "1807/73306",
        "cjes" : "1807/67562",
        "cjps" : "1807/73307",
        "cjfas" : "1807/67564",
        "cjfr" : "1807/67566",
        "cjm" : "1807/67568", #"1807/65469",
        "cjp" : "1807/67570",
        "cjpp" : "1807/67572",
        "cjss" : "1807/73308",
        "cjz" : "1807/67574",
        "er" : "1807/67576",
        "gen" : "1807/67578",
        "juvs" : "1807/67580" 
    },
    "nrc_collections_2016" : {
        "apnm" : "1807/71208",
        "as" : "1807/71209",
        "bcb" : "1807/71210",
        "cjb" : "1807/71211",
        "cgj" : "1807/71212",
        "cjc" : "1807/71213",
        "cjce" : "1807/71214",
        "cjas" : "1807/73265",
        "cjes" : "1807/71215",
        "cjps" : "1807/73263",
        "cjfas" : "1807/71216",
        "cjfr" : "1807/71217",
        "cjm" : "1807/71218",
        "cjp" : "1807/71207",
        "cjpp" : "1807/71219",
        "cjss" : "1807/73264",
        "cjz" : "1807/71220",
        "er" : "1807/71221",
        "gen" : "1807/71222",
        "juvs" : "1807/71223"    
    },
	"nrc_collections_2017" : {
		"apnm" : "1807/75476",
		"as" : "1807/75477",
		"bcb" : "1807/75478",
		"cjb" : "1807/75479",
		"cgj" : "1807/75480",
		"cjc" : "1807/75481",
		"cjce" : "1807/75482",
		"cjas" : "1807/75483",
		"cjes" : "1807/75484",
		"cjps" : "1807/75485",
		"cjfas" : "1807/75486",
		"cjfr" : "1807/75487",
		"cjm" : "1807/75488",
		"cjp" : "1807/75489",
		"cjpp" : "1807/75490",
		"cjss" : "1807/75491",
		"cjz" : "1807/75492",
		"er" : "1807/75493",
		"gen" : "1807/75494",
		"juvs" : "1807/75495"
	},
  "nrc_collections_2018" : {
    "apnm" : "1807/81035",
    "as" : "1807/81036",
    "bcb" : "1807/81037",
    "cjb" : "1807/81038",
    "cgj" : "1807/81039",
    "cjc" : "1807/81041",
    "cjce" : "1807/81042",
    "cjas" : "1807/81040",
    "cjes" : "1807/81043",
    "cjps" : "1807/81049",
    "cjfas" : "1807/81044",
    "cjfr" : "1807/81045",
    "cjm" : "1807/81046",
    "cjp" : "1807/81047",
    "cjpp" : "1807/81048",
    "cjss" : "1807/81050",
    "cjz" : "1807/81051",
    "er" : "1807/81052",
    "gen" : "1807/81053",
    "juvs" : "1807/81054"
  }
}

def archive():
	os.chdir(INGEST_DIR)

	# make a new dspace simple archive directory under archive if needed
	destination = ARCHIVE_DSA_DIR + DATE
        if not os.path.exists(destination):
            os.mkdir(destination)

	# move all simple archives under ingest into the new directory under archive
	for journal in os.listdir("."):
	    for year in os.listdir(os.path.join(INGEST_DIR, journal)):                
		for item in os.listdir(os.path.join(INGEST_DIR, journal, year)):
			try:		
				shutil.move(os.path.join(INGEST_DIR, journal, year, item), destination)
			except shutil.Error:				
				shutil.rmtree(os.path.join(INGEST_DIR, journal, year, item))

	# move all zip files under deposit into archive/original_zips
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
        '''Upload all dspace simple archives from WORK_DIR to each journal's target collection'''
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
        report.write("TSpace ingestion report for NRC Journal Press community\n\n")
        report.write("The time of ingestion is " + DATE_HUMAN + ", " + CURRENT_TIME_HUMAN + "\n\n")

        total_ingested = 0
        for journal_folder in os.listdir("."):
            #print "Scanning " + journal_folder
            for year_folder in os.listdir(journal_folder):
                #print indent + "Scanning " + journal_folder + " - " + year_folder
                count = 1
                for folder in os.listdir(os.path.join(journal_folder, year_folder)):
                        #print indent + indent + str(count) + ". " + folder
                        count += 1     
                        total_ingested += 1
                        report.write("Ingested " + folder + " for journal " + journal_folder + " for year " + year_folder + " \n\n")
               	if count > 1:    
                        # call the dspace import shell script
                        user = "xiaofeng.zhao@utoronto.ca"
                        source = os.path.join(INGEST_DIR, journal_folder, year_folder)
                        collection = collection_handles["nrc_collections_" + year_folder][journal_folder]
                        mapfile = MAP_DIR + journal_folder + "_" + year_folder + DATE + CURRENT_TIME
			#print user, source, collection, mapfile
                        status = call(["sudo", "/opt/dspace/bin/dspace", "import", "-a", "-e", user, "-s", source, "-c", collection, "-m", mapfile])
                        if status != 0:
                                #print "Error: /opt/dspace/bin/dspace returned non-ok status"
				report.close()
				os.remove(this_report_path)
                                sys.exit(1)
        report.write("Sincerely, \n\nTSpace admin")
        report.close()
        #print "Total ingest: " + str(total_ingested)
        if total_ingested == 0:
                os.remove(this_report_path)
        else:
            last_report = this_report_path
            email(last_report)

def email(last_report):
    '''Send the report to the list of recipients'''

    if last_report == '':
        #print "Report does not exist. Please check if the report was correctly generated."
        sys.exit(1)

    jerry = smtplib.SMTP('mailer.library.utoronto.ca')

    fp = open(last_report)
    body = MIMEText(fp.read())
    fp.close()

    newman = 'tspace@library.utoronto.ca'
    hawaii = ['xiaofeng.zhao@utoronto.ca', 'mariya.maistrovskaya@utoronto.ca', 'Accepted.manuscripts@cdnsciencepub.com']

    body['Subject'] = 'NRC Research Press University of Toronto TSpace ingestion report'
    body['From'] = newman
    body['To'] = ", ".join(hawaii)

    jerry.sendmail(newman, hawaii, body.as_string()) 

count = 0
for nrc_zip in os.listdir(DEPOSIT_DIR):
	count += 1
if count > 0:
	upload() #1.	
        archive() #2.
