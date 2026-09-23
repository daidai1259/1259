"use client";
import "./viewer.css";
import { useEffect, useMemo, useState } from "react";

type Page={id:number;drawing_id:number;page_number:number;image_name:string;thumbnail_name?:string|null;width:number;height:number;drawing_number?:string|null;drawing_title?:string|null;scale_text?:string|null};
type Issue={id:number;severity:string;title:string;description:string;page_id?:number|null;x0?:number|null;y0?:number|null;x1?:number|null;y1?:number|null;status:string};

const API=process.env.NEXT_PUBLIC_API_BASE_URL||"http://localhost:8000";

export default function DrawingViewer(){
 const [page,setPage]=useState(1),[zoom,setZoom]=useState(1),[selected,setSelected]=useState<Issue|null>(null);
 const [pages,setPages]=useState<Page[]>([]),[issues,setIssues]=useState<Issue[]>([]),[loading,setLoading]=useState(true),[error,setError]=useState("");
 const updateIssueStatus=async(id:number,status:string)=>{try{const r=await fetch(`${API}/api/review-issues/${id}`,{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify({status})});if(!r.ok)return;const updated=await r.json();setIssues(xs=>xs.map(x=>x.id===id?updated:x));setSelected(x=>x?.id===id?updated:x)}catch{}};
 const current=pages[page-1];
 useEffect(()=>{const id=window.location.pathname.split("/").filter(Boolean).pop(); if(!id)return;
  fetch(`${API}/api/drawings/${id}/page-summaries`).then(r=>r.ok?r.json():Promise.reject()).then(ps=>{setPages(ps);setLoading(false)}).catch(()=>{setError("无法连接审核 API，请确认后端已启动。");setLoading(false)});
 },[]);
 const pageIssues=useMemo(()=>issues.filter(i=>i.page_id===current?.id),[issues,current]);
 useEffect(()=>{if(!current)return; setSelected(null);
  fetch(`${API}/api/drawings/${current.drawing_id}/issues`).then(r=>r.ok?r.json():[]).then(setIssues).catch(()=>{});
 },[current?.drawing_id]);
 if(loading)return <main className="viewer-shell"><div className="viewer-loading">正在加载真实图纸数据…</div></main>;
 if(error)return <main className="viewer-shell"><div className="viewer-loading">{error}</div></main>;
 if(!current)return <main className="viewer-shell"><div className="viewer-loading">暂无可查看页面。</div></main>;
 return <main className="viewer-shell">
  <header className="viewer-top"><div><b>1259</b><span> / 图纸查看器</span></div><div className="viewer-title">{current.drawing_number||"未识别图号"} · {current.drawing_title||"未命名图纸"}</div><button onClick={()=>history.back()}>返回项目</button></header>
  <div className="viewer-body">
   <aside className="page-list"><h3>图纸目录</h3>{pages.map(p=><button className={page===p.page_number?"page-card active":"page-card"} onClick={()=>{setPage(p.page_number);setZoom(1)}} key={p.id}><img src={`${API}/api/drawing-pages/${p.id}/thumbnail`} alt="" /><div><b>{p.drawing_number||`第 ${p.page_number} 页`}</b><span>{p.drawing_title||"未识别标题"}</span><small>第 {p.page_number} 页 · {p.scale_text||"比例待识别"}</small></div></button>)}</aside>
   <section className="canvas-area"><div className="toolbar"><span>第 {page} / {pages.length} 页</span><button onClick={()=>setZoom(z=>Math.max(.5,z-.1))}>−</button><b>{Math.round(zoom*100)}%</b><button onClick={()=>setZoom(z=>Math.min(2,z+.1))}>＋</button><button onClick={()=>setZoom(1)}>适应</button></div><div className="canvas"><div className="drawing-paper" style={{transform:`scale(${zoom})`}}><img src={`${API}/api/drawing-pages/${current.id}/image`} alt={current.drawing_title||"施工图"} />{pageIssues.map(i=>i.x0!=null&&i.y0!=null&&i.x1!=null&&i.y1!=null&&<button key={i.id} className={selected?.id===i.id?"issue-box selected":"issue-box"} style={{left:`${i.x0*100}%`,top:`${i.y0*100}%`,width:`${(i.x1-i.x0)*100}%`,height:`${(i.y1-i.y0)*100}%`}} onClick={()=>setSelected(i)} aria-label={i.title}/>)}</div></div></section>
   <aside className="issue-panel"><div className="panel-head"><h3>问题清单</h3><span>{issues.length} 项</span></div>{issues.map(i=><button key={i.id} className={selected?.id===i.id?"issue-item selected":"issue-item"} onClick={()=>{setSelected(i);const idx=pages.findIndex(p=>p.id===i.page_id);if(idx>=0)setPage(idx+1)}}><span className={"severity "+(i.severity==="high"?"高":i.severity==="medium"?"中":"低")}>{i.severity==="high"?"高":i.severity==="medium"?"中":"低"}</span><div><b>{i.title}</b><small>{i.page_id===current.id?"当前页面":"其他页面"}</small></div></button>)}{selected&&<div className="issue-detail"><small>问题详情</small><h4>{selected.title}</h4><p>{selected.description}</p><div className="detail-meta">审核状态 · {selected.status}</div><div className="status-actions"><button onClick={()=>updateIssueStatus(selected.id,"confirmed")}>确认</button><button onClick={()=>updateIssueStatus(selected.id,"fixed")}>已整改</button><button onClick={()=>updateIssueStatus(selected.id,"rejected")}>驳回</button></div><button className="close-detail" onClick={()=>setSelected(null)}>关闭详情</button></div>}</aside>
  </div>
 </main>
}