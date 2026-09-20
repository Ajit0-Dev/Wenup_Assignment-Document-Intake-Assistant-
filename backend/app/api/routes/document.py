from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from uuid import UUID

from app.services.session_service import session_service

router = APIRouter()

@router.get("/document/{session_id}")
async def get_document(session_id: UUID) -> Dict[str, Any]:
    """
    Returns a fictional document preview based on the current session state.
    """
    session = session_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    state = session.intake_state
    
    # Generate document sections based on confirmed fields
    full_name = state.full_name.value if state.full_name.status == 'confirmed' else "[Full Name]"
    address = state.home_address.value if state.home_address.status == 'confirmed' else "[Address]"
    
    worldwide = "Yes" if state.covers_worldwide_assets.status == 'confirmed' and state.covers_worldwide_assets.value else "No"
    if state.covers_worldwide_assets.status != 'confirmed':
        worldwide = "[Unspecified]"
        
    executor_name = state.executor.name.value if state.executor.name.status == 'confirmed' else "[Executor Name]"
    executor_rel = state.executor.relationship.value if state.executor.relationship.status == 'confirmed' else "[Relationship]"
    
    children_info = "N/A"
    if state.has_children.status == 'confirmed':
        if state.has_children.value:
            children_names = state.children_names.value if state.children_names.status == 'confirmed' else ["[Names]"]
            children_info = f"Yes, children: {', '.join(children_names)}"
        else:
            children_info = "No children"
            
    gifts = state.specific_gifts.value if state.specific_gifts.status == 'confirmed' else "None specified"
    wishes = state.additional_wishes.value if state.additional_wishes.status == 'confirmed' else "None specified"

    html_content = f"""
    <h2>Personal Wishes Document</h2>
    <p><em>Prepared for: {full_name}</em></p>
    <p><em>Address: {address}</em></p>
    <hr/>
    <h3>1. Scope of Assets</h3>
    <p>Covers Worldwide Assets: {worldwide}</p>
    
    <h3>2. Family & Beneficiaries</h3>
    <p>Children: {children_info}</p>
    <p>Specific Gifts: {gifts}</p>
    
    <h3>3. Executor Designation</h3>
    <p>I appoint {executor_name} ({executor_rel}) as the executor of this document.</p>
    
    <h3>4. Additional Wishes</h3>
    <p>{wishes}</p>
    """

    return {
        "status": "success",
        "html_content": html_content
    }
