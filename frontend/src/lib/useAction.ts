import { useEffect, useRef, useState } from 'react';

export function useAction<T>() {
  const [data, setData] = useState<T>();
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);
  async function run(task: (signal: AbortSignal) => Promise<T>) {
    pending.current?.abort();
    const controller = new AbortController(); pending.current = controller;
    setBusy(true); setError(''); setData(undefined);
    try {
      const value = await task(controller.signal);
      if (!controller.signal.aborted) setData(value);
      return value;
    } catch (e) {
      if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'The request failed.');
    } finally {
      if (pending.current === controller) setBusy(false);
    }
  }
  return { data, error, busy, run, cancel: () => { pending.current?.abort(); setBusy(false); } };
}
