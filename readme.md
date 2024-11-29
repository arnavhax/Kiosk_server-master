 

---

## API Documentation

### 1. `GET /isPrinterConnected`

#### Purpose:
This route checks if the printer is connected and online. The connection status is determined based on the printer’s state reasons, including conditions such as "media-empty", "offline-report", etc. It returns a boolean response indicating the connection status.

#### HTTP Method:
`GET`

#### Endpoint:
`/isPrinterConnected`

#### Request Parameters:
- None

#### Response:
##### Success (200):
Returns a JSON response indicating whether the printer is connected based on its state reasons.

- **Status Code**: 200 OK
- **Content Type**: `application/json`

###### Response Body:
```json
{
  "status": true | false,
  "reasons": [ "string" ] // An array of reasons for the current printer state
}
```

##### Error Handling:
- **500 Internal Server Error**: If there is an issue connecting to the CUPS server or fetching the printer status.
- **503 Service Unavailable**: If the printer connection could not be verified.

###### Example Response (Connected):
```json
{
  "status": true,
  "reasons": []
}
```

###### Example Response (Disconnected):
```json
{
  "status": false,
  "reasons": [
    "offline-report",
    "media-empty-report"
  ]
}
```

#### Error Responses:
- **500 Internal Server Error**
  - **Description**: Occurs if there is a failure in connecting to CUPS or an internal application error.
  - **Response**:
    ```json
    {
      "error": "Failed to connect to printer.",
      "details": "Specific error details"
    }
    ```

#### Example Request:
```bash
GET /isPrinterConnected HTTP/1.1
Host: your-kiosk-server.com
```

#### Example Response (Printer Connected):
```json
{
  "status": true,
  "reasons": []
}
```

#### Example Response (Printer Disconnected):
```json
{
  "status": false,
  "reasons": [
    "offline-report",
    "media-empty-report"
  ]
}
```

---

### 2. `GET /printerStatus`

#### Purpose:
This route retrieves all current printer state reasons and presents the current state of the printer, along with any specific warnings or errors. It provides detailed information about the printer's operational status.

#### HTTP Method:
`GET`

#### Endpoint:
`/printerStatus`

#### Request Parameters:
- None

#### Response:
##### Success (200):
Returns detailed information about the current printer status and state reasons.

- **Status Code**: 200 OK
- **Content Type**: `application/json`

###### Response Body:
```json
{
  "printer_name": "string", // The name of the printer
  "printer_state": "string", // Printer state (3 for idle, 4 for printing, etc.)
  "printer_state_reasons": [
    "string" // List of printer state reasons (e.g. "offline-report", "media-jam", "toner-low", etc.)
  ]
}
```

##### Error Handling:
- **500 Internal Server Error**: If there is an issue connecting to the CUPS server or fetching the printer status.
- **404 Not Found**: If no printer is found.
  
###### Example Response (Printer is Printing):
```json
{
  "printer_name": "My_Printer",
  "printer_state": "4",
  "printer_state_reasons": [
    "printing",
    "toner-low"
  ]
}
```

###### Example Response (Printer is Idle):
```json
{
  "printer_name": "My_Printer",
  "printer_state": "3",
  "printer_state_reasons": [
    "idle"
  ]
}
```

#### Error Responses:
- **500 Internal Server Error**
  - **Description**: Occurs if there is a failure in connecting to CUPS or an internal application error.
  - **Response**:
    ```json
    {
      "error": "Failed to retrieve printer status.",
      "details": "Specific error details"
    }
    ```
- **404 Not Found**
  - **Description**: If the requested printer is not found.
  - **Response**:
    ```json
    {
      "error": "Printer not found."
    }
    ```

#### Example Request:
```bash
GET /printerStatus HTTP/1.1
Host: your-kiosk-server.com
```

#### Example Response (Printer in Use):
```json
{
  "printer_name": "My_Printer",
  "printer_state": "4",
  "printer_state_reasons": [
    "printing",
    "toner-low"
  ]
}
```

#### Example Response (Printer is Offline):
```json
{
  "printer_name": "My_Printer",
  "printer_state": "5",
  "printer_state_reasons": [
    "offline-report",
    "media-empty-report"
  ]
}
```

---

### Error Codes and Descriptions:

