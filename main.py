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


app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)
# cache.init_app(app=app, config={"CACHE_TYPE": "filesystem",'CACHE_DIR': Path('/tmp')})s


CLOUD_SERVER_URL = 'https://files-server.onrender.com'  # Currently local host , will change it to cloud

#creating session 
session = requests.Session()


@app.route('/')
def index():
    return "Working, Kiosk Server"


TRAY_STATUS_FILE = 'tray_status.json'
jobs = []


def load_try_status():
    with open(TRAY_STATUS_FILE, 'r') as f:
        return json.load(f)


def save_tray_status(tray_status):
    with open(TRAY_STATUS_FILE, 'w') as f:
        json.dump(tray_status, f)
        

def print_file_with_tray_management(temp_file, num_pages, copies, double_page):
    tray_status = load_try_status() 
    pages_remaining = tray_status['pages_remaining']
    
    
    conn = cups.Connection()
    if (conn is None):
        raise Exception("Cups Connection not Created")
    
    
    printers = conn.getPrinters()
    
    if len(printers) == 0:
        raise Exception("No printers found")
    selected_printer = list(printers.keys())[0]
    
    try:
        double_page =bool(double_page)
        if pages_remaining >= num_pages * copies:
            options = {
                'copies': str(copies),
                'multiple-document-handling': 'separated-documents-collated-copies' if double_page else 'single_document'
            }
            
            job_id = conn.printFile(selected_printer, temp_file, "Print Job", options)
            
            while conn.getJobAttributes(job_id)["job-state"] != 9:
                time.sleep(2)
            
            pages_remaining -= num_pages * copies
            tray_status['pages_remaining'] = pages_remaining
            
            save_tray_status(tray_status)
            
            if (pages_remaining <= 50):
                pass
                # write notify logic here
            
        else:
            raise Exception("Not enough pages remaining to complete the job.")
    except cups.IPPError as e:
        print(f"Print job failed: {str(e)}")
        return {"status": "error", "message": "Print job failed due to cups issue."}
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"status": "error", "message": str(e)}
    
@app.route('/resetPages', methods=['POST'])
def reset_pages():
    reset_value = request.args.get('pages')
    if (not (reset_value == 200 or reset_value == 500 or reset_value == 700)):
        return jsonify({'message': 'Invalid reset value'}), 400
    try:
        tray_status = load_try_status()
        
        tray_status['pages_remaining'] = reset_value
        save_tray_status(tray_status)
        ##
        return jsonify({'message': 'Pages count reset successfully'}), 200
    except Exception as e:
        return jsonify({'message': f'Some error occured \n {e}'}), 400


@app.route('/getPages', methods=['GET'])
def get_pages():
    try:
        tray_status = load_try_status()
        pages = tray_status['pages_remaining']
        return jsonify({'pages': pages}), 200
    except Exception as e:
        return jsonify({'message': f'Some error occured \n {e}'}), 400  


@app.route('/printNew', methods=['POST', 'GET'])
def print_route_new():
    global jobs
    if request.method == 'POST':
        try:
            if 'pdf' not in request.json:
                return Response(json.dumps({'error': 'No file received'}), status = 400, content_type='application/json')
            
            files = request.json.get('pdf')
            jobs.append(files)

            return jsonify({'status': 'Printing started'}), 200

        except Exception as e:
            return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

    elif request.method == 'GET':
        def generate_events():
            try:
                while jobs:
                    files = jobs.pop(0)
                    for file in files:
                        blob_data = file['blob']
                        double_page = file['selectedOption']
                        copies = file['numCopies']
                        selected_pages = file['selectedPages']
                        
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
                        
                        # Number of pages in the file
                        num_pages = len(selected_pages)
                        
                        # Attempt to print using tray management
                        result = print_file_with_tray_management(temp, num_pages, copies, double_page)
                        if result["status"] == "error":
                            yield f"data: {json.dumps({'error': result['message']})}\n\n"
                        else:
                            yield f"data: {json.dumps({'Current Job': file['name'], 'completed':'no', 'tray': result['tray']})}\n\n"
                        
                        os.remove(temp)
            
                    yield f"data: {json.dumps({'completed' : 'yes'})}\n\n"
            
            except Exception as e:
                yield f"data: {{'error': 'An unexpected error occurred', 'details': '{str(e)}'}}\n\n"
        
        return Response(generate_events(), content_type='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True, port=5001)