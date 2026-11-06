import { afterEach, describe, expect, it, vi } from 'vitest';
import { ApiClient } from './api';

afterEach(() => vi.unstubAllGlobals());
describe('API boundary', () => {
  it('uses a scoped header and preserves cancellation', async () => {
    const fetcher = vi.fn().mockResolvedValue({ok: true, json: async () => ({tool: 'calculator', result: 5})});
    vi.stubGlobal('fetch', fetcher);
    const controller = new AbortController();
    await new ApiClient('test-only').post('/tools/run', {question: '2+3'}, controller.signal);
    const [url, options] = fetcher.mock.calls[0];
    expect(url).toBe('/api/v1/tools/run');
    expect(options.headers.get('Authorization')).toBe('Bearer test-only');
    expect(options.signal).toBe(controller.signal);
    expect(options.credentials).toBe('omit');
  });
  it('turns validation details into a readable failure', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ok:false, status:422, json:async () => ({detail:[{msg:'Question is required'}]})}));
    await expect(new ApiClient().post('/tools/run', {})).rejects.toThrow('Question is required');
  });
});
