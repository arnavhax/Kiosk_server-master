 

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

