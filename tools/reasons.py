PRINTER_ISSUE_REASONS = [
    # General Issues
    'offline-report', 'paused-report', 'printer-stopped',
    
    # Consumables
    'toner-empty-report', 'toner-low-report', 'marker-supply-empty-report',
    'marker-supply-low-report', 'refill-required-report', 'expired-cartridge-error',
    'unauthorized-supply-error',
    
    # Media Handling
    'media-needed-report', 'media-jam-report', 'unsupported-media-error',
    'paper-out-report', 'paper-misaligned-report', 'envelope-jam-report',
    
    # Components
    'door-open-report', 'cover-open-report', 'tray-missing-report',
    'sensor-failure-report', 'optical-error-report',
    
    # Job Issues
    'queue-full-report', 'stuck-job-error', 'corrupt-job-report',
    'unsupported-job-format-error', 'duplicate-job-error', 'job-cancelled-report',
    'job-hold-report', 'priority-job-overload',
    
    # Hardware Failures
    'fuser-error', 'motor-error', 'carriage-jam-error', 'hardware-error',
    'printhead-error', 'memory-overflow-error', 'controller-error',
    
    # Connectivity
    'connection-error', 'network-unreachable-error', 'wifi-disconnected-report',
    'ethernet-disconnected-report', 'protocol-error',
    
    # Environmental
    'power-failure-report', 'power-surge-error', 'overheating-report',
    'temperature-warning-report',
    
    # Firmware/Software
    'firmware-corruption-error', 'update-required-error', 'update-failed-report',
    'software-error', 'configuration-error',
    
    # Security/Authentication
    'invalid-user-authentication', 'ssl-configuration-error',
    'malware-detected-report', 'unauthorized-access-report',
    
    # Warnings and Notices
    'maintenance-needed-report', 'cleaning-needed-report', 'calibration-needed-report',
    'excessive-usage-warning', 'eol-notice-report',
    
    # Rare Issues
    'malware-detected-report', 'unauthorized-access-report', 'disk-failure-report',
    'read-write-error'
]
