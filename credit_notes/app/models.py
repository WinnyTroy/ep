from typing import Optional
from sqlmodel import SQLModel, Field


class Installations(SQLModel, table=True):
    __tablename__ = 'sc_installation_unleashed_contents'
    invoice_cn_id: Optional[int] = Field(primary_key=True, nullable=False)
    installation_id: str = Field(nullable=False)
    type: str = Field(nullable=False)
    unleashed_number: str = Field(nullable=False)
    item_code: str = Field(nullable=False)
    quantity: int = Field(nullable=False)
    item_price: float = Field(nullable=False)
    comments: str = Field(nullable=True)
    account_id: str = Field(nullable=True)
    account_ref: int = Field(nullable=True)
    customer_id: str = Field(nullable=True)
    customer_identification: str = Field(nullable=True)
