# Document Intake Assistant — Manual Test Cases

To verify that the Assistant handles all the assignment requirements correctly, you can run through the following test scenarios manually in the UI at `http://localhost:5173`. 

Each scenario verifies a specific edge case or capability required by the Phase 1–5 instructions.

---

## Scenario 1: The Happy Path (Multi-turn Extraction)
**Goal:** Verify the assistant can extract basic fields incrementally.

1. **User:** "My name is Alice Smith."
   - *Expected state:* `full_name` is Confirmed as "Alice Smith".
   - *Expected UI:* Information Tab updates. Assistant asks for address or next missing field.
2. **User:** "I live at 123 Main St, London."
   - *Expected state:* `home_address` is Confirmed. 
3. **User:** "I do not have any assets outside the UK."
   - *Expected state:* `covers_worldwide_assets` is Confirmed as "No" (False).

---

## Scenario 2: Multiple Facts in One Message
**Goal:** Verify the LLM can extract several fields from a single complex sentence.

1. **User:** "My executor will be my brother, David Smith, and I want to leave my vintage car to my son, Michael."
   - *Expected state:* 
     - `executor.name` = "David Smith"
     - `executor.relationship` = "brother"
     - `specific_gifts` = "vintage car to my son, Michael"
   - *Expected UI:* All three fields update simultaneously in the Information tab.

---

## Scenario 3: Corrections & State Override
**Goal:** Verify that a user can correct previously confirmed information, and that conversation history is *not* blindly trusted.

1. **User:** (Following Scenario 1) "Actually, I moved. My new address is 456 High St, Manchester."
   - *Expected state:* `home_address` changes from "123 Main St, London" to "456 High St, Manchester".
   - *Expected UI:* The Document preview immediately updates to show the Manchester address, proving state is the source of truth, not a summary of the whole chat history.

---

## Scenario 4: Ambiguity & Clarification
**Goal:** Verify the assistant refuses to blindly guess when information is vague.

1. **User:** "Give everything to my family."
   - *Expected behavior:* The assistant should *not* update `specific_gifts` or `additional_wishes` with this vague statement. Instead, it should reply asking for clarification (e.g., "Could you specify exactly what you want to give and to whom?").
   - *Expected state:* No fields change.

---

## Scenario 5: Missing Conditional Fields (Children)
**Goal:** Verify that conditional logic works in the state schema.

1. **User:** "I do not have any children."
   - *Expected state:* `has_children` = "No" (False).
   - *Expected behavior:* The assistant should *not* ask for children's names, and should move on to asking about the executor or gifts.

---

## Scenario 6: Irrelevant or Out-of-Bounds Input
**Goal:** Verify the application ignores information outside the allowed schema.

1. **User:** "My favorite color is blue and I want to order a pizza."
   - *Expected behavior:* The LLM may acknowledge the statement politely, but no fields in the `IntakeState` should change. The application strictly validates against the Pydantic schema and drops unknown fields.

---

## Scenario 7: Document Preview Validation
**Goal:** Verify the real-time HTML document generator.

1. Open the **Document Preview** tab on the right side of the screen.
2. Verify the disclaimer is present at the top.
3. Send a new message updating an empty field: "I have no additional wishes."
4. Verify the Document Preview immediately re-renders to include a section about additional wishes (or states none) without requiring a page reload.
