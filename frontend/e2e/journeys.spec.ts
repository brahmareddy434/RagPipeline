import {test,expect} from '@playwright/test';

test('live document upload, grounded answer, source and deletion',async({page})=>{
  await page.goto('/#/documents');
  await expect(page.getByRole('heading',{name:'Policy documents'})).toBeVisible();
  await page.getByLabel('Choose up to ten documents').setInputFiles({name:'browser-fictional-policy.txt',mimeType:'text/plain',buffer:Buffer.from('Fictional motor policy. The standard motor deductible is 500 currency units. This is a training fixture.')});
  await page.getByRole('button',{name:'Index documents'}).click();
  await expect(page.getByRole('cell',{name:'browser-fictional-policy.txt',exact:true})).toBeVisible({timeout:120_000});
  await page.getByRole('link',{name:'Policy Q&A'}).click();
  await page.getByLabel('Policy question').fill('What is the standard motor deductible?');
  await page.getByRole('button',{name:'Ask policy',exact:true}).click();
  await page.getByRole('button',{name:'View source: browser-fictional-policy.txt'}).first().click({timeout:180_000});
  await expect(page.getByRole('article',{name:'Source passage'})).toContainText('500');
  await page.getByRole('link',{name:'Documents',exact:true}).click();
  page.once('dialog',dialog=>dialog.accept());
  await page.getByRole('button',{name:'Delete browser-fictional-policy.txt'}).click();
  await expect(page.getByText('No documents indexed. Upload a policy to begin.')).toBeVisible();
});

test('live structured calculator',async({page})=>{
  await page.goto('/#/tools');
  await page.getByLabel('Question',{exact:true}).fill('Calculate 2500 - 500');
  await page.getByRole('button',{name:'Run tool'}).click();
  await expect(page.getByRole('heading',{name:'2000',exact:true})).toBeVisible({timeout:180_000});
});
