from tools.tray_status import load_tray_status, save_tray_status


def deduct_pages(deduct):
    print("Deductiong Pages")
    if (deduct <= 0):
        return 400
    try:
        tray_status = load_tray_status()
        if (deduct > tray_status['pages_remaining_tray3']):
            tray_status['pages_remaining_tray3'] = 0
            tray_status['pages_remaining_tray2'] -= (deduct - tray_status['pages_remaining_tray3'])
        else:
            tray_status['pages_remaining_tray3'] -= deduct
        
        save_tray_status(tray_status)
        print("DEDUCTED PAGES")
        return 200
    except Exception as e:
        print("Log exception here", e)
        return 400
