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

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)

CLOUD_SERVER_URL = 'https://files-server.onrender.com'  

session = requests.Session()


@app.route('/deductPages', methods=['POST'])
def deduct_pages():
    deduct = request.args.get('pages')
    if (deduct <= 0):
        return jsonify({'message': 'Invalid deduct value'}), 400
    try:
        tray_status = load_tray_status()
        if (deduct > tray_status['pages_remaining_tray3']):
            tray_status['pages_remaining_tray3'] = 0
            tray_status['pages_remaining_tray2'] -= (deduct - tray_status['pages_remaining_tray3'])
        else:
            tray_status['pages_remaining_tray3'] -= deduct
        
        save_tray_status(tray_status)
        
        return jsonify({'message': 'Pages count deducted successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Some error occured \n {e}'}), 400

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
                
                # Process only the first job
                files = jobs.pop(0)  # Process the first job
                save_jobs(jobs)  # Save the updated jobs list after removing the processed job
                
                for file in files:
                    blob_data = file['blob']
                    double_page = file['selectedOption']
                    copies = file['numCopies']
                    selected_pages = file['selectedPages']
                    
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
                            time.sleep(5)
                        
                        yield f"data: {json.dumps({'Current Job': file['name'], 'completed': 'no'})}\n\n"
                        
                        os.remove(temp)
            
                yield f"data: {json.dumps({'completed': 'yes'})}\n\n"
            
            except Exception as e:
                yield f"data: {{'error': 'An unexpected error occurred', 'details': '{str(e)}'}}\n\n"
        
        return Response(generate_events(), content_type='text/event-stream')





if __name__ == '__main__':
    app.run(debug=True, port=5001)
    


# cartridge status ??
# printer connectivity  ?
# printer status - code ?
# printer test cases ?
# restart or abort ?
# printnewpage for testing ???
# page count updation after every file ?





# @app.route('/printTest')
# def printtest():
#     pdf_name = "../data/pdf-test.pdf"
#     conn = cups.Connection()
#     printer = conn.getPrinters()
#     print(printer)

#     # Safe guarding for no printer
#     if not printer:
#         return "No Printer Connected"

#     selected_printer = list(printer.keys())[0]
#     double_sided = False
#     copies = 1

#     options = {
#         'multiple-document-handling': 'separate-documents-collated-copies' if double_sided else 'single_document',
#         'copies': str(copies)
#     }

#     try:
#         conn.printFile(selected_printer, pdf_name, "", options)
#         return f"PRINTING SERVER IS WORKING: PRINTER : {printer}"
#     except Exception as e:
#         return f"Error: {str(e)}"