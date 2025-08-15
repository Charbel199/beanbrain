from enum import Enum

class Frequency(str, Enum):
    daily = "DAILY"
    weekly = "WEEKLY"
    monthly = "MONTHLY"      # same day every month
    yearly = "YEARLY"        # same month & day every year
