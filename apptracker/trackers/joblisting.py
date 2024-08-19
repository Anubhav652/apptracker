from dataclasses import dataclass

@dataclass
class JobListing:
    company_name : str
    job_title : str
    location : str
    url : str
    source : str
