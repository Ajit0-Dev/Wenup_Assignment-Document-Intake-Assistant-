from pydantic import BaseModel
from typing import Optional, Literal, Generic, TypeVar, List

T = TypeVar('T')
FieldStatus = Literal["missing", "unconfirmed", "confirmed"]

class FieldValue(BaseModel, Generic[T]):
    value: Optional[T] = None
    status: FieldStatus = "missing"

class Executor(BaseModel):
    name: FieldValue[str] = FieldValue[str]()
    relationship: FieldValue[str] = FieldValue[str]()

class IntakeState(BaseModel):
    full_name: FieldValue[str] = FieldValue[str]()
    home_address: FieldValue[str] = FieldValue[str]()
    covers_worldwide_assets: FieldValue[bool] = FieldValue[bool]()
    has_children: FieldValue[bool] = FieldValue[bool]()
    children_names: FieldValue[List[str]] = FieldValue[List[str]]()
    executor: Executor = Executor()
    specific_gifts: FieldValue[str] = FieldValue[str]()
    additional_wishes: FieldValue[str] = FieldValue[str]()
