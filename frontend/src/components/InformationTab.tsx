import React from 'react';
import type { IntakeState, FieldValue } from '../api';

interface InformationTabProps {
  state: IntakeState | null;
}

const FieldRow: React.FC<{ label: string; field: FieldValue | undefined }> = ({ label, field }) => {
  if (!field) return null;
  
  let statusIcon = '';
  let statusText = '';
  let statusClass = '';

  switch (field.status) {
    case 'confirmed':
      statusIcon = '✓';
      statusText = 'Confirmed';
      statusClass = 'status-confirmed';
      break;
    case 'unconfirmed':
      statusIcon = '?';
      statusText = 'Needs clarification';
      statusClass = 'status-unconfirmed';
      break;
    case 'missing':
    default:
      statusIcon = '○';
      statusText = 'Missing';
      statusClass = 'status-missing';
      break;
  }

  return (
    <div className="field-row">
      <div className="field-label">{label}</div>
      <div className="field-value">
        {field.value !== null && field.value !== undefined && (
          <span className="field-text">
            {typeof field.value === 'boolean' ? (field.value ? 'Yes' : 'No') : 
             Array.isArray(field.value) ? field.value.join(', ') : 
             String(field.value)}
          </span>
        )}
        <span className={`status-badge ${statusClass}`} title={statusText}>
          {statusIcon} {statusText}
        </span>
      </div>
    </div>
  );
};

const InformationTab: React.FC<InformationTabProps> = ({ state }) => {
  if (!state) {
    return <div className="loading-indicator">Waiting for state...</div>;
  }

  // Calculate progress
  const allFields = [
    state.full_name,
    state.home_address,
    state.covers_worldwide_assets,
    state.has_children,
    state.children_names, // Not strictly required if no children, but simple calculation
    state.executor?.name,
    state.executor?.relationship,
    state.specific_gifts,
    state.additional_wishes
  ].filter(Boolean); // Filter out undefined to prevent errors

  const confirmedCount = allFields.filter(f => f?.status === 'confirmed').length;
  // A simplistic required fields calculation. If has_children is false, children_names shouldn't count against missing.
  // We'll just do a raw count for now to give a sense of progress.
  const progressPercent = Math.min(100, Math.round((confirmedCount / 8) * 100)); // 8 core fields

  return (
    <div className="information-tab">
      <div className="progress-container">
        <div className="progress-text">Intake Progress ({confirmedCount} fields confirmed)</div>
        <div className="progress-bar-bg">
          <div 
            className="progress-bar-fill" 
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      <div className="info-section">
        <h3>Personal Details</h3>
        <FieldRow label="Full Name" field={state.full_name} />
        <FieldRow label="Home Address" field={state.home_address} />
        <FieldRow label="Worldwide Assets" field={state.covers_worldwide_assets} />
      </div>

      <div className="info-section">
        <h3>Family & Beneficiaries</h3>
        <FieldRow label="Has Children" field={state.has_children} />
        {state.has_children?.value === true && (
          <FieldRow label="Children Names" field={state.children_names} />
        )}
        <FieldRow label="Specific Gifts" field={state.specific_gifts} />
      </div>

      <div className="info-section">
        <h3>Executor</h3>
        <FieldRow label="Executor Name" field={state.executor?.name} />
        <FieldRow label="Relationship" field={state.executor?.relationship} />
      </div>

      <div className="info-section">
        <h3>Other</h3>
        <FieldRow label="Additional Wishes" field={state.additional_wishes} />
      </div>
    </div>
  );
};

export default InformationTab;
