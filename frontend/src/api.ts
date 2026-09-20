export interface FieldValue {
  value: any;
  status: 'missing' | 'unconfirmed' | 'confirmed';
}

export interface IntakeState {
  full_name: FieldValue;
  home_address: FieldValue;
  covers_worldwide_assets: FieldValue;
  has_children: FieldValue;
  children_names: FieldValue;
  executor: {
    name: FieldValue;
    relationship: FieldValue;
  };
  specific_gifts: FieldValue;
  additional_wishes: FieldValue;
}

export interface SessionResponse {
  session_id: string;
  message: string;
  state: IntakeState;
}

export interface ChatRequest {
  session_id: string;
  message: string;
}

export interface ChatResponse {
  session_id: string;
  assistant_message: string;
  state: IntakeState;
  clarification_needed: string | null;
}

export const createSession = async (): Promise<SessionResponse> => {
  const response = await fetch('/api/session', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to create session');
  }

  return response.json();
};

export const sendChatMessage = async (
  sessionId: string,
  message: string
): Promise<ChatResponse> => {
  const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!response.ok) {
    throw new Error('Failed to send message');
  }

  return response.json();
};

export const fetchDocument = async (sessionId: string): Promise<string> => {
  const response = await fetch(`/api/document/${sessionId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch document preview');
  }
  const data = await response.json();
  return data.html_content;
};

