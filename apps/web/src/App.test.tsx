import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import App from './App';

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  localStorage.removeItem('aegisos_token');
});

describe('AegisOS auth shell', () => {
  it('renders sign in and a valid local demo account hint when logged out', () => {
    localStorage.removeItem('aegisos_token');
    render(<App />);
    expect(screen.getByRole('heading', { name: /build with confidence/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /sign in to aegisos/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/email/i)).toHaveValue('demo@aegisos.dev');
  });

  it('shows a readable validation error when login is rejected', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [{ loc: ['body', 'email'], msg: 'Enter a valid email address', type: 'value_error' }],
      }),
    });
    vi.stubGlobal('fetch', fetchMock);
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /sign in to aegisos/i }));
    expect(await screen.findByText(/email: enter a valid email address/i)).toBeInTheDocument();
  });

  it('shows a network hint if the API cannot be reached', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')));
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /sign in to aegisos/i }));
    await waitFor(() => expect(screen.getByText(/cannot reach the aegisos api/i)).toBeInTheDocument());
  });
});
