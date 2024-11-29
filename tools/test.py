import cups
import time


def perform_test_print(mode):
    try:
        # Validate mode
        if mode not in ['normal', 'shaded']:
            return 'Invalid mode, must be "normal" or "shaded"', 400

        # Define the file to print based on the mode
        if mode == 'normal':
            file_to_print = 'testPdfs/TestPage.pdf'
        elif mode == 'shaded':
            file_to_print = 'testPdfs/ShadedTestPage.pdf'

        # Establish connection to CUPS and get available printers
        conn = cups.Connection()
        printers = conn.getPrinters()

        if len(printers) == 0:
            return 'No printers found', 500

        # Select the first available printer
        selected_printer = list(printers.keys())[0]

        # Define the print options
        options = {'media': 'A4'}

        # Send the file to the printer
        job_info = conn.printFile(selected_printer, file_to_print, "Test Print", options)
        job_error = [6, 7, 8]
        # Wait for the job to complete (CUPS job state 9 = "completed")
        while conn.getJobAttributes(job_info)["job-state"] != 9:
            if (conn.getJobAttributes(job_info)["job-state"] in job_error):
                print("error is", conn.getJobAttributes(job_info))
                raise Exception("Print file failed", "Printer Error code = ", conn.getJobAttributes(job_info)["job-state"])
            print("Processing job")
            print("job status", conn.getJobAttributes(job_info))
            time.sleep(1)

        return 'Print job completed', 200

    except Exception as e:
        print("error is", str(e))
        return f'An unexpected error occurred: {str(e)}', 500
