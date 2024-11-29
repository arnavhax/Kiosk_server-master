import cups

def enable_all_printers():
    try:
        # Connect to the CUPS server
        conn = cups.Connection()

        # Get a list of all printers
        printers = conn.getPrinters()

        if not printers:
            print("No printers found.")
            return
        
        # Enable each printer found
        for printer_name in printers:
            print(f"Enabling printer: {printer_name}")
            conn.enablePrinter(printer_name)
        
        print("All printers have been enabled.")
    
    except Exception as e:
        print(f"Error enabling printers: {e}")
        