import frappe
import requests
import json

@frappe.whitelist()
def send_whatsapp_message(recipient, message_body, content_sid=None, template_variables=None):
    """
    Sends a WhatsApp message using credentials from Twilio Settings.
    Can send a simple text message or a template message.
    Only logs to the Error Log if a real error occurs.
    """
    try:
        # Get credentials securely from the Single Doctype
        account_sid = frappe.db.get_single_value("Twilio Settings", "twilio_account_sid")
        from_number = frappe.db.get_single_value("Twilio Settings", "twilio_whatsapp_number")
        
        # get_password must be called on the full document object
        settings_doc = frappe.get_doc("Twilio Settings")
        auth_token = settings_doc.get_password('twilio_auth_token')

        # Validate that all credentials exist before proceeding
        if not all([account_sid, auth_token, from_number]):
             error_msg = "Twilio credentials are not fully set in Twilio Settings. Please check the configuration."
             frappe.log_error(error_msg, "Twilio Integration Error")
             return {"status": "error", "message": error_msg}

        # Construct the API request
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        
        data = {
            "From": from_number,
            "To": f"whatsapp:{recipient}",
            "Body": message_body # Used for simple messages or as fallback text
        }

        # If a template SID is provided, use it
        if content_sid:
            data.pop("Body") # Twilio requires removing Body when sending a template
            data["ContentSid"] = content_sid
            if template_variables:
                data["ContentVariables"] = json.dumps(template_variables)

        auth = (account_sid, auth_token)
        response = requests.post(url, data=data, auth=auth)
        
        # This will raise an HTTPError if the HTTP request returned an unsuccessful status code
        response.raise_for_status()

        # Success! Return the status and message SID without creating a log entry.
        return {"status": "success", "message_sid": response.json().get("sid")}

    except requests.exceptions.HTTPError as e:
        # This block catches errors from Twilio's API (e.g., bad number, invalid template)
        error_response = e.response.json()
        error_message = error_response.get("message", "Unknown Twilio Error")
        frappe.log_error(f"Twilio API Error for {recipient}: {error_message}", "Twilio Integration Error")
        return {"status": "error", "message": error_message}
    
    except Exception as e:
        # This block catches other errors (e.g., network issues, coding errors)
        frappe.log_error(f"Failed to send WhatsApp message to {recipient}: {frappe.get_traceback()}", "Twilio Integration Error")
        return {"status": "error", "message": str(e)}
