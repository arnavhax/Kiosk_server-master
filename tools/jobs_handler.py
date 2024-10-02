import json
import os

JOBS_FILE = os.path.join('data', 'jobs.json')

def load_jobs():
    """Load the jobs list from the jobs.json file."""
    if os.path.exists(JOBS_FILE):
        with open(JOBS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_jobs(jobs):
    """Save the jobs list to the jobs.json file."""
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f)
