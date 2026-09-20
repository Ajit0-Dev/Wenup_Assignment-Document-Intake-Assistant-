import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from './App';
import * as api from './api';

// Mock the API module
vi.mock('./api', () => ({
  createSession: vi.fn(),
  sendChatMessage: vi.fn(),
  fetchDocument: vi.fn().mockResolvedValue("<p>Mock document HTML</p>"),
}));

const mockState = {
  full_name: { value: null, status: 'missing' as const },
  home_address: { value: null, status: 'missing' as const },
  covers_worldwide_assets: { value: null, status: 'missing' as const },
  has_children: { value: null, status: 'missing' as const },
  children_names: { value: null, status: 'missing' as const },
  executor: {
    name: { value: null, status: 'missing' as const },
    relationship: { value: null, status: 'missing' as const },
  },
  specific_gifts: { value: null, status: 'missing' as const },
  additional_wishes: { value: null, status: 'missing' as const },
};

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially and then chat UI', async () => {
    vi.mocked(api.createSession).mockResolvedValueOnce({
      session_id: 'test-session',
      message: 'Hello! I am the assistant.',
      state: mockState,
    });

    render(<App />);

    expect(screen.getByText(/Starting session.../i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Hello! I am the assistant.')).toBeInTheDocument();
    });
    
    expect(screen.getByText('Document Intake Assistant')).toBeInTheDocument();
    expect(screen.getByText(/Intake Progress/i)).toBeInTheDocument();
  });

  it('handles sending a message', async () => {
    vi.mocked(api.createSession).mockResolvedValueOnce({
      session_id: 'test-session',
      message: 'Hello!',
      state: mockState,
    });

    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('Hello!')).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText('Type your message...');
    const sendButton = screen.getByText('Send');

    fireEvent.change(input, { target: { value: 'My name is Alice' } });
    
    vi.mocked(api.sendChatMessage).mockResolvedValueOnce({
      session_id: 'test-session',
      assistant_message: 'Nice to meet you, Alice.',
      clarification_needed: null,
      state: {
        ...mockState,
        full_name: { value: 'Alice', status: 'confirmed' },
      }
    });

    fireEvent.click(sendButton);

    // User message should appear immediately
    expect(screen.getByText('My name is Alice')).toBeInTheDocument();
    
    // Assistant message should appear after mock resolves
    await waitFor(() => {
      expect(screen.getByText('Nice to meet you, Alice.')).toBeInTheDocument();
    });
  });

  it('shows API error if session creation fails', async () => {
    // Suppress console.error for this expected failure
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    vi.mocked(api.createSession).mockRejectedValueOnce(new Error('Network error'));

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to start session/i)).toBeInTheDocument();
    });
    
    consoleSpy.mockRestore();
  });
});
