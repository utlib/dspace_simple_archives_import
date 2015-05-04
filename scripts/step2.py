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
WORK_DIR = dev + "/tspace_scratch/nrc/prepare/"
MAP_DIR = dev + "/tspace_scratch/mapfiles/nrc/"
ARCHIVE_DSA_DIR = dev + "/tspace_scratch/nrc/archive/dspace_simple_archives/"
ARCHIVE_ZIP_DIR = dev + "/tspace_scratch/nrc/archive/original_zips/"
REPORT_DIR = dev + "/tspace_scratch/nrc/reports/"
DATE = datetime.now().strftime("_%B_%d_%Y")
DATE_HUMAN = datetime.now().strftime("%B %d %Y")
CURRENT_TIME = datetime.now().strftime("_%-I%p_%-M_%-S")
CURRENT_TIME_HUMAN = datetime.now().strftime("%-I:%-M%p")

nrc_collections = {
    "apnm" : "1807/65451",
    "as" : "1807/67833",
    "bcb" : "1807/67552",
    "b" : "1807/67554",
    "cgj" : "1807/67556",
    "cjc" : "1807/67558",
    "cjce" : "1807/67560",
    "cjes" : "1807/67562",
    "cjfas" : "1807/67564",
    "cjfr" : "1807/67566",
    "cjm" : "1807/65513", #"1807/65469",
    "cjp" : "1807/67570",
    "cjpp" : "1807/67572",
    "cjz" : "1807/67574",
    "er" : "1807/67576",
        "g" : "1807/67578",
        "juvs" : "1807/67580" 
}

nrc_collections_dev = {
    "apnm" : "1807/42106",
    "as" : "1807/42106",
    "bcb" : "1807/42106",
    "b" : "1807/42106",
    "cgj" : "1807/42106",
    "cjc" : "1807/42106",
    "cjce" : "1807/42106",
    "cjes" : "1807/42106",
    "cjfas" : "1807/42106",
    "cjfr" : "1807/42106",
    "cjm" : "1807/42106", #"1807/42106",
    "cjp" : "1807/42106",
    "cjpp" : "1807/42106",
    "cjz" : "1807/42106",
    "er" : "1807/42106",
        "g" : "1807/42106",
        "juvs" : "1807/42106"
}


def archive():
        '''
		1. Backup the ingested DSpace simple archives into the archiving directory for potentially reingestion
		2. Backup the original zipfiles	
	'''

	# backup DSpace simple archives	
        os.chdir(WORK_DIR)
        destination = ARCHIVE_DSA_DIR + DATE
	try:
	        os.mkdir(destination)
	except OSError:
		pass
        indent = "\t"
        for journal_folder in os.listdir("."):
                print "Archiving " + journal_folder
                count = 1
                for folder in os.listdir(journal_folder):
                        print indent + folder
                        shutil.move(os.path.join(journal_folder, folder), destination)

	# backup original zip files
	os.chdir(DEPOSIT_DIR)
	dest = ARCHIVE_ZIP_DIR + DATE 
	try:
		os.mkdir(dest)
	except OSError:
		pass
	for zipfile in os.listdir("."):
		shutil.move(zipfile, dest)

def upload():
        '''Upload all dspace simple archives from WORK_DIR to each journal's target collection'''
        os.chdir(WORK_DIR)
        indent = "\t"
        total_ingested = 0
        
        # initialize the report file for this ingest
        this_report_dir = os.path.join(REPORT_DIR, DATE)
        this_report_path = os.path.join(this_report_dir, CURRENT_TIME)
        try:
                os.mkdir(this_report_dir)
        except OSError, detail:
                print detail # directory already exists due to a previous ingest
                pass
        report = open(this_report_path, 'w')
        report.write("TSpace ingestion report for NRC Journal Press community\n\n")
        report.write("The time of ingestion is " + DATE_HUMAN + ", " + CURRENT_TIME_HUMAN + "\n\n")

        total_ingested = 0
        # iterate the journals in the WORK_DIR
        for journal_folder in os.listdir("."):
                print "Scanning " + journal_folder
                count = 1
                for folder in os.listdir(journal_folder):
                        print indent + str(count) + ". " + folder
                        count += 1     
                        total_ingested += 1
                        report.write("Ingested " + folder + " for journal " + journal_folder + " \n\n")
                if count == 1:
                        print indent + "Nothing to upload"
                else:   
                        # call the dspace import shell script
                        user = "xiaofeng.zhao@utoronto.ca"
                        source = os.path.join(WORK_DIR, journal_folder)
                        collection = nrc_collections[journal_folder]
                        mapfile = MAP_DIR + journal_folder + DATE + CURRENT_TIME
			print user, source, collection, mapfile
                        status = call(["sudo", "/opt/dspace/bin/dspace", "import", "-a", "-e", user, "-s", source, "-c", collection, "-m", mapfile])
                        if status != 0:
                                print "Error: /opt/dspace/bin/dspace returned non-ok status"
				report.close()
				os.remove(this_report_path)
                                sys.exit(1)

        report.write("Sincerely, \n\nTSpace admin")
        report.close()
        print "Total ingest: " + str(total_ingested)
        if total_ingested == 0:
                os.remove(this_report_path)
        else:
            last_report = this_report_path
            email(last_report)

def email(last_report):
    '''Send the report to the list of recipients'''

    if last_report == '':
        print "Aw, Snap! no report to send even though something tried to send report."
        sys.exit(1)

    jerry = smtplib.SMTP('mailer.library.utoronto.ca')

    fp = open(last_report)
    body = MIMEText(fp.read())
    fp.close()

    newman = 'tspace@library.utoronto.ca'
    hawaii = ['xiaofeng.zhao@utoronto.ca', 'courtney.bodi@mail.utoronto.ca', 'mariya.maistrovskaya@utoronto.ca']

    body['Subject'] = 'NRC/CSP to U of T TSpace ingestion report'
    body['From'] = newman
    body['To'] = ", ".join(hawaii)

    jerry.sendmail(newman, hawaii, body.as_string()) # make sure not too many people get their mail
                
upload() #1.
archive() #2.
