import json
import hmac
import base64
import hashlib
import requests
from .common_vars import create_credit_note_request_obj
from .dev_settings import unleashed_api_id, unleashed_api_key


# main function interacting with unleashed API
def unleashed_api_get_request(url_base, url_param,
							  request_method, request_data=None):
		# Create url
		url = "https://api.unleashedsoftware.com/" + url_base
		if url_param:
				url += '?' + url_param
		signature = hmac.new(unleashed_api_key.encode(
												'utf-8'), url_param.encode(
													'utf-8'), hashlib.sha256)
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
			unleashed_data = requests.request(request_method,
											  data=json.dumps(request_data),
											  url=url, headers=headers)
		else:
			unleashed_data = requests.request(request_method, url=url, headers=headers)
		# convert json to dict
		unleashed_json = json.loads(unleashed_data.content)
		return unleashed_json

def get_single_unleashed_customer_details(name):
	'''
	retrieve single customer details.
	'''
	url_param = f"customerName={name}"
	url_base = "Customers"
	unleashed_json = unleashed_api_get_request(
										url_base, url_param , request_method="get")
	return unleashed_json

def create_credit_note(client_code, product_code, warehouse_code, credit_amount):
	'''
	Create free type credit note.
	'''
	request_method="post"
	url_param = ""
	url_base = "CreditNotes/FreeCredit"

	# create shallow copy of request json data
	request_data = create_credit_note_request_obj.copy()

	# Update dynamic values
	request_data["Warehouse"]["Guid"] = warehouse_code
	request_data["Customer"]["Guid"] = client_code
	request_data["CreditLines"][0]['CreditPrice'] = credit_amount
	request_data["CreditLines"][0]["Product"]["Guid"] = product_code
	unleashed_credit_note_json = unleashed_api_get_request(url_base,
															url_param,
															request_method,
															request_data)

	return unleashed_credit_note_json
