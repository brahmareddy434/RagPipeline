"""Exercise live demo HTTP routes; retain actual fictional responses in a new directory."""
import argparse
import asyncio
import json
from pathlib import Path

import httpx

from app.agents.claims import task_for


async def run(base_url, output):
    output.mkdir(parents=True, exist_ok=False)
    async with httpx.AsyncClient(base_url=base_url, timeout=240, trust_env=False) as client:
        for week in (8, 9):
            task = task_for('CLM-2026-10004') if week == 8 else 'What is the current status of claim CLM-2024-88120?'
            path = '/claims/demo/run' if week == 8 else '/mcp/demo/run'
            for variant in ('before', 'after'):
                reply = await client.post('/api/v1' + path, json={'task': task, 'variant': variant})
                reply.raise_for_status()
                result = reply.json()
                (output / f'week{week}-{variant}.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
                r = result['run']
                print(json.dumps({'week': week, 'variant': variant, 'answer': r['answer'],
                    'stop': r['stop_reason'], 'tokens': r['usage']['total_tokens'],
                    'tools': [s['tool'] for s in r['steps']]}), flush=True)
        reply = await client.post('/api/v1/claims/demo/run', json={
            'task': task_for('CLM-2026-10004'), 'variant': 'after', 'injection': True})
        reply.raise_for_status()
        result = reply.json()
        (output / 'week8-injection.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps({'injection': result['diagnostics'], 'answer': result['run']['answer']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    asyncio.run(run(args.base_url, args.output))
