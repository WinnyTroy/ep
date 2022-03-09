import ast
import json
import pytest
from credit_notes.app.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def test_app():
    client = TestClient(app)
    yield client

test_data = ('{"client_id": 10811332,'
             '"amount": 29698,'
             '"comments": "why this is being created"}')

# def test_create_unleashed_credit_note(test_app):
#     '''
#     Test post request to `/api/create-credit`
#     creates credit note on Unleashed.
#     '''
#     # Make request
#     resp = test_app.post(
#         "/api/create-credit", test_data)
#     request_data = ast.literal_eval(test_data)

#     assert resp.status_code == 201
#     # Test that Free Credit Note created on Unleashed
#     assert resp.json()['CreditType'] == 'FreeCredit'
#     # Test that Credit is created for client Id passed to request
#     assert request_data['client_id'] == int(resp.json()['Customer']['CustomerCode'])
#     assert request_data['amount'] == float(resp.json()["CreditLines"][0]['CreditPrice'])
#     assert request_data['comments'] == resp.json()["CreditLines"][0]['Comments']

def test_no_unleashed_client_when_creating_credit_note(test_app):
    '''
    Test that Error is raised if user does not exist in Unleashed system.
    '''
    request_data = ast.literal_eval(test_data)
    request_data['client_id'] = 1081133211
    updated_test_data = json.dumps(request_data)
    # Make request to /api/create-credit endpoint
    resp = test_app.post(
        "/api/create-credit", updated_test_data)

    assert resp.status_code == 404
    assert resp.json()['detail'] == 'Client id `1081133211` does not exist in Unleashed.'
