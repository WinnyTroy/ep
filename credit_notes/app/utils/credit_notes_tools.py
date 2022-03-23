import json
import hmac
import base64
import hashlib
import logging
import requests
from fastapi import HTTPException
from credit_notes.app.settings import settings
from .common_vars import create_credit_note_request_obj
from ..utils.db_connections_utils import (get_saved_user,
                                         query_user_existing_installations,
                                         query_user_installation_records)

# main function interacting with unleashed API
def unleashed_api_get_request(url_base, url_param,
                              request_method,
                              request_data=None):
    # Create Unleashed URL
    url = "https://api.unleashedsoftware.com/" + url_base
    if url_param:
        url += '?' + url_param
    signature = hmac.new(settings.unleashed_api_key.encode(
                                            'utf-8'), url_param.encode(
                                                'utf-8'), hashlib.sha256)
    # Create auth token using url params and api key
    auth_token = signature.digest()
    auth_token64 = base64.b64encode(auth_token)
    # set request headers
    headers = {
            'Accept': 'application/json',
            'api-auth-id': settings.unleashed_api_id,
            'api-auth-signature': auth_token64.decode("utf-8"),
            'Content-Type': 'application/json'
    }
    # perform request
    unleashed_data = requests.request(request_method,
                                        data=json.dumps(request_data),
                                        url=url, headers=headers)

    if unleashed_data.status_code != 200:
        error_message = unleashed_data.json()['description']
        logging.error(f'Request failed with-{error_message}')
        raise HTTPException(
            status_code=unleashed_data.status_code,
            detail=error_message)

    unleashed_response = unleashed_data.json()
    return unleashed_response

def get_single_unleashed_customer_details(name):
    '''
    retrieve single customer details.
    '''
    url_param = f"customerCode={name}"
    url_base = "Customers"
    unleashed_json = unleashed_api_get_request(url_base,
                                               url_param,
                                               request_method="get")
    return unleashed_json

def create_credit_note(client_code, product_code,
                       warehouse_code, credit_amount, credit_reason):
    '''
    Create free type credit note.
    '''
    request_method = "post"
    url_param = ""
    url_base = "CreditNotes/FreeCredit"

    # create shallow copy of request json data
    request_data = create_credit_note_request_obj.copy()

    # Update dynamic values
    request_data["Warehouse"]["Guid"] = warehouse_code
    request_data["Customer"]["Guid"] = client_code
    request_data["CreditLines"][0]['CreditPrice'] = credit_amount
    request_data["CreditLines"][0]["Product"]["Guid"] = product_code
    request_data["CreditLines"][0]["Comments"] = credit_reason
    unleashed_credit_note_json = unleashed_api_get_request(url_base,
                                                           url_param,
                                                           request_method,
                                                           request_data)

    return unleashed_credit_note_json

def calculate_existing_credits(db_user_installations):
    '''
    Function that sums up all existing credit records.
    '''
    # Handle scenerio where user had
    # no existing installation records
    if len(db_user_installations) > 1:
        aggregated_credit_sum = sum(
            [item.item_price for item in db_user_installations])
    else:
        aggregated_credit_sum = 0
    return aggregated_credit_sum

def fetch_client_existing_interest_invoices(client_id):
    '''
    Function that fetches existing credit notes
    for specific client.
    '''
    # Fetch user account from db
    import ipdb; ipdb.set_trace()
    db_user_account = get_saved_user(client_id=client_id)

    if not isinstance(db_user_account, HTTPException):
        db_user_installations = query_user_installation_records(
            db_user_account_id=db_user_account)
        # Query financing component installations for current user
        if not isinstance(db_user_installations, HTTPException):
            db_user_existing_credit_invoices = query_user_existing_installations(
                db_user_installations=db_user_installations)
            return db_user_existing_credit_invoices
        else:
            return db_user_installations
    else:
        return db_user_account

def aggregate_existing_credit(db_user_existing_credit_invoices, credit_amount):
    # Instantiate credit value to 0
    existing_client_credit_value = 0

    # Determine if we should generate credit note
    aggregated_existing_credits = calculate_existing_credits(
        db_user_existing_credit_invoices)

    # Deduct existing credit from credit amount requested
    existing_client_credit_value = credit_amount - aggregated_existing_credits

    return existing_client_credit_value
