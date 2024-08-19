import threading
import yarl

import apptracker.trackers.tracker_settings as TrackerSettings
from apptracker.sheets import Sheets, JobStatus
from apptracker.tracker import Tracker, JobListing

# Connects job listing and sheets.
class Backend:
    def __init__(self):
        self.sheets = Sheets()
        self.tracker = Tracker()
        self.tracker_list : dict[str, dict[str, list[JobListing]]] = {}
        # self.tracker_list[ COMPANY NAME ][ JOB TITLE ] = list of job listings corresponding to this
    
        self.to_display_job_lsting : list[JobListing] = []
        self.urls_done : list[yarl.URL] = []
        self.jobs_applied_to_count : int = 0

    def add_application(self, event : threading.Event, type : str, company_name : str, job_title : str, job_location : str, url : str):
        if type == "Applied":
            self.sheets.add_applied(company_name, job_title, job_location, url)
            self.jobs_applied_to_count += 1
        elif type == "Discarded":
            self.sheets.add_discarded(company_name, job_title, job_location, url)
    
        for lsting in self.to_display_job_lsting:
            if lsting.company_name == company_name and lsting.job_title == job_title and lsting.location == job_location:
                self.to_display_job_lsting.remove(lsting)
                break

        event.set()

    def load(self, event : threading.Event):
        self.tracker_list = self.tracker.get()
        self.sheets.reload()
        self.to_display_job_lsting.clear()
        self.urls_done.clear()

        # Remove all applied to and discarded applications for final listing.
        for company_name, _data in self.tracker_list.items():
            for job_title, job_listings in _data.items():
                for lsting in job_listings:
                    if self.sheets.get_job_status(company_name, job_title, lsting.location, lsting.url) != JobStatus.NOT_APPLIED:
                        continue
                    
                    if lsting.url not in TrackerSettings.JOB_LISTINGS_ACTUAL_LINKS.values():
                        yarl_url = yarl.URL(lsting.url)

                        found = False
                        for url in self.urls_done:
                            if url == yarl_url:
                                found = True
                                break

                        if found:
                            print(f"Found URL: {lsting.url}")
                            continue

                        self.urls_done.append(yarl_url)
                    
                    self.to_display_job_lsting.append(lsting)
        
        self.jobs_applied_to_count = self.sheets.applied_last_row_id
        # We are done now. Mark event as completed.
        event.set()