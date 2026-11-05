import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e', timeout:240_000, workers:1,
  use:{baseURL:'http://127.0.0.1:18765', channel:'msedge', headless:true, trace:'retain-on-failure'},
  webServer:{command:'.venv\\Scripts\\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 18765', cwd:'..',
    url:'http://127.0.0.1:18765', reuseExistingServer:false, timeout:60_000,
    env:{ACCESS_MODE:'local',CHROMA_PATH:`./data/browser-tests-${Date.now()}`,COLLECTION_NAME:'browser_documents',MEMORY_COLLECTION_NAME:'browser_memory',TRACE_LOG_PATH:'./logs/browser-tests.jsonl'}},
});
