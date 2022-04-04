from ..database import engine
from ..models import Installations
from sqlmodel import Session, select, or_

# Intialize database session per single thread
session = Session(engine)


def create_unleashed_credit_note_record(client_id, credit_amount,
                                        created_unleashed_credit_note,
                                        credit_reason, installation_id,
                                        account_id, customer_id):
    created_credit_note = Installations(
        installation_id=installation_id,
        type='Credit Note',
        unleashed_number=created_unleashed_credit_note['CreditNoteNumber'],
        item_code='financing_component',
        quantity=1,
        item_price=credit_amount,
        account_id=account_id,
        account_ref=client_id,
        customer_id=customer_id,
        customer_identification=client_id,
        comments=credit_reason)
    session.add(created_credit_note)
    session.commit()
    return created_credit_note.invoice_cn_id


def query_user_existing_installations(user_account_ref):
    # Query db table `sc_installation_unleashed_contents`
    # for financing_component installations
    client_installations = session.exec(select(Installations).where(
        Installations.account_ref == user_account_ref,
        or_(Installations.item_code == "InterestPiece",
            Installations.item_code == "financing_component"))).all()
    if not client_installations:
        # Return single list where
        # item price is defaulted to 0
        client_installations = [{"item_price": 0}]
    return client_installations
