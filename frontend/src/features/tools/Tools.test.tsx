import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, expect, it, vi } from 'vitest';
import { ApiClient } from '../../lib/api';
import { Tools } from './Tools';

afterEach(cleanup);
it('shows the validated tool result and execution owner', async () => {
  const api = new ApiClient(); vi.spyOn(api,'post').mockResolvedValue({tool:'calculator',result:2000,executed_by:'Python'});
  render(<Tools api={api}/>); fireEvent.click(screen.getByText('Run tool'));
  await waitFor(() => expect(screen.getByText('2000')).toBeTruthy());
  expect(screen.getByText('Executed by Python')).toBeTruthy();
});
it('shows failures and makes retry available', async () => {
  const api = new ApiClient(); vi.spyOn(api,'post').mockRejectedValue(new Error('Provider unavailable'));
  render(<Tools api={api}/>); fireEvent.click(screen.getByText('Run tool'));
  await waitFor(() => expect(screen.getByRole('alert').textContent).toBe('Provider unavailable'));
  expect((screen.getByText('Run tool') as HTMLButtonElement).disabled).toBe(false);
});
