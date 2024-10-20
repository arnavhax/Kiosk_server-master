import base64
import io
import os
import math
import cups
import time
from PyPDF2 import PdfReader, PdfWriter
from tools.deduct_pages import deduct_pages

def process_print_job(files):
    for file in files:
        blob_data = file['blob']
        double_page = file['selectedOption']
        copies = file['numCopies']
        selected_pages = file['selectedPages']

        # Deducting pages logic
        if double_page == 'double':
            job_pages = math.ceil(int(len(selected_pages)) / 2)
        else:
            job_pages = int(len(selected_pages))
        total_pages = job_pages * int(copies)

        # Call to deduct pages
        code = deduct_pages(total_pages)
        if code != 200:
            raise Exception("Deduct pages failed")

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

        temp = "temp.pdf"
        with open(temp, 'wb') as f:
            f.write(pdf_binary_data)

        if temp and temp.endswith('.pdf'):
            conn = cups.Connection()
            printers = conn.getPrinters()
            if len(printers) == 0:
                raise Exception("No printers found")
            selected_printer = list(printers.keys())[0]  # Assuming the first printer in the list

            options = {
                'multiple-document-handling': 'separate-documents-collated-copies' if copies > 1 else 'single_document',
                'sides': 'two-sided-long-edge' if double_page == 'double' else 'one-sided',
                'copies': str(copies)
            }

            job_info = conn.printFile(selected_printer, temp, "", options)

            while conn.getJobAttributes(job_info)["job-state"] != 9:
                if (conn.getJobAttributes(job_info)["job-state"] == 6 or conn.getJobAttributes(job_info)["job-state"] == 7 or conn.getJobAttributes(job_info)["job-state"] == 8):
                    return {{'error': 'An unexpected error occurred', 'details': '{str(e)}'}}
                print("Processing job")
                time.sleep(1)

            os.remove(temp)

        return {'Current Job': file['name'], 'completed': 'no'}
    
    return {'completed': 'yes'}
