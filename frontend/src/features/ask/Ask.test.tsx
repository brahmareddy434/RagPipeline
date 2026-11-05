import {fireEvent,render,screen,waitFor,cleanup} from '@testing-library/react';
import {afterEach,expect,test,vi} from 'vitest';
import {Ask} from './Ask';
import {ApiClient} from '../../lib/api';
afterEach(cleanup);
test('source requests use the authenticated client and expose expired source errors',async()=>{
  const api=new ApiClient();
  vi.spyOn(api,'post').mockResolvedValue({answer:'Deductible 500',abstained:false,confidence:'medium',validation_issues:[],citations:[{chunk_id:'exact-version',source:'p.txt',quote:'Deductible 500'}]});
  const source=vi.spyOn(api,'request').mockRejectedValue(new Error('Source replaced.'));
  render(<Ask api={api}/>); fireEvent.click(screen.getByRole('button',{name:'Ask policy'}));
  fireEvent.click(await screen.findByRole('button',{name:'View source: p.txt'}));
  await waitFor(()=>expect(source).toHaveBeenCalledWith('/sources/exact-version',expect.objectContaining({signal:expect.any(AbortSignal)})));
  expect((await screen.findByRole('alert')).textContent).toBe('Source replaced.');
  expect(screen.getByText('Source replaced.')).toBeTruthy();
});
