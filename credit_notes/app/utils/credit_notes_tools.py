from ast import If
import json
import hmac
import base64
import hashlib
import logging
import requests
from fastapi import HTTPException
from credit_notes.app.settings import settings
from .common_vars import create_credit_note_request_obj
from ..utils.db_connections_utils import (query_db_user_record,
                                         query_user_existing_installations,
                                         query_user_installation_records,
                                         create_unleashed_credit_note_record)

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
    retrieve single customer details
    from Unleashed platform.
    '''
    url_param = f"customerCode={name}"
    url_base = "Customers"
    unleashed_json = unleashed_api_get_request(url_base,
                                               url_param,
                                               request_method="get")
    return unleashed_json

def perform_unleashed_create_credit_note(client_code, product_code,
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

def create_credit_note(client_id, credit_amount, credit_reason):
    # Fetching client by client id
    # if client_credit_value is greater than 0
    unleashed_client = get_single_unleashed_customer_details(
                        name=client_id)

    # Handle Non existent Unleashed clients
    if unleashed_client['Pagination']['NumberOfItems'] == 0:
        raise HTTPException(
            status_code=404,
            detail=f"Client id `{client_id}` does not exist in Unleashed.")
    else:
        # Get unleashed client guid
        client_code = unleashed_client["Items"][0]["Guid"]
        print(f'Client fetched from Unleashed >>>>>>>>>>> {unleashed_client}')
        logging.debug(f'Retrieved Unleashed client - {unleashed_client}')
        # apm.capture_message(f'Retrieved Unleashed client - {unleashed_client}')

    # Default the product to the fincancing component
    product_code = 'f5f20ff7-ebf8-4196-b413-650f50582f8d'

    # Default the warehouse to Wells Fargo Warehouse
    warehouse_code = 'f8027663-364d-4325-a0f9-518e095aa0da'

    response_object = perform_unleashed_create_credit_note(client_code,
                                        product_code, warehouse_code,
                                        credit_amount,credit_reason)
    return response_object

def calculate_existing_credits(db_user_existing_credit_invoices):
    '''
    Function that sums up all existing credit records.
    '''
    if len(db_user_existing_credit_invoices) > 1:
        aggregated_credit_sum = sum(
            [item.item_price for item in db_user_existing_credit_invoices])
    else:
        # If only 1 existing credit invoice
        aggregated_credit_sum = db_user_existing_credit_invoices[0]['item_price']  # noqa
    return aggregated_credit_sum

def confirm_existing_user_credit(client_id, credit_amount, credit_reason):
    '''
    This function is used to determine if we should generate
    an Unleashed Credit Note.
    Params:
        - client_id
        - client_amount
        - credit_reason
    Returns:
        - Unleashed credit json or
        - HTTP Exception
    '''
    # Instantiate credit value to 0
    existing_client_credit_value = 0
    # Fetch user account from db
    db_user_account = query_db_user_record(client_id=client_id)
    # Query `Installations` if user account exists
    if not isinstance(db_user_account, HTTPException):
        db_user_installations = query_user_installation_records(
            db_user_account_id=db_user_account)
        # Query `Sunculture Unleashed Contents` if user account exists
        if not isinstance(db_user_installations, HTTPException):
            db_user_existing_credit_invoices = query_user_existing_installations(
                db_user_installations=db_user_installations)
            ###### Credit Aggregating section ######
            # If we have more than one credit invoice
            if not isinstance(db_user_existing_credit_invoices, HTTPException):
                # Determine if we should generate credit note
                aggregated_existing_credits = calculate_existing_credits(
                    db_user_existing_credit_invoices)

                if aggregated_existing_credits:
                    existing_client_credit_value = aggregated_existing_credits - credit_amount  # noqa

                if existing_client_credit_value < 0:
                    # Generate debit Note on Unleashed
                    return HTTPException(
                        status_code=422 ,
                        detail=f"Bad Request - Client {client_id}'s existing"\
                            f" credit value is {existing_client_credit_value}")
                # If existing credit note is greater than 0
                # Generate Unleashed Credit Note
                created_unleashed_credit_note = create_credit_note(client_id=client_id,
                                                                   credit_amount=credit_amount,
                                                                   credit_reason=credit_reason)
                # Persist Data in unleashed Database
                create_unleashed_credit_note_record(
                    db_user_installations,
                    credit_amount,
                    created_unleashed_credit_note)
                return created_unleashed_credit_note
            return db_user_existing_credit_invoices
        return db_user_installations
    return db_user_account

def perform_unleashed_create_debit_note():
    '''
    Create Unleashed Debit Note
    '''
    pass