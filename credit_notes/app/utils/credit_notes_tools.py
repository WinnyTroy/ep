import json
import hmac
import base64
import hashlib
import logging
import requests
import datetime
from fastapi import HTTPException
from credit_notes.app.settings.settings import settings
from .common_vars import create_credit_note_request_obj
from ..utils.db_connections_utils import (query_user_existing_installations,
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


def generate_unleashed_create_credit_note(client_code, product_code,
                                          warehouse_code, credit_amount,
                                          credit_reason):
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


def create_unleashed_credit_note(client_id, credit_amount, credit_reason):
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

    # Default the product to the fincancing component
    product_code = 'f5f20ff7-ebf8-4196-b413-650f50582f8d'

    # Default the warehouse to Wells Fargo Warehouse
    warehouse_code = 'f8027663-364d-4325-a0f9-518e095aa0da'

    response_object = generate_unleashed_create_credit_note(client_code,
                                                            product_code,
                                                            warehouse_code,
                                                            credit_amount,
                                                            credit_reason)
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
        aggregated_credit_sum = db_user_existing_credit_invoices[
                                0]['item_price']  # noqa
    return aggregated_credit_sum


def confirm_existing_user_credit(client_id,
                                 credit_amount,
                                 credit_reason,
                                 client_name,
                                 client_contact,
                                 performing_action):
    '''
    Used to determine if we should generate
    an Unleashed Credit Note or Debit Note.
    The Debit Note is basically an extra invoice
    on Unleashed.
    '''
    # Query `Sunculture Unleashed Contents Table`
    db_user_existing_credit_invoices = query_user_existing_installations(
            user_account_ref=client_id)

    # *************** Credit Aggregating section ***************
    # Aggregate `item_price` field from
    # data pulled from db
    aggregated_existing_credit = calculate_existing_credits(
        db_user_existing_credit_invoices)

    # Deduct existing credit from amount sent in request
    existing_client_credit_value = credit_amount - aggregated_existing_credit

    if existing_client_credit_value > 0:
        installation_id = db_user_existing_credit_invoices[0].installation_id
        customer_id = db_user_existing_credit_invoices[0].customer_id
        account_id = db_user_existing_credit_invoices[0].account_id
        if performing_action == 'Credit':
            create_credit_note(client_id, credit_amount, credit_reason,
                               installation_id, account_id, customer_id)
        elif performing_action == 'Debit':
            perform_unleashed_create_debit_note(credit_amount, client_name,
                                                client_contact,
                                                installation_id,
                                                account_id, customer_id)
    else:
        return HTTPException(
            status_code=422,
            detail=f"The account {client_id} does not have an subsequent Invoice")  # noqa


def perform_unleashed_create_debit_note(credit_amount, client_name,
                                        client_contact, installation_id,
                                        account_id, customer_id):
    invoice_url = settings.invoice_url
    invoice_request_headers = {"Content-Type": "application/json"}
    debit_request_data = {"installation_id": installation_id,
                          "dispatch_data": datetime.now().strftime("%m/%d/%Y"),
                          "customer_id": customer_id,
                          "dispatch_type": "DebitNote",
                          "account_id": account_id,
                          "warehouse_code": "WF",
                          "customer_names": client_name,
                          "msisdn": client_contact,
                          "debit_amount": credit_amount}
    debit_note_invoice_number = requests.get(data=debit_request_data,
                                             url=invoice_url,
                                             headers=invoice_request_headers)
    return debit_note_invoice_number


def create_credit_note(client_id, credit_amount, credit_reason,
                       installation_id, account_id, customer_id):
    # Create credit Note on Unleashed
    created_unleashed_credit_note = (
        create_unleashed_credit_note(client_id=client_id,
                                     credit_amount=credit_amount,
                                     credit_reason=credit_reason))
    # Persist Data in unleashed Database
    create_unleashed_credit_note_record(
        client_id, credit_amount,
        created_unleashed_credit_note,
        credit_reason, installation_id,
        account_id, customer_id)
    return created_unleashed_credit_note
