import {test,expect} from '@playwright/test';

const run={answer:'Under review; estimate missing.',abstained:false,stop_reason:'finished',stop_detail:'Evidence gathered.',usage:{model_calls:1,total_tokens:22},steps:[{index:1,tool:'get_claim_record',ok:true}],citations:[],evidence:[]};

test('claims comparison page renders the same-claim agent and workflow traces',async({page})=>{
  await page.route('**/api/v1/claims/fixtures',route=>route.fulfill({json:{provenance:'fictional',claims:[{claim_id:'CLM-2026-10001',status:'awaiting_documents'}],tools:[]}}));
  await page.route('**/api/v1/claims/run',route=>route.fulfill({json:{claim_id:'CLM-2026-10001',agent:run,workflow:{...run,steps:[{index:1,tool:'get_claim_record',ok:true},{index:2,tool:'get_adjuster_notes',ok:true}]}}}));
  await page.goto('/#/runs');
  await page.getByRole('button',{name:'Compare approaches'}).click();
  await expect(page.getByRole('heading',{name:'Agent',exact:true})).toBeVisible();
  await expect(page.getByRole('heading',{name:'Fixed workflow',exact:true})).toBeVisible();
  await page.getByText('Tool trajectory (2 steps)').click();
  await expect(page.getByText('get_adjuster_notes')).toBeVisible();
});

test('MCP page renders discovered tools and host model trace',async({page})=>{
  await page.route('**/api/v1/mcp/tools',route=>route.fulfill({json:{count:1,names:['claims__get_claim_status'],tools_list_responses:[]}}));
  await page.route('**/api/v1/mcp/agent/run',route=>route.fulfill({json:{discovery:[],run,trace_id:'trace-fixture'}}));
  await page.goto('/#/mcp');
  await expect(page.getByText('claims__get_claim_status')).toBeVisible();
  await page.getByRole('button',{name:'Run discovered tools'}).click();
  await expect(page.getByRole('heading',{name:'MCP host run'})).toBeVisible();
  await page.getByText('Tool trajectory (1 steps)').click();
  await expect(page.getByText('get_claim_record')).toBeVisible();
});

test('versioned benchmark screen renders metrics, comparison and case trace',async({page})=>{
  const metrics={outcome_pass_rate:.5,trajectory_pass_rate:0,outcome_minus_trajectory_gap:.5,p50_latency_ms:74000,total_tokens:62000,mean_cost_per_claim_usd:.0014,cost_p50_usd:.0014,cost_max_usd:.0017,tool_choice_accuracy:.95,argument_validity:.93,step_efficiency:.79,modes:{repeated_calls:8}};
  await page.route('**/api/v1/claims/benchmarks',route=>route.fulfill({json:{reports:{'baseline-r4':{agent:metrics},'mitigation-r4':{agent:metrics}},comparison:{only_change:'one prompt instruction'},notice:'Fictional fixture report.'}}));
  await page.route('**/api/v1/claims/benchmarks/baseline-r4/agent/C01',route=>route.fulfill({json:{case_id:'C01',assessment:{mode:'repeated_calls'},run}}));
  await page.goto('/#/benchmarks');
  await expect(page.getByRole('heading',{name:'Trajectory benchmarks'})).toBeVisible();
  await expect(page.getByRole('heading',{name:'baseline-r4'})).toBeVisible();
  await page.getByText('Single mitigation: regressions and measured price').click();
  await expect(page.getByText('one prompt instruction')).toBeVisible();
  await page.getByRole('button',{name:'C01'}).first().click();
  await expect(page.getByRole('heading',{name:'C01',exact:true})).toBeVisible();
});
