"use client";
import { useState } from "react";

const stats=[["12","本项目图纸"],["8","已完成解析"],["3","待处理问题"],["96%","解析完成率"]];
const drawings=[
 {no:"A-101",name:"建筑首层平面图",discipline:"建筑",status:"已解析",pages:1},
 {no:"S-201",name:"结构基础平面图",discipline:"结构",status:"已解析",pages:2},
 {no:"E-301",name:"照明平面图",discipline:"电气",status:"处理中",pages:3},
];
const issues=[
 {level:"高",title:"楼梯间防火门开启方向需复核",page:"A-101",pos:"首层平面"},
 {level:"中",title:"结构图与建筑轴网标注存在待核对项",page:"S-201",pos:"基础平面"},
 {level:"低",title:"部分图签比例未识别",page:"E-301",pos:"图签区域"},
];

export default function Home(){
 const [active,setActive]=useState("总览");
 return <main className="shell">
  <aside className="sidebar">
   <div className="brand"><div className="logo">12</div><div><b>1259</b><span>AI施工图审核</span></div></div>
   <div className="project"><small>当前项目</small><strong>滨江研发中心一期</strong><span>项目编号：BJ-2026-001</span></div>
   <nav>{["总览","图纸管理","AI审图","问题清单","审核报告"].map(x=><button className={active===x?"nav active":"nav"} onClick={()=>setActive(x)} key={x}><i>{x==="总览"?"⌂":x==="图纸管理"?"▤":x==="AI审图"?"✦":x==="问题清单"?"!":"▥"}</i>{x}</button>)}</nav>
   <div className="side-foot"><span className="dot"/>系统运行正常</div>
  </aside>
  <section className="content">
   <header><div><div className="crumb">项目 / {active}</div><h1>{active}</h1></div><div className="header-actions"><button className="ghost">导出报告</button><button className="primary">＋ 上传图纸</button></div></header>
   <div className="notice"><span>AI 辅助审图</span> 当前审核结果用于辅助校核，不替代注册工程师、施工图审查机构或法定审批。</div>
   <section className="stats">{stats.map(([n,l])=><div className="stat" key={l}><strong>{n}</strong><span>{l}</span></div>)}</section>
   <div className="grid">
    <section className="card wide"><div className="card-head"><div><h2>图纸处理进度</h2><p>最近上传与解析状态</p></div><button className="textbtn">查看全部 →</button></div>
     <div className="table">{drawings.map(d=><div className="row" key={d.no}><div className="drawing-icon">DWG</div><div className="drawing-main"><b>{d.no} · {d.name}</b><span>{d.discipline} · {d.pages} 页</span></div><span className={d.status==="处理中"?"pill blue":"pill green"}>{d.status}</span><span className="row-action">查看 →</span></div>)}</div>
    </section>
    <section className="card"><div className="card-head"><div><h2>审核概览</h2><p>规则检查与 AI 分析</p></div></div><div className="donut"><div><b>87%</b><span>完成</span></div></div><div className="legend"><span><i className="green-dot"/>已检查 8</span><span><i className="amber-dot"/>待检查 2</span><span><i className="red-dot"/>发现问题 3</span></div></section>
   </div>
   <section className="card"><div className="card-head"><div><h2>问题清单</h2><p>按严重程度与图纸位置汇总</p></div><button className="textbtn">进入问题中心 →</button></div>
    <div className="issues">{issues.map((i,n)=><div className="issue" key={n}><span className={"severity "+i.level}>{i.level}</span><div><b>{i.title}</b><span>{i.page} · {i.pos}</span></div><button>定位 →</button></div>)}</div>
   </section>
  </section>
 </main>
}