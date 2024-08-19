from abc import ABC, abstractmethod
from apptracker.trackers.joblisting import JobListing
import requests_cache

class TrackerABC(ABC):
    def __init__(self, session : requests_cache.CachedSession):
        self.session = session

    @abstractmethod
    def get(self, force : bool = False) -> list[JobListing]:
        """Gets job listing dictionary from the tracker.

            Args:
                force (bool): If true, skips any data refresh cooldown. By default, this is false.

            Returns:
                Returns a list of all job listings associated with this tracker.
        """
        pass

