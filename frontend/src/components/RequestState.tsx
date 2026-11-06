export function RequestState({ busy, error, cancel }: {busy: boolean; error: string; cancel?: () => void}) {
  return <>
    {busy && <p role="status">Working… {cancel && <button type="button" className="secondary" onClick={cancel}>Cancel</button>}</p>}
    {error && <p role="alert" className="error">{error}</p>}
  </>;
}
