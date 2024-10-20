from flask import Flask, jsonify, request, Response
from flask_cors import CORS
import cups
import requests
import json
import secrets
from tools.tray_status import load_tray_status, save_tray_status
from tools.jobs_handler import load_jobs, save_jobs
from tools.reasons import PRINTER_ISSUE_REASONS
from tools.get_mac_address import get_mac_address
from flask import Response, request, jsonify
from tools.printer_utils import process_print_job
import time

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
CORS(app, supports_credentials=True)
session = requests.Session()


@app.route('/getKioskCredentials', methods=['GET'])
def get_kiosk_credentials():
    mac_address = get_mac_address()
    kiosk_id = 1  # environment variable set in kiosk server
    
    if mac_address is None or kiosk_id is None:
        print("Mac_address or kiosk_id is missing")
        return jsonify({'message': 'Kiosk_id or mac_address not found , hint: check for env config'}), 400
    kiosk_id = int(kiosk_id)
    return jsonify({'mac_address': mac_address, 'kiosk_id': kiosk_id}), 200

@app.route('/resetPages', methods=['POST'])
def reset_pages():
    data = request.get_json()
    reset_value = data.get('pages')
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


@app.route('/print', methods=['POST', 'GET'])
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
                save_jobs(jobs)  # Save the updated jobs list after removing the processed job

                # Call the function from printer_utils
                result = process_print_job(files)
                
                yield f"data: {json.dumps(result)}\n\n"
            
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


@app.route('/test', methods=['GET'])
def test_print_route():
    try:
        # Get the query parameter (either "normal" or "shaded")
        mode = request.args.get('mode')

        # Validate mode
        if mode not in ['normal', 'shaded']:
            return jsonify({'error': 'Invalid mode, must be "normal" or "shaded"'}), 400
        
        # Define the file to print based on the mode
        if mode == 'normal':
            file_to_print = 'testPdfs/TestPage.pdf'
        elif mode == 'shaded':
            file_to_print = 'testPdfs/ShadedTestPage.pdf'

        # Establish connection to CUPS and get available printers
        conn = cups.Connection()
        printers = conn.getPrinters()

        if len(printers) == 0:
            return jsonify({'error': 'No printers found'}), 500

        # Select the first available printer
        selected_printer = list(printers.keys())[0]

        # Define the print options (we're not changing options here)
        options = {
            'media': 'A4'
        }

        # Send the file to the printer
        job_info = conn.printFile(selected_printer, file_to_print, "Test Print", options)

        # Wait for the job to complete (CUPS job state 9 = "completed")
        while conn.getJobAttributes(job_info)["job-state"] != 9:
            print("Processing job")
            time.sleep(1)

        return jsonify({'status': 'Print job completed'}), 200
    
    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
    


# cartridge status ??
# printer test cases ?
# restart or abort ?
# printnewpage for testing ???
# page count updation after every file ?

