import datetime
# These are common credit notes variables that we'll want to access

create_credit_note_request_obj = {
    "Comment": None,
    "CreditDate": datetime.datetime.now().strftime("%Y-%d-%m"),
    "ExchangeRate": 1,  # default this to 1
    "Reference": None,
    "Warehouse": {
      "Guid": ''
    },
    "Customer": {
      "Guid": ''
    },
    "CreditLines": [
      {
        "CreditQuantity": 1,  # default product quantity to 1
        "CreditPrice": '',
        "Reason": "Credit",
        "Return": False,  # No returns for financing component
        "Comments": "UNLEASHED API FREE TYPE CREDIT",
        "Product": {
          "Guid": '',
          "ProductCode": "financing_component"
        }
      }
    ]
  }
