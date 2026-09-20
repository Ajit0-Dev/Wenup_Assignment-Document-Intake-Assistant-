import React, { useEffect, useState } from 'react';
import type { IntakeState } from '../api';
import { fetchDocument } from '../api';

interface DocumentTabProps {
  state: IntakeState | null;
  sessionId: string | null;
}

const DocumentTab: React.FC<DocumentTabProps> = ({ state, sessionId }) => {
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) return;
    
    const loadDocument = async () => {
      setLoading(true);
      setError(null);
      try {
        const html = await fetchDocument(sessionId);
        setHtmlContent(html);
      } catch (err) {
        setError("Failed to load document preview.");
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [state, sessionId]); // Re-fetch whenever state changes

  return (
    <div className="document-tab">
      <div className="disclaimer">
        <strong>Fictional document for demonstration purposes only — not legal advice.</strong>
      </div>
      
      <div className="document-preview">
        {loading && !htmlContent && <p>Loading document preview...</p>}
        {error && <p className="error-text">{error}</p>}
        
        {htmlContent && (
          <div 
            className="document-html-content"
            dangerouslySetInnerHTML={{ __html: htmlContent }} 
          />
        )}
      </div>
    </div>
  );
};

export default DocumentTab;
