from dataclasses import dataclass

@dataclass
class SheetRow:
    row_id : int
    company_name : str
    job_title : str
    location : str
    url : str