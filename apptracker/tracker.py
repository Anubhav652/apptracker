import requests_cache

from copy import deepcopy

from apptracker.trackers.trackerabc import TrackerABC
from apptracker.trackers.joblisting import JobListing
from apptracker.trackers.ouckah import OuckahTracker
from apptracker.trackers.simplify import SimplifyTracker
import apptracker.trackers.tracker_settings as tracker_settings

class Tracker:
    def __init__(self):
        self.trackers : list[TrackerABC] = []
        self.job_listings : dict[str, dict[str, list[JobListing]]] = {}
        # self.job_listings[ COMPANY NAME ][ JOB TITLE ] = list of job listings corresponding to this.

        self.session = requests_cache.CachedSession('listing_cache',
            use_cache_dir=True,
            expire_after=60,
            stale_if_error=True
        )

        for tracker, is_enabled in tracker_settings.TRACKERS_ENABLED.items():
            if not is_enabled:
                continue

            match tracker:
                case "Ouckah & CS Careers":
                    self.trackers.append(OuckahTracker(self.session))

                case "Pitt CSC & Simplify":
                    self.trackers.append(SimplifyTracker(self.session))

                case _:
                    print(f"Tracker not found: {tracker}")

    def get(self, force : bool = False) -> dict[str, dict[str, list[JobListing]]]:
        """Gets job listing dictionary from predefined GitHub job listings as given in settings.py. If a request was made in the past minute, sends the same data to avoid getting blocked.

            Args:
                force (bool): If true, skips the 1 minute cooldown between data refresh. By default, this is false.

            Returns:
                dictionary[companyNamme, dictionary[jobTitle, list[JobListing]]]
        """

        for tracker in self.trackers:
            tracker_listing = tracker.get(force)

            for listing in tracker_listing:
                if not listing.company_name in self.job_listings:
                    self.job_listings[listing.company_name] = {}

                if not listing.job_title in self.job_listings[listing.company_name]:
                    self.job_listings[listing.company_name][listing.job_title] = []
                
                found = False

                # Check for duplicate listing by matching company name, job title, and location
                for duplicate_listing in self.job_listings[listing.company_name][listing.job_title]:
                    if listing.location == duplicate_listing.location:
                        found = True
                        break
                
                if found:
                    continue

                self.job_listings[listing.company_name][listing.job_title].append(listing)

        return deepcopy(self.job_listings) # Safe-guard just in case.