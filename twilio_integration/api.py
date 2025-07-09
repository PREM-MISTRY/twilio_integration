import frappe
import requests
import json

@frappe.whitelist()
def send_whatsapp_message(recipient, message_body, content_sid=None, template_variables=None):
    """
    Sends a WhatsApp message using credentials from Twilio Settings.
    Can send a simple text message or a template message.

    :param recipient: The recipient's phone number in E.164 format (e.g., +919876543210).
    :param message_body: The text of the message or fallback text for a template.
    :param content_sid: (Optional) The SID of the Twilio template (e.g., 'HX...').
    :param template_variables: (Optional) A dictionary of variables for the template, e.g., {"1": "Value1", "2": "Value2"}.
    """
    try:
        settings = frappe.get_doc("Twilio Settings")
        account_sid = settings.twilio_account_sid
        auth_token = settings.get_password('twilio_auth_token')
        from_number = settings.twilio_whatsapp_number

        if not all([account_sid, auth_token, from_number]):
            frappe.log_error("Twilio credentials are not set in Twilio Settings.", "Twilio Integration Error")
            return {"status": "error", "message": "Twilio credentials are not configured."}

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
        response.raise_for_status()

        frappe.log_error(f"WhatsApp message sent to {recipient}", "Twilio Success")
        return {"status": "success", "message_sid": response.json().get("sid")}

    except requests.exceptions.HTTPError as e:
        error_response = e.response.json()
        error_message = error_response.get("message", "Unknown Twilio Error")
        frappe.log_error(f"Twilio API Error for {recipient}: {error_message}", "Twilio Integration Error")
        return {"status": "error", "message": error_message}
    
    except Exception as e:
        frappe.log_error(f"Failed to send WhatsApp message to {recipient}: {str(e)}", "Twilio Integration Error")
        return {"status": "error", "message": str(e)}