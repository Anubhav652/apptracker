import requests_cache
import requests

from settings import Settings
from time import time
from joblist_listing import JobListing
from bs4 import BeautifulSoup
from copy import deepcopy

import helpers

# Cooldown protection for ListingRetriever.get
requests_cache.install_cache(
    'listing_cache',
    use_cache_dir=True,
    expire_after=60,
    stale_if_error=True
)

class ListingRetriever:
    def __init__(self):
        self.job_listings : dict[str, dict[str, list[JobListing]]] = {}
        # self.job_listings[ COMPANY NAME ][ JOB TITLE ] = list of job listings corresponding to this.
        self.last_retrieval_time : int = 0

    def get(self, force : bool = False) -> dict[str, dict[str, list[JobListing]]]:
        """Gets job listing dictionary from predefined GitHub job listings as given in settings.py. If a request was made in the past minute, sends the same data to avoid getting blocked.

            Args:
                force (bool): If true, skips the 1 minute cooldown between data refresh. By default, this is false.

            Returns:
                A dictionary with key as job provider (e.g Ouckah & CS Careers) and value as all job listings of the form JobListing.
        """
        self.last_retrieval_time = time()

        # Last company to check for sublistings
        last_company = ""
        for provider, url in Settings.JOB_LISTING_LINKS.items():
            if force:
                with requests_cache.disabled():
                    r = requests.get(url)
            else:
                r = requests.get(url)

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

                company_name = helpers.replace_md_links(company_name, lambda _ : "") # Removes all markdown essentially.

                last_company = company_name

                # Parse URL
                if listing_data[4] == "🔒":
                    job_url = Settings.JOB_LISTINGS_ACTUAL_LINKS[provider]
                else:
                    try:
                        parsed_html = BeautifulSoup(listing_data[4], "lxml")
                        job_url = parsed_html.find("a")["href"]
                        job_url = job_url.replace("?utm_source=Simplify&ref=Simplify", "")
                        job_url = job_url.replace("&utm_source=Simplify&ref=Simplify", "")
                        job_url = job_url.replace("www.", "")
                    except TypeError:
                        # if it ever errors, exit and print the listing data which it error'd on. Should never happen.
                        print(listing_data)
                        exit()

                job_title = listing_data[2].encode('ascii', 'ignore').decode('ascii')
                job_location = listing_data[3].replace("</br>", " | ").replace("<details><summary>", "").replace("</summary>", " ").replace("</details>", "")

                if not company_name in self.job_listings:
                    self.job_listings[company_name] = {}

                if not job_title in self.job_listings[company_name]:
                    self.job_listings[company_name][job_title] = []
                
                found = False
                for lsting in self.job_listings[company_name][job_title]:
                    if lsting.location == job_location:
                        found = True
                        break
                
                # duplicate listing
                if found:
                    continue

                self.job_listings[company_name][job_title].append(
                    JobListing(
                        company_name = company_name,
                        job_title = job_title,
                        location = job_location,
                        url = job_url,
                        source = provider
                    )
                )

        return deepcopy(self.job_listings) # Safe-guard just in case.

if __name__ == "__main__":
    test = ListingRetriever()
    print(test.get())
