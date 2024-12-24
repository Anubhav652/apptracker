from apptracker.trackers.trackerabc import TrackerABC
from apptracker.trackers.joblisting import JobListing
import requests_cache
import apptracker.trackers.tracker_settings as tracker_settings
import apptracker.trackers.helpers as helpers
import traceback

class NorthwesternFintech(TrackerABC):
    """Tracks Northwestern Fintech Club's Quant Summer 2025 Internships"""
    ID_TO_ROLE_NAME_MATCH = {
        3: "Software Engineer Intern",
        4: "Quantitative Researcher Intern",
        5: "Quantitative Trader Intern"
    }

    def __init__(self, session: requests_cache.CachedSession):
        super().__init__(session)
        
        self.provider_name = "Northwestern Fintech Club"
        self.raw_url = tracker_settings.JOB_LISTING_LINKS[self.provider_name]
        self.display_url = tracker_settings.JOB_LISTINGS_ACTUAL_LINKS[self.provider_name]

    def get(self, force : bool = True) -> list[JobListing]:
        """Gets job listing dictionary from the Northwestern Fintech Club's Quant Summer 2025 tracker.

            Args:
                force (bool): If true, skips any data refresh cooldown. By default, this is false.

            Returns:
                Returns a list of all job listings associated with this tracker.
        """
        # Last company to check for sublistings
        if force:
            with requests_cache.disabled():
                r = self.session.get(self.raw_url)
        else:
            r = self.session.get(self.raw_url)

        job_listings : list[JobListing] = []
        data_started = False
        for line in r.text.splitlines():
            # First, find where the table starts.
            if not data_started:
                if not line.startswith("| Company| Location|SWE|QR|QT|Status| Notes|"):
                    continue

                data_started = True
                continue

            # Skip away any empty lines.
            if line.strip() == "":
                continue
            
            # Get data nicely and make sure to remove all spaces through strip().
            listing_data = [x.strip() for x in line.split("|")]

            company_name = listing_data[1]
            # Remove links
            company_name = helpers.replace_md_links(company_name, lambda _ : "")

            for id, job_title in NorthwesternFintech.ID_TO_ROLE_NAME_MATCH.items():
                if not "✅" in listing_data[id]:
                    continue

                try:
                    job_url = helpers.find_md_links(listing_data[id])['regular'][0][1]
                    job_url = job_url.replace("www.", "")

                    job_location = listing_data[2]

                    job_listings.append(
                        JobListing(
                            company_name = company_name,
                            job_title = job_title,
                            location = job_location,
                            url = job_url,
                            source = self.provider_name
                        )
                    )
                except Exception:
                    print(traceback.format_exc())
                    continue

        return job_listings