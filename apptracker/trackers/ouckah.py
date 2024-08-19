from apptracker.trackers.trackerabc import TrackerABC
from apptracker.trackers.joblisting import JobListing
import requests_cache
import apptracker.trackers.tracker_settings as tracker_settings
from bs4 import BeautifulSoup

class OuckahTracker(TrackerABC):
    """Tracks Ouckah & CS Careers"""
    def __init__(self, session: requests_cache.CachedSession):
        super().__init__(session)
        
        self.provider_name = "Ouckah & CS Careers"
        self.raw_url = tracker_settings.JOB_LISTING_LINKS[self.provider_name]
        self.display_url = tracker_settings.JOB_LISTINGS_ACTUAL_LINKS[self.provider_name]

    def get(self, force : bool = True) -> list[JobListing]:
        """Gets job listing dictionary from the Ouckah & CS Careers tracker.

            Args:
                force (bool): If true, skips any data refresh cooldown. By default, this is false.

            Returns:
                Returns a list of all job listings associated with this tracker.
        """
        # Last company to check for sublistings
        last_company = ""
        if force:
            with requests_cache.disabled():
                r = self.session.get(self.raw_url)
        else:
            r = self.session.get(self.raw_url)

        job_listings : list[JobListing] = []
        data_started = False
        for line in r.text.splitlines():
            # First, find where the table starts.
            # The current GitHub links make this very easy with "TABLE_BEGIN" and "TABLE_END" in the line denoting start and end of table in comments.
            if not data_started:
                if not "TABLE_START" in line:
                    continue

                data_started = True
                continue

            if "TABLE_END" in line:
                break

            # Skip away any empty lines.
            if line.strip() == "":
                continue
            
            # Get data nicely and make sure to remove all spaces through strip().
            listing_data = [x.strip() for x in line.split("|")]

            company_name = listing_data[1]
            # Skip some filler rows (heading rows)
            if company_name == "Company" and listing_data[2] == "Role":
                continue
            
            if company_name == "-------":
                continue
            
            # Check for sublisting
            if company_name == "↳":
                company_name = last_company

            last_company = company_name

            # Parse URL
            if listing_data[4] == "🔒":
                job_url = self.display_url
            else:
                try:
                    # Job Listings are inside <a href>, so we parse reliably using BeautifulSoup4.
                    parsed_html = BeautifulSoup(listing_data[4], "lxml")
                    job_url = parsed_html.find("a")["href"]

                    # The below things make it easier to get a more consistent URL for URL matching purposes (i.e checking duplicate job listings.)
                    job_url = job_url.replace("www.", "")
                except TypeError:
                    # if it ever errors, exit and print the listing data which it error'd on. Should never happen.
                    print(listing_data)
                    exit()

            # The below removes all unnecessary icons from a job title.
            job_title = listing_data[2].encode('ascii', 'ignore').decode('ascii')
            # Make job location into a consistent form (when there are multiple job locations for the same listing)
            job_location = listing_data[3].replace("</br>", " | ").replace("<details><summary>", "").replace("</summary>", " ").replace("</details>", "")

            job_listings.append(
                JobListing(
                    company_name = company_name,
                    job_title = job_title,
                    location = job_location,
                    url = job_url,
                    source = self.provider_name
                )
            )

        return job_listings