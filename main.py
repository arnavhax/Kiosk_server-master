from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import cups
import requests
import os
import base64
from PyPDF2 import PdfWriter, PdfReader
import io
import time
import json
import secrets
from tools.tray_status import load_tray_status, save_tray_status
from tools.jobs_handler import load_jobs, save_jobs
from tools.reasons import PRINTER_ISSUE_REASONS
from tools.deduct_pages import deduct_pages
import math
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)

CLOUD_SERVER_URL = 'https://files-server.onrender.com' 

session = requests.Session()


@app.route('/resetPages', methods=['POST'])
def reset_pages():
    reset_value = request.args.get('pages')
    if (not (reset_value == 200 or reset_value == 500 or reset_value == 700)):
        return jsonify({'message': 'Invalid reset value'}), 400
    try:
        tray_status = load_tray_status()
        if (reset_value == 200):
            tray_status['pages_remaining_tray2'] = reset_value
        elif (reset_value == 500):
            tray_status['pages_remaining_tray3'] = reset_value
        else:
            tray_status['pages_remaining_tray2'] = 200
            tray_status['pages_remaining_tray3'] = 500
    
        save_tray_status(tray_status)
        return jsonify({'message': 'Pages count reset successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Some error occured \n {e}'}), 400


@app.route('/getPages', methods=['GET'])
def get_pages():
    try:
        tray_status = load_tray_status()
        pages = tray_status['pages_remaining_tray2']+tray_status['pages_remaining_tray3']
        return jsonify({'pages': pages}), 200
    except Exception as e:
        return jsonify({'message': f'Some error occured \n {e}'}), 400  


@app.route('/printNew', methods=['POST', 'GET'])
def print_route_new():
    if request.method == 'POST':
        try:
            if 'pdf' not in request.json:
                return Response(json.dumps({'error': 'No file received'}), status=400, content_type='application/json')
            
            files = request.json.get('pdf')
            print("inside printnew")
            # Load jobs from jobs.json
            jobs = load_jobs()
            print("jobs loaded")
            jobs.append(files)
            save_jobs(jobs)  # Save the updated jobs list to jobs.json

            return jsonify({'status': 'Printing started'}), 200

        except Exception as e:
            return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

    elif request.method == 'GET':
        def generate_events():
            try:
                # Load jobs from the file
                jobs = load_jobs()
                
                if not jobs:
                    yield f"data: {{'error': 'No jobs available'}}\n\n"
                    return
                
                files = jobs[0]
                jobs = []  # Process the first and only job
                print("jobs after popping" ,jobs)
                save_jobs(jobs)  # Save the updated jobs list after removing the processed job
                
                for file in files:
                    blob_data = file['blob']
                    double_page = file['selectedOption']
                    copies = file['numCopies']
                    selected_pages = file['selectedPages']


                    ## DEDUCTING PAGES HERE 
                    print("PRINTING ")
    
                    if double_page == 'double':
                        job_pages = math.ceil(int(len(selected_pages))/2)
                    else:
                        job_pages = int(len(selected_pages))
                    total_pages = job_pages*int(copies)
                    print("TOTAL PAGES", total_pages)
                    code = deduct_pages(total_pages)
                    
                    if (code != 200):
                        raise Exception("Deduct pages failed")
                    
                    print("Options", double_page, copies, selected_pages)
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
                        print(options)
                        
                        job_info = conn.printFile(selected_printer, temp, "", options)
                        
                        while conn.getJobAttributes(job_info)["job-state"] != 9:
                            print("Processing job")
                            time.sleep(1)  # optimise this , find a way to make this more stable
                        
                        yield f"data: {json.dumps({'Current Job': file['name'], 'completed': 'no'})}\n\n"
                        
                        os.remove(temp)
            
                yield f"data: {json.dumps({'completed': 'yes'})}\n\n"
            
            except Exception as e:
                yield f"data: {{'error': 'An unexpected error occurred', 'details': '{str(e)}'}}\n\n"
        
        return Response(generate_events(), content_type='text/event-stream')



@app.route('/isPrinterConnected', methods=['GET'])
def is_printer_connected():
    try:
        # Establish a connection to the CUPS server
        conn = cups.Connection()

        # Fetch the list of available printers
        printers = conn.getPrinters()

        if not printers:
            return jsonify({'status': False, 'message': 'No printers found.'}), 404

        # Assuming we are checking the first printer
        printer_name = list(printers.keys())[0]

        # Fetch printer attributes
        printer_attributes = conn.getPrinterAttributes(printer_name)
        printer_state_reason = printer_attributes.get('printer-state-reasons', [])

        # Check if any of the issue reasons are present
        if any(reason in printer_state_reason for reason in PRINTER_ISSUE_REASONS):
            return jsonify({
                'status': False,
                'message': f"Printer is not connected or has issues: {', '.join(printer_state_reason)}",
                'printer_state_reason': printer_state_reason
            }), 200
        else:
            return jsonify({
                'status': True,
                'message': 'Printer is connected and ready.',
                'printer_state_reason': printer_state_reason
            }), 200

    except cups.IPPError as e:
        # Handle specific CUPS errors
        return jsonify({'status': False, 'message': f'IPP Error: {str(e)}'}), 500
    except Exception as e:
        # General error handling
        return jsonify({'status': False, 'message': f'An unexpected error occurred: {str(e)}'}), 500


@app.route('/printerStatus', methods=['GET'])
def get_printer_status():
    try:
        # Establish a connection to the CUPS server
        conn = cups.Connection()

        # Fetch the list of available printers
        printers = conn.getPrinters()
        
        if not printers:
            return jsonify({'status': 'error', 'message': 'No printers found.'}), 404

        # Assuming we are checking the first printer
        printer_name = list(printers.keys())[0]
        printer_attributes = conn.getPrinterAttributes(printer_name)

        # Get the printer state (3: Idle, 4: Processing, 5: Stopped)
        printer_state = printer_attributes['printer-state']

        # Printer state reasons give more specific information about issues
        printer_state_reason = printer_attributes.get('printer-state-reasons', 'none')

        # Handle different printer states according to CUPS official documentation
        if printer_state == 3:
            state_message = 'Printer is idle and ready to print.'
        elif printer_state == 4:
            state_message = 'Printer is currently processing a job.'
        elif printer_state == 5:
            state_message = 'Printer is stopped due to an issue.'
        else:
            state_message = 'Unknown printer state.'

        return jsonify({
            'status': 'success',
            'printer_name': printer_name,
            'printer_state': printer_state,
            'state_message': state_message,
            'printer_state_reason': printer_state_reason
        }), 200

    except cups.IPPError as e:
        # Handle specific CUPS errors
        return jsonify({'status': 'error', 'message': f'IPP Error: {str(e)}'}), 500
    except Exception as e:
        # General error handling
        return jsonify({'status': 'error', 'message': f'An unexpected error occurred: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5001)
    


# cartridge status ??
# printer test cases ?
# restart or abort ?
# printnewpage for testing ???
# page count updation after every file ?

