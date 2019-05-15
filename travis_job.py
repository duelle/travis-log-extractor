import os


class TravisJob:
    """Data storage for one TravisTorrent Job"""

    def __init__(self, build_number, commit_hash, job_id):
        self.__build_number = build_number
        self.__commit_hash = commit_hash
        self.__job_id = job_id

        # Initialize all values with None resp. with 0
        self.__startup_duration = None
        self.__worker_hostname = None
        self.__worker_version = None
        self.__worker_instance = None
        self.__os_dist_id = None
        self.__os_dist_release = None
        self.__os_description = None
        self.__using_worker_header = None
        self.__travis_fold_worker_info = False
        self.__travis_fold_system_info = False
        self.__travis_fold_count = 0
        self.__step_first_start = None
        self.__step_last_end = None
        self.__duration_aggregated_timestamp = None
        self.__duration_diff_timestamp = None


    @property
    def build_number(self):
        return self.__build_number

    @property
    def commit_hash(self):
        return self.__commit_hash

    @property
    def job_id(self):
        return self.__job_id

    def assign_properties(self,
                          startup_duration,
                          worker_hostname,
                          worker_version,
                          worker_instance,
                          os_dist_id,
                          os_dist_release,
                          os_description,
                          using_worker_header,
                          travis_fold_worker_info,
                          travis_fold_system_info,
                          travis_fold_count,
                          step_first_start,
                          step_last_end,
                          duration_aggregated_timestamp,
                          duration_diff_timestamp
                          ):
        self.__startup_duration = startup_duration
        self.__worker_hostname = worker_hostname
        self.__worker_version = worker_version
        self.__worker_instance = worker_instance
        self.__os_dist_id = os_dist_id
        self.__os_dist_release = os_dist_release
        self.__os_description = os_description
        self.__using_worker_header = using_worker_header
        self.__travis_fold_worker_info = travis_fold_worker_info
        self.__travis_fold_system_info = travis_fold_system_info
        self.__travis_fold_count = travis_fold_count
        self.__step_first_start = step_first_start
        self.__step_last_end = step_last_end
        self.__duration_aggregated_timestamp = duration_aggregated_timestamp
        self.__duration_diff_timestamp = duration_diff_timestamp
