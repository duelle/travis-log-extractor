#!/usr/bin/env python

from curses.ascii import isprint
from datetime import timedelta, datetime
import logging
import re
import os

from travis_job import TravisJob

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_file_formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
log_file_handler = logging.FileHandler('job_helper.log')
log_file_handler.setLevel(logging.DEBUG)
log_file_handler.setFormatter(log_file_formatter)
logger.addHandler(log_file_handler)

log_stream_formatter = logging.Formatter('%(asctime)s:%(message)s')
log_stream_handler = logging.StreamHandler()
log_stream_handler.setLevel(logging.INFO)
log_stream_handler.setFormatter(log_stream_formatter)
logger.addHandler(log_stream_handler)

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
    out = "".join(filter(isprint,out))

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
        log_file_name = os.path.splitext(os.path.basename(log_file))[0]
        log_file_split = log_file_name.split('_')

        build_number = int(log_file_split[0])
        commit_hash = str(log_file_split[1])
        job_id = int(log_file_split[2])

        return TravisJob(build_number, commit_hash, job_id)
    else:
        raise Exception("File name format error in {}. File name contains different segments.".format(log_file))


def __convert_timestamp_to_datetime(timestamp):
    """
    Converts a travis_time timestamp to a DateTime string
    :param timestamp: Timestamp to be converted
    :return: Timestamp in DateTime format
    """

    # Timestamp of January 1st 2018
    upper_time_limit = int(1514761200)

    if not timestamp == 0 and timestamp is not None:
        # Scale down resolution to seconds
        ts = int(timestamp)/1000000000

        if ts > upper_time_limit:
            return None
        else:
            return datetime.utcfromtimestamp(ts).replace(microsecond=0)
    else:
        return None


def parse_job_log_file(log_file_path, parser_error_logger):

    job = None

    if os.path.isfile(log_file_path):

        # Initialization
        job_build_id = None
        job_startup_duration = None
        job_worker_hostname = None
        job_worker_version = None
        job_worker_instance = None
        job_os_dist_id = None
        job_os_dist_release = None
        job_os_description = None
        job_build_language = None
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

            first_line = True
            os_details_coming = False
            worker_details_coming = False
            build_system_details_coming = False

            with open(log_file_path, "r") as log:
                for raw_line in log:
                    line = __strip_meta_characters(raw_line)
                    lower_line = line.lower()

                    if lower_line == '':
                        continue

                    # Worker Header
                    if first_line and lower_line.startswith("using worker"):
                        job_using_worker_header = True
                        job_worker_hostname = line.split(' ')[2]
                        first_line = False

                    # Fold count
                    elif lower_line.startswith("travis_fold:start"):
                        job_travis_fold_count += 1

                    # OS Info
                    elif lower_line.startswith("Operating System Details"):
                        os_details_coming = True
                        worker_details_coming = False
                        build_system_details_coming = False

                    # Worker Info
                    elif lower_line.startswith("worker information"):
                        os_details_coming = False
                        worker_details_coming = True

                    # Build System Info
                    elif lower_line.startswith("build system information"):
                        build_system_details_coming = True

                    # System Info
                    elif lower_line.startswith("travis_fold:start:system_info"):
                        job_travis_fold_system_info = True

                    # End of System Info
                    elif lower_line.startswith("travis_fold:end:system_info"):
                        os_details_coming = False

                    # Worker Info
                    elif lower_line.startswith("travis_fold:start:worker_info"):
                        job_travis_fold_worker_info = True

                    # End of Worker Info
                    elif lower_line.startswith("travis_fold:end:worker_info"):
                        worker_details_coming = False

                    # Startup time
                    elif lower_line.startswith("startup:"):
                        job_startup_duration = \
                            int(__extract_startup_duration(line.split(' ')[1]))

                    elif lower_line.startswith("travis_time:end"):
                        colon_split = line.split(':')
                        valid_time_end = False

                        # Valid entries contain all three keywords
                        if 'start' and 'finish' and 'duration' in lower_line:

                            # Some entries contain 3 and some 4 colons
                            if len(colon_split) == 4:
                                timings = line.split(':')[3]
                                valid_time_end = True

                            elif len(colon_split) == 3:
                                timings = line.split(',')[1]
                                valid_time_end = True

                        if not valid_time_end:
                            parser_error_logger.warning("Invalid travis_time:end line in " + log_file_path + "\n> " + line)
                        else:
                            start_timings = timings.split(',')[0]
                            start_value_x = start_timings.split('=')[1]
                            if start_value_x.isdigit():
                                start_value = int(start_value_x)

                            finish_timings = timings.split(',')[1]
                            finish_value_x = finish_timings.split('=')[1]
                            if finish_value_x.isdigit():
                                finish_value = int(finish_value_x)

                            duration_timings = timings.split(',')[2]
                            duration_value_x = duration_timings.split('=')[1]
                            if duration_value_x.isdigit():
                                duration_value = int(duration_value_x)

                                # Milliseconds
                                duration_value_ms = duration_value / 1000000

                                if job_duration_aggregated_timestamp is None:
                                    job_duration_aggregated_timestamp = duration_value_ms
                                else:
                                    job_duration_aggregated_timestamp += duration_value_ms

                            if job_step_first_start is None:
                                job_step_first_start = __convert_timestamp_to_datetime(start_value)

                            job_step_last_end = __convert_timestamp_to_datetime(finish_value)

                            if job_step_first_start is None or job_step_last_end is None:
                                job_duration_diff_timestamp = None
                            else:
                                job_duration_diff_timestamp = (job_step_last_end - job_step_first_start).total_seconds()

                    # System/OS Details
                    if os_details_coming:
                        if lower_line.startswith("description:"):
                            job_os_description = line.split(":")[1]
                        elif lower_line.startswith("distributor id"):
                            job_os_dist_id = line.split(":")[1]
                        elif lower_line.startswith("release:"):
                            job_os_dist_release = line.split(":")[1]
                        elif lower_line.startswith("build language") and job_build_language is None:
                            job_build_language = line.split(":")[1]

                    # Worker Details
                    if worker_details_coming:
                        if lower_line.startswith("hostname:"):
                            job_worker_hostname = line.split(':')[1]

                        if lower_line.startswith("version:"):
                            job_worker_version = " ".join(line.split(' ')[1:])

                        if lower_line.startswith("instance:"):
                            job_worker_instance = line.split(' ')[1]

                    # Build System Details
                    if build_system_details_coming:
                        if lower_line.startswith("build id:"):
                            job_build_id = line.split(':')[1]
                        if lower_line.startswith("build language:") and job_build_language is None:
                            job_build_language = line.split(':')[1]

                job.assign_properties(
                                      build_id=job_build_id,
                                      startup_duration=job_startup_duration,
                                      worker_hostname=job_worker_hostname,
                                      worker_version=job_worker_version,
                                      worker_instance=job_worker_instance,
                                      os_dist_id=job_os_dist_id,
                                      os_dist_release=job_os_dist_release,
                                      os_description=job_os_description,
                                      build_language=job_build_language,
                                      using_worker_header=job_using_worker_header,
                                      travis_fold_worker_info=job_travis_fold_worker_info,
                                      travis_fold_system_info=job_travis_fold_system_info,
                                      travis_fold_count=job_travis_fold_count,
                                      step_first_start=job_step_first_start,
                                      step_last_end=job_step_last_end,
                                      duration_aggregated_timestamp=job_duration_aggregated_timestamp,
                                      duration_diff_timestamp=job_duration_diff_timestamp
                                      )

        except Exception as e:
            parser_error_logger.warning(e)

        return job
