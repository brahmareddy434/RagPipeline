import {test,expect} from '@playwright/test';

const run={task:'fixture',answer:'Under review; dated photographs needed.',abstained:false,stop_reason:'finished',stop_detail:'Recorded test response.',usage:{latency_ms:1000,total_tokens:100,cost_usd:.00002},steps:[{tool:'get_claim_record',arguments:{},ok:true}],citations:[],evidence:[]};

test('Week 8 submits the same typed query and injection setting to both arms',async({page})=>{
  const calls:Record<string,unknown>[]=[];
  await page.route('**/api/v1/claims/demo/run',async route=>{
    const body=route.request().postDataJSON();calls.push(body);
    await route.fulfill({json:{task:body.task,variant:body.variant,run,notice:'Fresh test response',diagnostics:{tool_errors:0,repeated_calls:1,injection_enabled:true,injection_delivered:true,attack_marker_in_answer:false}}});
  });
  await page.goto('/#/demo/week8');
  await page.getByLabel('Your question').fill('What is missing for CLM-2026-10001?');
  await page.getByLabel('Append a prompt-injection test note').check();
  await page.getByRole('button',{name:'Run before and after',exact:true}).click();
  await expect(page.getByRole('heading',{name:'After answer and tool trace'})).toBeVisible();
  expect(calls).toEqual([
    {task:'What is missing for CLM-2026-10001?',variant:'before',injection:true},
    {task:'What is missing for CLM-2026-10001?',variant:'after',injection:true},
  ]);
  await expect(page.getByText('marker absence alone does not prove safety.',{exact:false}).first()).toBeVisible();
  await page.getByText('Tool trajectory (1 steps)').first().click();
  await expect(page.getByText('get_claim_record',{exact:false}).first()).toBeVisible();
});

test('Week 8 shows validation errors and labels saved evidence separately',async({page})=>{
  await page.route('**/api/v1/claims/demo/run',route=>route.fulfill({status:400,json:{detail:'Include exactly one fictional claim ID.'}}));
  await page.route('**/api/v1/claims/benchmarks/*/agent/C04',route=>route.fulfill({json:{run}}));
  await page.goto('/#/demo/week8');
  await page.getByLabel('Your question').fill('No claim ID');
  await page.getByRole('button',{name:'Run before only'}).click();
  await expect(page.getByRole('alert')).toContainText('Include exactly one fictional claim ID.');
  await page.getByRole('button',{name:'Show saved C04 before and after'}).click();
  await expect(page.getByRole('heading',{name:'Saved baseline C04'})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Saved mitigation C04'})).toBeVisible();
});

test('Week 9 discovers both configurations and runs the identical query',async({page})=>{
  const calls:Record<string,unknown>[]=[];
  await page.route('**/api/v1/mcp/demo/tools?*',route=>{
    const after=route.request().url().includes('after');
    return route.fulfill({json:{count:after?4:2,names:after?['policy__read_policy','claims__get_claim_status']:['policy__read_policy'],tools_list_responses:[]}});
  });
  await page.route('**/api/v1/mcp/demo/run',route=>{
    const body=route.request().postDataJSON();calls.push(body);
    return route.fulfill({json:{task:body.task,run:{...run,answer:body.variant==='before'?'No claim status evidence.':'Awaiting repair estimate.'},notice:'Fresh test response'}});
  });
  await page.goto('/#/demo/week9');
  await page.getByRole('button',{name:'Discover before and after tools'}).click();
  await expect(page.getByRole('heading',{name:'before: 2 tools'})).toBeVisible();
  await expect(page.getByRole('heading',{name:'after: 4 tools'})).toBeVisible();
  await page.getByRole('button',{name:'Run before and after',exact:true}).click();
  await expect(page.getByText('Awaiting repair estimate.',{exact:true})).toBeVisible();
  expect(calls[0].task).toBe(calls[1].task);
  expect(calls.map(c=>c.variant)).toEqual(['before','after']);
});

test('cancelling the first arm does not submit the second arm',async({page})=>{
  const calls:string[]=[];
  let release:()=>void=()=>{};
  const gate=new Promise<void>(resolve=>{release=resolve;});
  await page.route('**/api/v1/claims/demo/run',async route=>{
    calls.push(route.request().postDataJSON().variant);
    await gate;
    await route.fulfill({json:{task:run.task,run,notice:'Test response'}}).catch(()=>{});
  });
  await page.goto('/#/demo/week8');
  await page.getByRole('button',{name:'Run before and after',exact:true}).click();
  await expect.poll(()=>calls.length).toBe(1);
  await page.getByRole('button',{name:'Cancel',exact:true}).click();
  release();
  await expect(page.getByRole('button',{name:'Run before and after',exact:true})).toBeEnabled();
  await page.getByRole('link',{name:'Week 9 live demo'}).click();
  await expect(page.getByLabel('Your question')).toHaveValue('What is the current status of claim CLM-2024-88120?');
  expect(calls).toEqual(['before']);
});
