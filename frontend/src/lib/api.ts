export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

export class ApiClient {
  constructor(private token = '', private base = '/api/v1') {}
  async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers = new Headers(options.headers);
    if (this.token) headers.set('Authorization', `Bearer ${this.token}`);
    if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json');
    const signal = options.signal || AbortSignal.timeout(300_000);
    const response = await fetch(this.base + path, { ...options, headers, signal, credentials: 'omit' });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const detail = Array.isArray(body.detail) ? body.detail.map((e: {msg: string}) => e.msg).join('; ') : body.detail;
      throw new ApiError(typeof detail === 'string' ? detail : `Request failed (${response.status})`, response.status);
    }
    return body as T;
  }
  post<T>(path: string, body: unknown, signal?: AbortSignal): Promise<T> {
    return this.request<T>(path, { method: 'POST', body: JSON.stringify(body), signal });
  }
}
