import cups

def cancel_all_jobs():
    try:
        # Connect to the CUPS server
        conn = cups.Connection()

        # Get a list of all printers
        printers = conn.getPrinters()

        if not printers:
            print("No printers found.")
            return

        # Get the list of all jobs (across all printers)
        jobs = conn.getJobs()

        if not jobs:
            print("No jobs found.")
            return

        # Cancel each job
        for job_id, job_info in jobs.items():
            printer_name = job_info['printer-uri-supported']
            print(f"Cancelling job {job_id} on printer {printer_name}")
            conn.cancelJob(job_id)

        print("All jobs have been cancelled.")

    except Exception as e:
        print(f"Error cancelling jobs: {e}")
