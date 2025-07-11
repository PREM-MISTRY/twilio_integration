import frappe
import requests
import json

@frappe.whitelist()
def send_whatsapp_message(recipient, message_body, content_sid=None, template_variables=None):
    """
    Sends a WhatsApp message using credentials from Twilio Settings.
    Includes a msgprint command for definitive testing.
    """
    # This is the test line. If this runs, the app is working.
    # frappe.msgprint("Confirmation: The send_whatsapp_message function in your custom app is running.")

    try:
        # Get credentials securely from the Single Doctype
        account_sid = frappe.db.get_single_value("Twilio Settings", "twilio_account_sid")
        from_number = frappe.db.get_single_value("Twilio Settings", "twilio_whatsapp_number")
        
        settings_doc = frappe.get_doc("Twilio Settings")
        auth_token = settings_doc.get_password('twilio_auth_token')

        if not all([account_sid, auth_token, from_number]):
             error_msg = "Twilio credentials are not fully set in Twilio Settings."
             frappe.log_error(error_msg, "Twilio Integration Error")
             return {"status": "error", "message": error_msg}

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        data = {
            "From": from_number,
            "To": f"whatsapp:{recipient}",
            "Body": message_body
        }

        if content_sid:
            data.pop("Body")
            data["ContentSid"] = content_sid
            if template_variables:
                data["ContentVariables"] = json.dumps(template_variables)

        auth = (account_sid, auth_token)
        response = requests.post(url, data=data, auth=auth)
        response.raise_for_status()

        return {"status": "success", "message_sid": response.json().get("sid")}

    except Exception as e:
        frappe.log_error(f"Failed to send WhatsApp message: {frappe.get_traceback()}", "Twilio Integration Error")
        return {"status": "error", "message": str(e)}
