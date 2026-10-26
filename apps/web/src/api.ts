const API = import.meta.env.VITE_API_URL ?? `http://${typeof window !== 'undefined' && window.location.hostname === '127.0.0.1' ? '127.0.0.1' : 'localhost'}:8000`;
export type Task = {id:number;title:string;issue:string;acceptance_criteria:string[];language:string;status:string;verdict:string|null;patch:string|null;error_message:string|null;budget_usd:number;cost_usd:number;latency_ms:number|null;created_at:string};
export type Dashboard = {total_tasks:number;active_tasks:number;completed_tasks:number;failed_tasks:number;success_rate:number|null;avg_latency_ms:number|null;total_cost_usd:number;provider:string;sandbox_enabled:boolean;recent_runs:Task[]};
export type Repo = {id:number;name:string;workspace_path:string;language:string};
let token = localStorage.getItem('aegisos_token') ?? '';
export function setToken(value:string){token=value; if(value)localStorage.setItem('aegisos_token',value);else localStorage.removeItem('aegisos_token');}
export function getToken(){return token;}
function readableError(detail: unknown, status: number): string {
 if (typeof detail === 'string' && detail.trim()) return detail;
 if (Array.isArray(detail)) {
  const messages = detail.map((item: any) => {
   if (typeof item === 'string') return item;
   if (item && typeof item.msg === 'string') {
    const location = Array.isArray(item.loc) ? item.loc.filter((part: unknown) => part !== 'body').join('.') : '';
    return location ? `${location}: ${item.msg}` : item.msg;
   }
   return '';
  }).filter(Boolean);
  if (messages.length) return messages.join('; ');
 }
 return `Request failed (HTTP ${status})`;
}
async function request<T>(path:string,init:RequestInit={}):Promise<T>{
 const headers=new Headers(init.headers);headers.set('Content-Type','application/json');if(token)headers.set('Authorization',`Bearer ${token}`);
 let res: Response;
 try { res=await fetch(`${API}${path}`,{...init,headers}); }
 catch { throw new Error(`Cannot reach the AegisOS API at ${API}. Make sure the backend is running and open the UI at localhost:5173 or 127.0.0.1:5173.`); }
 if(!res.ok){const body=await res.json().catch(()=>({detail:'Request failed'}));throw new Error(readableError(body?.detail,res.status));}
 return res.json();
}
export const api={login:(email:string,password:string)=>request<{access_token:string}>('/api/auth/login',{method:'POST',body:JSON.stringify({email,password})}),register:(email:string,password:string)=>request<{access_token:string}>('/api/auth/register',{method:'POST',body:JSON.stringify({email,password})}),me:()=>request<{id:number;email:string}>('/api/auth/me'),dashboard:()=>request<Dashboard>('/api/dashboard'),tasks:()=>request<Task[]>('/api/tasks?limit=100'),task:(id:number)=>request<Task>(`/api/tasks/${id}`),events:(id:number)=>request<any[]>(`/api/tasks/${id}/events`),trace:(id:number)=>request<any>(`/api/tasks/${id}/trace`),cancel:(id:number)=>request(`/api/tasks/${id}/cancel`,{method:'POST'}),rerun:(id:number)=>request<Task>(`/api/tasks/${id}/rerun`,{method:'POST'}),createTask:(data:unknown)=>request<Task>('/api/tasks',{method:'POST',body:JSON.stringify(data)}),repos:()=>request<Repo[]>('/api/repositories'),createRepo:(data:unknown)=>request<Repo>('/api/repositories',{method:'POST',body:JSON.stringify(data)}),experiments:()=>request<any[]>('/api/experiments'),createExperiment:(data:unknown)=>request<any>('/api/experiments',{method:'POST',body:JSON.stringify(data)}),experiment:(id:number)=>request<any>(`/api/experiments/${id}`)};
