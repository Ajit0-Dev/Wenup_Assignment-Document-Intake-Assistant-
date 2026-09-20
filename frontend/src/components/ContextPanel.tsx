import React, { useState } from 'react';
import type { IntakeState } from '../api';
import InformationTab from './InformationTab';
import DocumentTab from './DocumentTab';

interface ContextPanelProps {
  state: IntakeState | null;
  sessionId: string | null;
}

const ContextPanel: React.FC<ContextPanelProps> = ({ state, sessionId }) => {
  const [activeTab, setActiveTab] = useState<'info' | 'document'>('info');

  return (
    <div className="context-panel">
      <div className="tabs-header">
        <button 
          className={`tab-button ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          Information
        </button>
        <button 
          className={`tab-button ${activeTab === 'document' ? 'active' : ''}`}
          onClick={() => setActiveTab('document')}
        >
          Document Preview
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'info' ? (
          <InformationTab state={state} />
        ) : (
          <DocumentTab state={state} sessionId={sessionId} />
        )}
      </div>
    </div>
  );
};

export default ContextPanel;
