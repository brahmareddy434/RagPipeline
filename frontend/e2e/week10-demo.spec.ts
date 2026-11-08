import {test,expect} from '@playwright/test';

test('Week 10 mentor page calls paired arms with the same edited query and shows failure and artifacts',async({page})=>{
  const posts:{url:string;body:any}[]=[];
  await page.route('**/api/v1/claims/team/agent-card',route=>route.fulfill({json:{protocolVersion:'1.0.0',name:'Local claims team',defaultInputModes:['application/json'],defaultOutputModes:['application/json'],skills:[],securitySchemes:{},security:[]}}));
  await page.route('**/api/v1/claims/team/race/latest',route=>route.fulfill({json:{generated_at_utc:'saved run',manifest:{case_ids:['C01'],cohort_provenance:'provisional Week-7/8',exact_week6_cohort:false},single:{},team:{},context_resend_multiplier:.1,dominant_handoff:'manager->coverage_worker',dominant_handoff_share_percent:53.2,artifacts:{'race_table.md':'saved race metrics','handoffs.log':'saved handoff tokens','failure_case.md':'saved HTTP 500','verdict.md':'saved sunk-cost verdict','run_id':'saved-run'}}}));
  await page.route('**/api/v1/claims/team/run',async route=>{
    const body=route.request().postDataJSON();posts.push({url:route.request().url(),body});
    const run={task:body.task,answer:body.arm==='failure'?'Claim coverage remains undetermined.':'Status awaiting documents; repair estimate missing.',abstained:body.arm==='failure',stop_reason:body.arm==='failure'?'worker_error':'finished',stop_detail:'test fixture',usage:{total_tokens:200,latency_ms:20,cost_usd:.0001,worker_failures:body.arm==='failure'?[{status_code:500}]:[]},steps:[],citations:[],evidence:[]};
    await route.fulfill({json:{claim_id:body.claim_id,provenance:'fictional fixture',arm:body.arm,...(body.arm==='both'?{single:run,team:run}:{team:run,task_state:'failed'})}});
  });
  await page.route('**/api/v1/claims/team/race',route=>route.fulfill({json:{generated_at_utc:'test',manifest:{case_ids:['C01'],cohort_provenance:'provisional Week-7/8',exact_week6_cohort:false},single:{},team:{},context_resend_multiplier:2.3,dominant_handoff:'manager->coverage_worker',dominant_handoff_share_percent:41,artifacts:{'race_table.md':'paired metrics','handoffs.log':'tokens by handoff','failure_case.md':'HTTP 500','verdict.md':'Sunk-cost bias','run_id':'fixture-run'}}}));
  await page.goto('/#/demo/week10');
  await expect(page.getByText(/no identified ten-case Week-6/)).toBeVisible();
  await expect(page.getByText('saved race metrics')).toBeVisible();
  const query=page.getByLabel('Question sent to both arms');await query.fill('Summarize claim CLM-2026-10001 and its missing estimate.');
  await page.getByRole('button',{name:'Run single and team'}).click();
  await expect(page.getByRole('heading',{name:'Before: single agent'})).toBeVisible();
  expect(posts[0].body.task).toBe(await query.inputValue());
  await page.getByRole('button',{name:'Inject coverage worker 500'}).click();
  await expect(page.getByRole('heading',{name:'Injected failure result'})).toBeVisible();
  await page.getByRole('button',{name:'Run a new ten-case race'}).click();
  await expect(page.getByText('paired metrics')).toBeVisible();
  await expect(page.getByText(/largest hand-off:/)).toBeVisible();
});
