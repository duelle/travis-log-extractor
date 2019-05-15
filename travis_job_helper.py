#!/usr/bin/env python

from curses.ascii import isprint
from datetime import timedelta, datetime
import re
import os

from travis_job import TravisJob

sanitize1 = re.compile(r'\x1B\[(([0-9]{1,2})?(;)?([0-9]{1,2})?)?[m,K,H,f,J]')
sanitize2 = re.compile(r'^M\n')
startup_duration_regex = \
    re.compile(r'((?P<hours>\d+?)h)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)?)(.\d+)?s')


def __strip_meta_characters(log_string):
    """
    Removes color codes and other irrelevant meta-characters
    :param log_string: Log string
    :return: String without meta-characters
    """

    out = log_string
    out = sanitize1.sub('', out)
    out = sanitize2.sub('', out)
    out = "".join(filter(isprint(out)))

    return out


def __extract_startup_duration(duration_string):
    """
    Extracts total duration in seconds from duration string.
    """

    parts = startup_duration_regex.match(duration_string)
    if not parts:
        return
    parts = parts.groupdict()
    time_params = {}

    # Go through all parts and add up the second representations.
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params).seconds


def __extract_job_base(log_file):
    """
    Extracts base information from the log_file name
    :param log_file: Log file for the job
    :return: TravisTorrentJob object
    """

    if '_' in log_file:
        log_file_name = os.path.splitext(log_file)[0]
        log_file_split = log_file_name.split('_')

        build_number = int(log_file_split[0])
        commit_hash = str(log_file_split[1])
        job_id = int(log_file_split[2])

        return TravisJob(build_number, commit_hash, job_id)
    else:
        raise Exception("File name format error in {}. File name contains different segments."
              .format(log_file))


def parse_job_log_file(log_file_path):

    if os.path.isfile(log_file_path):

        job_startup_duration = None
        job_worker_hostname = None
        job_worker_version = None
        job_worker_instance = None
        job_os_dist_id = None
        job_os_dist_release = None
        job_os_description = None
        job_using_worker_header = None
        job_travis_fold_worker_info = False
        job_travis_fold_system_info = False
        job_travis_fold_count = 0
        job_step_first_start = None
        job_step_last_end = None
        job_duration_aggregated_timestamp = None
        job_duration_diff_timestamp = None

        try:
            job = __extract_job_base(log_file_path)

            first_line_read = False

            for line in log_file_path:
                stripped_line = __strip_meta_characters(line)

                # Worker Header
                if (not first_line_read) and stripped_line.startswith("Using worker"):
                    job_using_worker_header = True
                    job_worker_hostname = stripped_line.split(' ')[2]
                    first_line_read = True

                # Fold count
                if stripped_line.startswith("travis_fold:start"):
                    job_travis_fold_count += 1

                # System Info
                if stripped_line.startswith("travis_fold:start:system_info"):
                    job_travis_fold_system_info = True

                # Worker Info
                if stripped_line.startswith("travis_fold:start:worker_info"):
                    job_travis_fold_worker_info = True

                # Startup time
                if stripped_line.startswith("startup:"):
                    job_startup_duration = \
                        int(__extract_startup_duration(stripped_line.split(' ')[1]))

            job.assign_properties(job_startup_duration, job_worker_hostname, job_worker_version)

        except Exception as e:
            print("Exception: {}".format(e.args))
