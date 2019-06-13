#!/usr/bin/env python

from concurrent.futures import ProcessPoolExecutor, as_completed
import datetime
import getopt
import glob
import logging
# from multiprocessing import Process, Queue
import multiprocessing_logging
import os
import sys
import time

from travis_project import TravisProject
from travis_job import TravisJob
import travis_job_helper

# https://github.com/jruere/multiprocessing-logging
multiprocessing_logging.install_mp_handler()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_file_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s:%(message)s')
log_file_handler = logging.FileHandler('parser.log')
log_file_handler.setLevel(logging.DEBUG)
log_file_handler.setFormatter(log_file_formatter)
logger.addHandler(log_file_handler)

log_stream_formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(message)s')
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)
log_stream_handler.setFormatter(log_stream_formatter)
logger.addHandler(log_stream_handler)

csv_logger = logging.getLogger("travis_log")
csv_output_formatter = logging.Formatter('%(message)s')
csv_output_handler = logging.FileHandler('travis_log.csv')
csv_output_handler.setLevel(logging.INFO)
csv_output_handler.setFormatter(csv_output_formatter)
csv_logger.addHandler(csv_output_handler)

parsing_error_logger = logging.getLogger("parsing_errors")
parsing_error_formatter = logging.Formatter('%(message)s')
parsing_error_handler = logging.FileHandler('parsing_errors.log')
parsing_error_handler.setLevel(logging.WARNING)
parsing_error_handler.setFormatter(parsing_error_formatter)
parsing_error_logger.addHandler(parsing_error_handler)


def extract_project(project_folder_name):
    project_folder_name_split = project_folder_name.split('@')
    return TravisProject(project_folder_name_split[0], project_folder_name_split[1])


def process_project_folder(project_folder):

    start_time = time.process_time()

    log_files_processed = 0
    log_files_total = 0
    processing_duration = 0

    project_folder_name = ""

    if "@" in os.path.basename(project_folder):
        project_folder_name = os.path.basename(project_folder)
        project = extract_project(project_folder_name)

        logger.info("Started processing " + project_folder_name)

        log_file_list = [item for item in glob.glob(project_folder + os.sep + "*.log") if os.path.isfile(item)]
        log_files_total = len(log_file_list)

        jobs = []

        for log_file in log_file_list:
            job = travis_job_helper.parse_job_log_file(log_file, parsing_error_logger)

            if job is not None:
                jobs.append(job)
                log_files_processed += 1
            else:
                logger.warning("Result of parsing was None for: " + log_file)

        project.assign_jobs(jobs)

        with open(output_file + os.sep + project_folder_name + ".csv", "w") as csv_file:
            csv_file.writelines(project.get_as_csv())

        end_time = time.process_time()
        processing_duration = end_time - start_time

        logger.info("Done processing " + project_folder_name + " (" + str(log_files_processed) + '/'
                    + str(log_files_total) + ' ' + str(processing_duration) + ")")

    else:
        logger.warning('Given project folder does not match project folder format (containing @): "'
                       + project_folder + '"')

    if project_folder_name is "":
        logger.error("Parsing for folder " + project_folder + " failed.")

    return project_folder_name, log_files_processed, log_files_total, processing_duration


def process_input_folder(input_folder):
    start_time = time.time()

    projects_processed = 0
    project_count_total = 0
    log_file_count = 0
    logs_overall_processed = 0
    logs_overall = 0

    if os.path.isdir(input_folder):
        folder_list = [item for item in glob.glob(input_folder + os.sep + "*") if os.path.isdir(item)]
        project_count_total = len(folder_list)

        future_list = []

        with ProcessPoolExecutor(max_workers=8) as executor:
            for folder in folder_list:
                future_list.append(executor.submit(process_project_folder,folder))

        for f in future_list:
            project, log_files_processed, log_files_total, processing_duration = f.result()

            logs_overall_processed += log_files_processed
            logs_overall += log_files_total

            if log_files_processed > 0:
                logger.info(project + ": " + str(log_files_processed) + "/" + str(log_files_total)
                            + " (" + str(processing_duration) + ")")
                projects_processed += 1
            else:
                logger.error(project + ": No log files processed! (" + str(processing_duration) + ")")

        end_time = time.time()
        folder_processing_duration = end_time - start_time

        logger.info("Projects processed: " + str(projects_processed) + '/' + str(project_count_total))
        logger.info("Processing duration: " + str(folder_processing_duration) + " seconds")
        logger.info("Logs processed/total: " + str(logs_overall_processed) + "/" + str(logs_overall))

    else:
        logger.warning('Given folder does not exist or is not a folder: "' + input_folder + '"')


def main(argv):
    tool_name = "travis_log_parser.py"
    tool_params = " -i <input_folder> -o <output_folder>"
    usage_string = "Usage: " + tool_name + tool_params

    global output_file

    try:
        opts, args = getopt.getopt(argv, "hi:o:", ["infile=","outfile="])
    except getopt.GetoptError:
        print(usage_string)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(usage_string)
            sys.exit()
        elif opt in ("-i", "--infile"):
            input_file = arg.rstrip('/')
        elif opt in ("-o", "--outfile"):
            output_file = arg.rstrip('/')

    if input_file is None or output_file is None:
        print(usage_string)
        sys.exit()

    logger.info('Input file is "' + input_file + '"')
    logger.info('Output file is "' + output_file + '"')

    process_input_folder(input_file)


if __name__ == "__main__":
    main(sys.argv[1:])
