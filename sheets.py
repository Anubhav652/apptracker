import gspread
from settings import Settings
from sheet_row import SheetRow
from time import time
from enum import Enum
from typing import Optional

class JobStatus(Enum):
    NOT_APPLIED = 1
    APPLIED = 2
    DISCARDED = 3

class Sheets:
    def __init__(self):
        """Initializes the gspread objects used for making calls to Google Sheets. Loads data into self.applied and self.discarded. """
        self.gc = gspread.service_account(filename=Settings.KEY_FILE_PATH)
        self.sh = self.gc.open_by_key(Settings.SHEET_KEY)

        self.applied_ws = self.sh.worksheet("Applications")
        self.discarded_ws = self.sh.worksheet("Ignore")

        self.applied : dict[str, dict[str, list[SheetRow]]] = {}
        self.discarded : dict[str, dict[str, list[SheetRow]]] = {}
        # The structure of applied and discarded is as follows:
        # self.applied[ COMPANY NAME ][ JOB TITLE ] = list of job applications corresponding to this.
        self.applied_by_url : dict[str, list[SheetRow]] = {}
        self.discarded_by_url : dict[str, list[SheetRow]] = {}

        self.applied_last_row_id = 0
        self.discarded_last_row_id = 0

        self.last_reload_time = 0

    def _add_discarded_dict(self, row_id : int, company_name : str, job_title : str, job_location : str, url : str) -> None:
        """Handles adding a discarded application to the dictionary inside this class."""
        if not company_name in self.discarded:
            self.discarded[company_name] = {}
        
        if not job_title in self.discarded[company_name]:
            self.discarded[company_name][job_title] = []
        
        self.discarded[company_name][job_title].append(
            SheetRow(
                row_id,
                company_name,
                job_title,
                job_location,
                url
            )
        )

        if not url in self.discarded_by_url:
            self.discarded_by_url[url] = []
        
        self.discarded_by_url[url].append(
            SheetRow(
                row_id,
                company_name,
                job_title,
                job_location,
                url
            )
        )

    def _add_applied_dict(self, row_id : int, company_name : str, job_title : str, job_location : str, url : str) -> None:
        """Handles adding an "applied to" application to the dictionary inside this class."""
        if not company_name in self.applied:
            self.applied[company_name] = {}
        
        if not job_title in self.applied[company_name]:
            self.applied[company_name][job_title] = []

        self.applied[company_name][job_title].append(
            SheetRow(
                row_id,
                company_name,
                job_title,
                job_location,
                url
            )
        )

        if not url in self.applied_by_url:
            self.applied_by_url[url] = []
        
        self.applied_by_url[url].append(
            SheetRow(
                row_id,
                company_name,
                job_title,
                job_location,
                url
            )
        )
    
    def reload(self, force : bool = False) -> None:
        """Reloads data inside this class by fetching data from sheets. This ensures we are not out of sync. There is an inbuilt cooldown of 5 seconds which can be skipped by the force param.

            Args:
                force (bool): If true, skips the 5 second cooldown between reloads. By default, this is false.
        """
        # Enforce cooldown protection of 5 seconds.
        if not force:
            if (time() - self.last_reload_time) < 5:
                return

        self.last_reload_time = time()
    
        self.applied : dict[str, dict[str, list[SheetRow]]] = {}
        self.discarded : dict[str, dict[str, list[SheetRow]]] = {}
    
        self.applied_last_row_id = 0
        self.discarded_last_row_id = 0

        applied_values = self.applied_ws.get_all_values()
        for row_id, row in enumerate(applied_values):
            # row format: Job Name - Title - URL - Location
            self._add_applied_dict(row_id, row[0], row[1], row[3], row[2])
    
        self.applied_last_row_id = len(applied_values)

        discarded_values = self.discarded_ws.get_all_values()
        for row_id, row in enumerate(discarded_values):
            # row format: Job Name - Title - URL - Location
            self._add_discarded_dict(row_id, row[0], row[1], row[3], row[2])

        self.discarded_last_row_id = len(discarded_values)

    def add_applied(self, company_name : str, job_title : str, job_location : str, url : str) -> None:    
        """Adds in a "applied-to" application. Updates Google Sheets and internal dictionary (self.applied)."""
        row_id = self.applied_last_row_id + 1

        # Update Google Sheets
        cells = self.applied_ws.range(row_id, 1, row_id, 4)
        cells[0].value = company_name
        cells[1].value = job_title
        cells[2].value = url
        cells[3].value = job_location

        self.applied_ws.update_cells(cells, value_input_option = "USER_ENTERED")

        # Update our internal dictionary.
        self._add_applied_dict(row_id, company_name, job_title, job_location, url)

        # Ensure we keep the right count for row ID purposes for next added application.
        self.applied_last_row_id = row_id
    

    def add_discarded(self, company_name : str, job_title : str, job_location : str, url : str) -> None:
        """Adds in a discarded application. Updates Google Sheets and internal dictionary (self.applied)."""
        self.reload()

        row_id = self.discarded_last_row_id + 1
        
        # Update Google Sheets
        cells = self.discarded_ws.range(row_id, 1, row_id, 4)
        cells[0].value = company_name
        cells[1].value = job_title
        cells[2].value = url
        cells[3].value = job_location

        self.discarded_ws.update_cells(cells, value_input_option = "USER_ENTERED")

        # Update our internal dictionary.
        self._add_discarded_dict(row_id, company_name, job_title, job_location, url)
    
        # Ensure we keep the right count for row ID purposes for next added application.
        self.discarded_last_row_id = row_id
    
    def get_job_status(self, company_name : str, job_title : str, job_location : str, job_url : str) -> JobStatus:
        """Gets job status; for a job to match, there must be an exact company_name, job_title and job_location match. The URL is NOT used for job matching. Or one job URL matching."""
        # first, we do URL matching.
        if job_url not in Settings.JOB_LISTINGS_ACTUAL_LINKS.values():
            if job_url in self.applied_by_url:
                return JobStatus.APPLIED
            
            if job_url in self.discarded_by_url:
                return JobStatus.DISCARDED

        # Match the job in "applied-to" database.
        if company_name in self.applied:
            if job_title in self.applied[company_name]:
                for job in self.applied[company_name][job_title]:
                    if job.location == job_location:
                        return JobStatus.APPLIED
        
        # Match the job in "discarded" database.
        if company_name in self.discarded:
            if job_title in self.discarded[company_name]:
                for job in self.discarded[company_name][job_title]:
                    if job.location == job_location:
                        return JobStatus.DISCARDED

        # If it's in neither, default job status (it has not been applied to)
        return JobStatus.NOT_APPLIED