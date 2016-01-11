import unittest
from interfaces.stagingInterface import StagingInterface
from dataactcore.models.jobModels import Status, Type
from dataactcore.models import errorModels
import requests
from interfaces.jobTrackerInterface import JobTrackerInterface
from interfaces.validationInterface import ValidationInterface
from interfaces.errorInterface import ErrorInterface
import os
import inspect
import time
from dataactcore.aws.s3UrlHandler import s3UrlHandler
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from dataactcore.scripts.databaseSetup import runCommands
from dataactcore.scripts.createJobTables import createJobTables
from scripts.setupValidationDB import setupValidationDB
from dataactcore.scripts.clearErrors import clearErrors
from interfaces.interfaceHolder import InterfaceHolder
from dataactcore.scripts.clearJobs import clearJobs

class JobTests(unittest.TestCase):

    BASE_URL = "http://127.0.0.1:5000"
    #BASE_URL = "http://52.90.92.100:5000"
    JSON_HEADER = {"Content-Type": "application/json"}
    TABLE_POPULATED = False  # Gets set to true by the first test to populate the tables
    DROP_TABLES = False  # If true, staging tables are dropped after tests are run
    USE_THREADS = False
    INCLUDE_LONG_TESTS = True
    UPLOAD_FILES = True

    def __init__(self, methodName):
        """ Run scripts to clear the job tables and populate with a defined test set """
        super(JobTests, self).__init__(methodName=methodName)
        # Get staging handler

        if not self.TABLE_POPULATED:
            print("Initial setup")
            # Last job number
            lastJob = 100

            # Create staging database
            runCommands(StagingInterface.getCredDict(), [], "staging")
            self.stagingDb = InterfaceHolder.STAGING

            # Clear databases and run setup
            print("Resetting databases:")
            print("Job tracker")
            createJobTables()
            print("Error DB")
            clearErrors()
            print("Validation DB")
            setupValidationDB()

            # Define user
            user = 1
            # Upload needed files to S3

            s3FileNameValid = self.uploadFile("testValid.csv", user)
            s3FileNamePrereq = self.uploadFile("testPrereq.csv", user)
            s3FileNameBadValues = self.uploadFile("testBadValues.csv", user)
            s3FileNameMixed = self.uploadFile("testMixed.csv", user)
            s3FileNameEmpty = self.uploadFile("testEmpty.csv", user)
            s3FileNameMissingHeader = self.uploadFile("testMissingHeader.csv", user)
            s3FileNameBadHeader = self.uploadFile("testBadHeader.csv", user)
            s3FileNameMany = self.uploadFile("testMany.csv", user)
            s3FileNameOdd = self.uploadFile("testOddCharacters.csv", user)
            s3FileNameManyBad = self.uploadFile("testManyBadValues.csv", user)
            s3FileNameTestRules = self.uploadFile("testRules.csv", user)

            # Populate with a defined test set
            self.jobTracker = InterfaceHolder.JOB_TRACKER

            sqlStatements = ["INSERT INTO submission (datetime_utc) VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12),(13),(14),(15),(16)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",1, '" + s3FileNameValid + "',1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("file_upload")) + ",2,1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",2,1)",
            "INSERT INTO job_dependency (job_id, prerequisite_id) VALUES (3, 2)",
            "INSERT INTO job_status (status_id, type_id, submission_id, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("external_validation")) + ",4,1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, file_type_id) VALUES (" + str(Status.getStatus("finished")) + "," + str(Type.getType("csv_record_validation")) + ",5,1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, file_type_id) VALUES (" + str(Status.getStatus("finished")) + "," + str(Type.getType("file_upload")) + ",6,1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",6, '" + s3FileNamePrereq + "',1)",
            "INSERT INTO job_dependency (job_id, prerequisite_id) VALUES (7, 6)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",8, '" + s3FileNameBadValues + "',1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",9, '" + s3FileNameMixed + "',1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",10, '" + s3FileNameEmpty + "',1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",11, '" + s3FileNameMissingHeader + "',1)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",11, '" + s3FileNameBadHeader + "',2)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",11, '" + s3FileNameMany + "',3)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",14, '" + s3FileNameOdd + "',2)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",11, '" + s3FileNameManyBad + "',4)",
            "INSERT INTO job_status (status_id, type_id, submission_id, filename, file_type_id) VALUES (" + str(Status.getStatus("ready")) + "," + str(Type.getType("csv_record_validation")) + ",16, '" + s3FileNameTestRules + "',1)"
            ]
            print("Setting up job tracker")
            for statement in sqlStatements:
                self.jobTracker.runStatement(statement)
            validationDB = InterfaceHolder.VALIDATION

            sqlStatements = [
                "DELETE FROM rule",
                "DELETE FROM file_columns",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (3,1,'header 1','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (3,1,'header 2','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (3,4,'header 3','',False)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (3,4,'header 4','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (3,4,'header 5','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (1,1,'header 1','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (1,1,'header 2','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (1,4,'header 3','',False)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (1,4,'header 4','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (1,4,'header 5','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (2,1,'header 1','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (2,1,'header 2','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (2,4,'header 3','',False)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (2,4,'header 4','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (2,4,'header 5','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (4,1,'header 1','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (4,1,'header 2','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (4,4,'header 3','',False)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (4,4,'header 4','',True)",
                "INSERT INTO file_columns (file_id,field_types_id,name,description,required) VALUES (4,4,'header 5','',True)",
                "INSERT INTO rule (file_column_id, rule_type_id, rule_text_1, description) VALUES (1, 5, 0, 'value 1 must be greater than zero'),(1,3,13,'value 1 may not be 13'),(5,1,'INT','value 5 must be an integer'),(3,2,42,'value 3 must be equal to 42 if present'),(1,4,100,'value 1 must be less than 100')"
                ]
            for statement in sqlStatements:
                validationDB.runStatement(statement)

            # Remove existing tables from staging if they exist
            for jobId in range(1, lastJob+1):
                self.stagingDb.dropTable("job"+str(jobId))

            JobTests.TABLE_POPULATED = True
        else:
            self.stagingDb = InterfaceHolder.STAGING

    def uploadFile(self, filename, user):
        """ Upload file to S3 and return S3 filename"""
        # Get bucket name
        bucketName = s3UrlHandler.getBucketNameFromConfig()

        path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
        fullPath = path + "/" + filename

        # Create file names for S3
        s3FileName = str(user) + "/" + filename

        if(JobTests.UPLOAD_FILES) :
            # Use boto to put files on S3
            s3conn = S3Connection()
            key = Key(s3conn.get_bucket(bucketName))
            key.key = s3FileName
            bytesWritten = key.set_contents_from_filename(fullPath)

            assert(bytesWritten > 0)
        return s3FileName

    def test_valid_job(self):
        """ Test valid job """
        jobId = 1
        self.response = self.validateJob(1)
        self.waitOnJob(jobId, "finished")

        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(self.jobTracker.getStatus(jobId) == Status.getStatus("finished"))
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 37)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 1)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_rules(self):
        """ Test rules, should have one type failure and two value failures """
        jobId = 16
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "finished")
        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(self.jobTracker.getStatus(jobId) == Status.getStatus("finished"))
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 315)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 1)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 5)

    def test_bad_values_job(self):
        # Test job with bad values
        jobId = 8
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "finished")
        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(self.jobTracker.getStatus(jobId) == Status.getStatus("finished"))
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 5319)
        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 90)

    def test_many_bad_values_job(self):
        # Test job with many bad values
        if not self.INCLUDE_LONG_TESTS:
            return
        jobId = 15
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "finished")

        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(self.jobTracker.getStatus(jobId) == Status.getStatus("finished"))
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 103683914)
        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 1727355)

    def test_mixed_job(self):
        """ Test mixed job """
        jobId = 9
        self.response = self.validateJob(jobId)

        self.waitOnJob(9, "finished")
        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(self.jobTracker.getStatus(jobId) == Status.getStatus("finished"))
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 83)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 3)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 1)

    def test_empty(self):
        """ Test empty file """
        jobId = 10
        self.response = self.validateJob(jobId)

        self.waitOnJob(10, "invalid")
        if JobTests.USE_THREADS:
            assert(self.response.status_code == 200)
        else:
            assert(self.response.status_code == 400)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        if not JobTests.USE_THREADS:
            assert(self.response.json()["message"] == "CSV file must have a header")
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)
        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("single_row_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_missing_header(self):
        """ Test missing header in first row """
        jobId = 11
        self.response = self.validateJob(jobId)

        self.waitOnJob(11, "invalid")
        if JobTests.USE_THREADS:
            assert(self.response.status_code == 200)
        else:
            assert(self.response.status_code == 400)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)

        if not JobTests.USE_THREADS:
            assert(self.response.json()["message"] == "Header : header 5 is required")
        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("missing_header_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_bad_header(self):
        """ Test bad header value in first row """
        jobId = 12

        self.response = self.validateJob(jobId)
        if JobTests.USE_THREADS:
            assert(self.response.status_code == 200)
        else:
            assert(self.response.status_code == 400)
        self.waitOnJob(12, "invalid")
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)

        if not JobTests.USE_THREADS:
            assert(self.response.json()["message"] == "Header : walrus not in CSV schema")
        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("bad_header_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_many_rows(self):
        """ Test many rows """
        if not self.INCLUDE_LONG_TESTS:
            # Don't do this test when skipping long tests
            return
        jobId = 13
        self.response = self.validateJob(jobId)
        self.waitOnJob(13, "finished")
        assert(self.response.status_code == 200)
        if(self.response.status_code != 200):
            print(self.response.status_code)
            print(self.response.json()["errorType"])
            print(self.response.json()["message"])
            print(self.response.json()["trace"])
            print(self.response.json()["wrappedType"])
            print(self.response.json()["wrappedMessage"])
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 37)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 22380)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_odd_characters(self):
        """ Test potentially problematic characters """
        jobId = 14
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "finished")
        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        # Check that job is correctly marked as finished
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 136)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 5)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 2)

    def test_bad_id_job(self):
        """ Test job ID not found in job status table """
        jobId = 2001
        self.response = self.validateJob(jobId)
        assert(self.response.status_code == 400)
        self.assertHeader(self.response)
        assert(self.response.json()["message"] == "Job ID not found in job_status table")
        assert(self.jobTracker.getReportPath(jobId) == False)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("job_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_prereq_job(self):
        """ Test job with prerequisites finished """
        jobId = 7
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "finished")
        assert(self.response.status_code == 200)
        self.assertHeader(self.response)
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == 37)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == True)
        assert(self.stagingDb.countRows(tableName) == 4)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("complete"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_bad_prereq_job(self):
        """ Test job with unfinished prerequisites """
        jobId = 3
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "ready")
        assert(self.response.status_code == 400)
        self.assertHeader(self.response)
        assert(self.response.json()["message"] == "Prerequisites incomplete, job cannot be started")
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("job_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def test_bad_type_job(self):
        """ Test job with wrong type """
        jobId = 4
        self.response = self.validateJob(jobId)
        self.waitOnJob(jobId, "ready")
        assert(self.response.status_code == 400)
        self.assertHeader(self.response)
        assert(self.response.json()["message"] == "Wrong type of job for this service")
        assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)

        tableName = self.response.json()["table"]
        assert(self.stagingDb.tableExists(tableName) == False)
        assert(self.stagingDb.countRows(tableName) == 0)
        errorInterface = InterfaceHolder.ERROR
        assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("job_error"))
        assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    # TODO uncomment this unit test once jobs are labeled as ready
    # def test_finished_job(self):
        # """ Test job that is already finished """
        # jobId = 5
        # self.response = self.validateJob(jobId)
        # assert(self.response.status_code == 400)
        # self.assertHeader(self.response)
        # assert(self.response.json()["message"] == "Job is not ready")
        # assert(s3UrlHandler.getFileSize(self.jobTracker.getReportPath(jobId)) == False)

        # tableName = self.response.json()["table"]
        # assert(self.stagingDb.tableExists(tableName) == False)
        # assert(self.stagingDb.countRows(tableName) == 0)
        # self.dropTables(tableName)
        # errorInterface = InterfaceHolder.ERROR
        # assert(errorInterface.checkStatusByJobId(jobId) == errorModels.Status.getStatus("job_error"))
        # assert(errorInterface.checkNumberOfErrorsByJobId(jobId) == 0)

    def assertHeader(self, response):
        """ Assert that content type header exists and is json """
        assert("Content-Type" in response.headers)
        assert(response.headers["Content-Type"] == "application/json")

    def waitOnJob(self, jobId, status):
        currentID = Status.getStatus("running")
        targetStatus = Status.getStatus(status)
        if JobTests.USE_THREADS:
            while self.jobTracker.getStatus(jobId) == currentID:
                time.sleep(1)
            assert(targetStatus == self.jobTracker.getStatus(jobId))
        else:
            assert(targetStatus == self.jobTracker.getStatus(jobId))
            return

    def validateJob(self, jobId):
        """ Send request to validate specified job """
        if JobTests.USE_THREADS:
            url = "/validate_threaded/"
        else:
            url = "/validate/"

        return requests.request(method="POST", url=self.BASE_URL + url, data=self.jobJson(jobId), headers=self.JSON_HEADER)

    def setUp(self):
        self.jobTracker = InterfaceHolder.JOB_TRACKER
        self.errorInterface = InterfaceHolder.ERROR

    def tearDown(self):
        try:
            self.dropTables(self.response.json()["table"])
        except AttributeError:
            # Table not specified, generally this means the job didn't run
            pass

    def dropTables(self, table):
        if self.DROP_TABLES:
            stagingDb = InterfaceHolder.STAGING
            stagingDb.dropTable(table)
            return True
        else:
            return False

    def jobJson(self, jobId):
        """ Create JSON to hold jobId """
        return '{"job_id":'+str(jobId)+'}'
