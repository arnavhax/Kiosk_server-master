import base64
import io
import os
import math
import cups
import time
from PyPDF2 import PdfReader, PdfWriter
from tools.deduct_pages import deduct_pages
from tools.resume_printer import enable_all_printers

def process_print_job(files):
    enable_all_printers()
    for file in files:
        try:
            # Extract job details
            blob_data = file['blob']
            double_page = file['selectedOption']
            copies = file['numCopies']
            selected_pages = file['selectedPages']

            # Deduct pages logic
            if double_page == 'double':
                job_pages = math.ceil(len(selected_pages) / 2)
            else:
                job_pages = len(selected_pages)
            total_pages = job_pages * copies

            # Deduct pages before processing
            code = deduct_pages(total_pages)
            if code != 200:
                raise ExceptionWithCode("Failed to deduct pages from user balance.", 101)

            # Decode and process PDF
            pdf_file = base64.b64decode(blob_data)
            pdf_reader = PdfReader(io.BytesIO(pdf_file))

            output = PdfWriter()
            for page_number in range(len(pdf_reader.pages)):
                if page_number + 1 in selected_pages:
                    output.add_page(pdf_reader.pages[page_number])

            output_stream = io.BytesIO()
            output.write(output_stream)
            output_stream.seek(0)
            pdf_binary_data = output_stream.getvalue()

            # Write the processed PDF to a temporary file
            temp = "temp.pdf"
            with open(temp, 'wb') as f:
                f.write(pdf_binary_data)

            # Check if the file exists and ends with .pdf
            if temp and temp.endswith('.pdf'):
                conn = cups.Connection()
                printers = conn.getPrinters()
                if not printers:
                    raise ExceptionWithCode("No printers found on the CUPS server.", 102)

                # Select the first available printer
                selected_printer = list(printers.keys())[0]

                # Set printer options
                options = {
                    'multiple-document-handling': 'separate-documents-collated-copies' if copies > 1 else 'single_document',
                    'sides': 'two-sided-long-edge' if double_page == 'double' else 'one-sided',
                    'copies': str(copies)
                }

                # Submit the print job
                job_id = conn.printFile(selected_printer, temp, "", options)

                # Monitor the print job
                while True:
                    job_attributes = conn.getJobAttributes(job_id)
                    job_state = job_attributes["job-state"]
                    job_state_reasons = job_attributes.get("job-printer-state-reasons", [])

                    # Critical printer states to monitor
                    CRITICAL_JOB_STATES = [6, 7, 8]  # Job canceled, aborted, or completed with errors
                    if job_state in CRITICAL_JOB_STATES:
                        conn.cancelJob(job_id)
                        raise ExceptionWithCode(f"Job failed with state {job_state}: {job_state_reasons}", 103)

                    # Specific printer errors and warnings
                    for reason in job_state_reasons:
                        if reason in [
                            "media-empty-error", "media-jam-error", "toner-empty-error", "cover-open-error",
                            "door-open-error", "fuser-error", "overheating-error", "ink-empty-error", 
                            "wrong-media-error", "sensor-malfunction"
                        ]:
                            conn.cancelJob(job_id)
                            raise ExceptionWithCode(f"Printer issue detected: {reason}", 104)

                        # Log warnings for non-critical issues
                        if reason in ["low-ink-warning", "toner-low-warning"]:
                            print(f"Warning: {reason}. Consider replenishing supplies.")

                    # Environmental factors
                    if "overheating-warning" in job_state_reasons:
                        print("Warning: Printer is overheating. Job might pause.")
                    
                    # Handle successful job completion
                    if job_state == 9:  # Job is completed successfully
                        print("Job completed successfully.")
                        break

                    # Wait before checking the status again
                    time.sleep(1)

                # Remove the temporary file
                os.remove(temp)

            return {'Current Job': file['name'], 'completed': 'no'}

        except ExceptionWithCode as e:
            print(f"Error processing job: {e.message} (Code: {e.code})")
            return {'error': e.message, 'code': e.code}

    return {'completed': 'yes'}


class ExceptionWithCode(Exception):
    """Custom exception class for handling errors with specific error codes."""
    def __init__(self, message, code):
        super().__init__(message)
        self.message = message
        self.code = code

    def to_dict(self):
        """Convert the exception details to a dictionary."""
        return {'code': self.code, 'message': self.message}



