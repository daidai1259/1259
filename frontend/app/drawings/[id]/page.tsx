"use client";
import "./viewer.css";
import { useState } from "react";

type Page={id:number;page_number:number;image_name:string;thumbnail_name?:string|null;width:number;height:number;drawing_number?:string|null;drawing_title?:string|null;scale_text?:string|null};
type Issue={id:number;severity:string;title:string;description:string;page_id?:number|null;x0?:number|null;y0?:number|null;x1?:number|null;y1?:number|null;status:string};

export default function DrawingViewer(){
 const [page,setPage]=useState(1);
 const [zoom,setZoom]=useState(1);
 const [selected,setSelected]=useState<Issue|null>(null);
 const pages:Page[]=[
  {id:1,page_number:1,image_name:"",thumbnail_name:null,width:1600,height:1100,drawing_number:"A-101",drawing_title:"建筑首层平面图",scale_text:"1:100"},
  {id:2,page_number:2,image_name:"",thumbnail_name:null,width:1600,height:1100,drawing_number:"A-102",drawing_title:"建筑二层平面图",scale_text:"1:100"}
 ];
 const issues:Issue[]=[
  {id:1,severity:"高",title:"楼梯间防火门开启方向需复核",description:"请结合防火分区、疏散方向及门扇开启范围进行专业复核。",page_id:1,x0:48,y0:31,x1:61,y1:43,status:"open"},
  {id:2,severity:"中",title:"图签信息待确认",description:"当前页面比例已识别，但部分图签字段需要人工确认。",page_id:1,x0:82,y0:84,x1:97,y1:97,status:"open"}
 ];
 const current=pages[page-1];
 return <main className="viewer-shell">
  <header className="viewer-top"><div><b>1259</b><span> / 图纸查看器</span></div><div className="viewer-title">{current.drawing_number} · {current.drawing_title}</div><button>返回项目</button></header>
  <div className="viewer-body">
   <aside className="page-list"><h3>图纸目录</h3>{pages.map(p=><button className={page===p.page_number?"page-card active":"page-card"} onClick={()=>{setPage(p.page_number);setSelected(null)}} key={p.id}><div className="thumb-placeholder">A</div><div><b>{p.drawing_number}</b><span>{p.drawing_title}</span><small>第 {p.page_number} 页</small></div></button>)}</aside>
   <section className="canvas-area"><div className="toolbar"><span>第 {page} / {pages.length} 页</span><button onClick={()=>setZoom(z=>Math.max(.5,z-.1))}>−</button><b>{Math.round(zoom*100)}%</b><button onClick={()=>setZoom(z=>Math.min(2,z+.1))}>＋</button><button onClick={()=>setZoom(1)}>适应</button></div><div className="canvas"><div className="drawing-paper" style={{transform:`scale(${zoom})`}}><div className="drawing-grid"/><div className="fake-plan"><div className="room r1">客厅</div><div className="room r2">卧室</div><div className="room r3">楼梯间</div><div className="room r4">卫生间</div><div className="axis">A</div><div className="axis b">B</div></div>{issues.filter(i=>i.page_id===current.id).map(i=><button key={i.id} className={selected?.id===i.id?"issue-box selected":"issue-box"} style={{left:`${i.x0}%`,top:`${i.y0}%`,width:`${(i.x1||i.x0||0)-(i.x0||0)}%`,height:`${(i.y1||i.y0||0)-(i.y0||0)}%`}} onClick={()=>setSelected(i)} aria-label={i.title}/>)}</div></div></section>
   <aside className="issue-panel"><div className="panel-head"><h3>问题清单</h3><span>{issues.length} 项</span></div>{issues.map(i=><button key={i.id} className={selected?.id===i.id?"issue-item selected":"issue-item"} onClick={()=>{setSelected(i);if(i.page_id)setPage(i.page_id)}}><span className={"severity "+i.severity}>{i.severity}</span><div><b>{i.title}</b><small>{i.page_id===current.id?"当前页面":"其他页面"}</small></div></button>)}{selected&&<div className="issue-detail"><small>问题详情</small><h4>{selected.title}</h4><p>{selected.description}</p><div className="detail-meta">规则定位 · 页面 {selected.page_id}</div><button className="close-detail" onClick={()=>setSelected(null)}>关闭详情</button></div>}</aside>
  </div>
 </main>
}