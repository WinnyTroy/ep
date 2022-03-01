import hmac
import json
import base64
import hashlib
import requests
from .utils.credit_notes_tools import create_credit_note_request_obj


unleashed_api_key = "unleashedapisecretkey=="
unleashed_api_id = "unleashed-api-id-9fa7"


# main function to send a get request to retrieve data from unleashed API
def unleashed_api_get_request(url_base, url_param, request_method, request_data=None):
    # Create url
    url = "https://api.unleashedsoftware.com/" + url_base
    if url_param:
        url += '?' + url_param
    signature = hmac.new(unleashed_api_key.encode('utf-8'), url_param.encode('utf-8'), hashlib.sha256)
    # Create auth token using url params and api key
    auth_token = signature.digest()
    auth_token64 = base64.b64encode(auth_token)
    # set request headers
    headers = {
        'Accept': 'application/json',
        'api-auth-id': unleashed_api_id,
        'api-auth-signature': auth_token64.decode("utf-8"),
        'Content-Type': 'application/json'
    }
    # perform request
    if request_data:
      unleashed_data = requests.request(
                        request_method, data=json.dumps(request_data),
                        url=url, headers=headers)
    else:
      unleashed_data = requests.request(request_method, url=url, headers=headers)
    # convert json to dict
    unleashed_json = json.loads(unleashed_data.content)
    return unleashed_json

# retrieve one specific customer's details
def get_single_unleashed_customer_details(name):
  url_param = f"customerName={name}"
  url_base = "Customers"
  unleashed_json = unleashed_api_get_request(
                    url_base, url_param , request_method="get")
  return unleashed_json

# Create free type credit note
def create_credit_note(client_code, product_code, warehouse_code, credit_amount):
  request_method="post"
  url_param = ""
  url_base = "CreditNotes/FreeCredit"

  # create shallow copy of request json data
  request_data = create_credit_note_request_obj.copy()

  # Update dynamic values
  request_data["Warehouse"]["Guid"] = warehouse_code
  request_data["Customer"]["Guid"] = client_code
  request_data["CreditLines"]["CreditPrice"] = credit_amount
  request_data["CreditLines"]["Product"]["Guid"] = product_code
  unleashed_credit_note_json = unleashed_api_get_request(
                    url_base, url_param, request_method,
                    request_data)
  return unleashed_credit_note_json

def create_customer_free_credit(data):
  # Unpack request data
  client_id = data['client_id']
  credit_amount = data['amount']

  # Fetching client by client name for now
  unleashed_client = get_single_unleashed_customer_details(
                      name="JOSEPH NZAVI")

  # Get unleashed client guid
  client_code = unleashed_client["Items"][0]["Guid"]

  # Default the product to the fincancing component
  product_code = 'f5f20ff7-ebf8-4196-b413-650f50582f8d'

  # Default the warehouse to Wells Fargo
  warehouse_code = 'f8027663-364d-4325-a0f9-518e095aa0da'

  create_credit_note(client_code,
                     product_code,
                     warehouse_code,
                     credit_amount)


if __name__ == "__main__":
    request_data = {"client_id": 14346, "amount": 16000}
    data = create_customer_free_credit(data=request_data)
    print(data)
