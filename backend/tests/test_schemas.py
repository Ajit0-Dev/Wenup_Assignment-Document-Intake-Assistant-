import pytest
from app.models.intake_state import IntakeState
from pydantic import ValidationError

def test_initial_state_is_valid():
    state = IntakeState()
    assert state.full_name.status == "missing"
    assert state.full_name.value is None

def test_invalid_field_type_rejected():
    with pytest.raises(ValidationError):
        # covers_worldwide_assets expects a boolean
        IntakeState(covers_worldwide_assets={"value": "maybe", "status": "confirmed"})
