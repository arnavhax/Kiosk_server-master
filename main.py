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
    current_tray = tray_status["current_tray"]
    tray2_pages_remaining = tray_status["tray2_pages_remaining"]
    
    
    conn = cups.Connection()
    if (conn is None):
        raise Exception("Cups Connection not Created")
    
    
    printers = conn.getPrinters()
    
    if len(printers) == 0:
        raise Exception("No printers found")
    selected_printer = list(printers.keys())[0]
    
    try:
        if current_tray == "Tray3":
            print(f"Attempting to print from Tray3 on printer {selected_printer}")
            options = {
                'copies': str(copies),
                'multiple-document-handling': 'separate-documents-collated-copies' if double_page else 'single_document'
            }
            job_id = conn.printFile(selected_printer, temp_file, "Print Job", options)

            # Wait for job completion or failure
            while conn.getJobAttributes(job_id)["job-state"] != 9:
                time.sleep(2)

            job_attrs = conn.getJobAttributes(job_id)
            print(job_attrs)
            # Look for tray information in the job attributes (exact key may vary by printer)
            tray_used = job_attrs.get("media-col", {}).get("InputSlot", "unknown")
            
            print(f"Job completed. Tray used: {tray_used}")

            return {"status": "success", "tray": tray_used}

        elif current_tray == "Tray2":
            if tray2_pages_remaining >= num_pages * copies:
                print(f"Attempting to print from Tray2 on printer {selected_printer}")
                options = {
                    'InputSlot': "Tray2",  # Use Tray2
                    'copies': str(copies)
                }
                job_id = conn.printFile(selected_printer, temp_file, "Print Job", options)

                # Wait for job completion or failure
                while conn.getJobAttributes(job_id)["job-state"] != 9:
                    time.sleep(2)

                # Subtract pages from Tray2
                tray2_pages_remaining -= num_pages * copies
                tray_status["tray2_pages_remaining"] = tray2_pages_remaining
                save_tray_status(tray_status)  # Persist the updated tray status

                print(f"Job successfully printed from Tray2. Pages remaining in Tray2: {tray2_pages_remaining}")
                return {"status": "success", "tray": "Tray2", "pages_remaining": tray2_pages_remaining}
            else:
                raise Exception("Not enough pages remaining in Tray2 to complete the job.")
    except cups.IPPError as e:
        # Handle error where Tray3 runs out of paper and needs to switch to Tray2
        error_str = str(e)
        if "media-empty" in error_str or "not enough pages" in error_str:
            print("Detected 'Out of Paper' or not enough pages in the current tray.")
            tray_status["current_tray"] = "Tray2"
            save_tray_status(tray_status)
            return {"status": "switching", "message": "Switched to Tray2"}
        else:
            print(f"Print job failed: {str(e)}")
            return {"status": "error", "message": "Print job failed due to another issue."}

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {"status": "error", "message": str(e)}
    

##########################
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