- **200 OK**: The request was successful, and the printer status is returned.
- **500 Internal Server Error**: An internal error occurred while connecting to CUPS or processing the request.
- **404 Not Found**: The requested printer was not found or no printer is connected.
- **503 Service Unavailable**: The printer is not connected, or the service is temporarily unavailable.

---


# Error Code Documentation

This document outlines the error codes used by the system, along with their descriptions.

| **Error Code** | **Description**                                               |
|----------------|---------------------------------------------------------------|
| 101            | Failed to deduct pages from user balance.                     |
| 102            | No printers found on the CUPS server.                         |
| 103            | Job failed with critical state (e.g., canceled, aborted).      |
| 104            | Printer issue detected (e.g., paper jam, empty media).        |
| 105            | File processing error (e.g., invalid PDF structure).          |
| 106            | Printer overheating detected.                                 |
| 107            | Printer driver or connectivity issue.                         |

## How to Use Error Codes

- **Code 101**: This error occurs when the system cannot deduct pages from the user's account balance, often due to insufficient balance or account-related issues.
- **Code 102**: Raised when no printers are available on the CUPS server, making it impossible to process print jobs.
- **Code 103**: Indicates that a print job has failed due to a critical state, such as being canceled or aborted by the printer.
- **Code 104**: This error signifies a problem with the printer itself, such as a paper jam or empty media.
- **Code 105**: Raised when the system encounters issues while processing a file, such as an invalid PDF structure or unsupported file format.
- **Code 106**: Indicates that the printer has overheated, and the job cannot proceed until the issue is resolved.
- **Code 107**: Raised when there are connectivity or driver issues that prevent the printer from communicating with the system.

## Example Error Response

When an error occurs, the system will return a structured response like:

```json
{
  "error": "An issue occurred during printing",
  "details": {
    "code": 101,
    "message": "Failed to deduct pages from user balance."
  }
}

Here’s a Markdown example of how the different error cases can be represented as sample yield responses based on the exception handling logic in the Flask route:

```markdown
# Sample Yield Responses for Print Job Processing

This document provides sample yield responses for various cases during the print job processing.

## 1. **No File Received**
If the request does not contain a PDF file:

```json
data: {"error": "No file received", "details": {"message": "No PDF file found in the request."}}
```

## 2. **Failed to Deduct Pages from User Balance**
If the system fails to deduct pages from the user's balance:

```json
data: {"error": "An issue occurred during printing", "details": {"code": 101, "message": "Failed to deduct pages from user balance."}}
```

## 3. **No Printers Found on the CUPS Server**
If no printers are available on the CUPS server:

```json
data: {"error": "An issue occurred during printing", "details": {"code": 102, "message": "No printers found on the CUPS server."}}
```

## 4. **Job Failed with Critical State**
If the print job fails with a critical state (e.g., canceled, aborted):

```json
data: {"error": "An issue occurred during printing", "details": {"code": 103, "message": "Job failed with state 5: Job canceled."}}
```

## 5. **Printer Issue Detected (Paper Jam, Empty Media, etc.)**
If there is a printer issue such as a paper jam or empty media:

```json
data: {"error": "An issue occurred during printing", "details": {"code": 104, "message": "Printer issue detected: media-empty-error"}}
```

## 6. **File Processing Error (Invalid PDF Structure)**
If there is an error in processing the PDF file:

```json
data: {"error": "An issue occurred during printing", "details": {"message": "File processing error: Invalid PDF structure."}}
```

## 7. **Printer Overheating Detected**
If the printer is overheating:

```json
data: {"error": "An issue occurred during printing", "details": {"message": "Printer overheating detected."}}
```

## 8. **Printer Driver or Connectivity Issue**
If there is a driver or connectivity issue with the printer:

```json
data: {"error": "An issue occurred during printing", "details": {"message": "Printer driver or connectivity issue."}}
```

## 9. **Successful Job Completion**
If the print job is successfully completed:

```json
data: {"status": "success", "details": {"message": "Job completed successfully."}}
```

## 10. **No Jobs Available in Queue**
If there are no jobs available in the job queue:

```json
data: {"error": "No jobs available", "details": {"message": "No print jobs in the queue."}}
```

## 11. **Unknown Error**
For any unexpected errors:

```json
data: {"error": "An unexpected error occurred", "details": {"message": "An unknown error occurred during printing."}}
```

