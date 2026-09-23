"use client";

import { ChangeEvent, useState } from "react";

const initialProjects = [
  { name: "示例办公楼项目", disciplines: "建筑 · 结构 · 给排水 · 电气", status: "待审核" },
  { name: "住宅楼施工图", disciplines: "建筑 · 结构", status: "审核中" },
];

export default function Home() {
  const [projects, setProjects] = useState(initialProjects);
  const [selectedFile, setSelectedFile] = useState("");
  const [message, setMessage] = useState("");

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (!["application/pdf", "image/jpeg", "image/png"].includes(file.type)) {
      setMessage("文件格式不支持，请上传 PDF、JPG 或 PNG。"); return;
    }
    if (file.size > 50 * 1024 * 1024) {
      setMessage("文件超过 50MB，请选择较小的文件。"); return;
    }
    setSelectedFile(file.name);
    setMessage("文件已选择。真实上传接口将在后端接入后启用。");
  }

  function createProject() {
    const name = window.prompt("请输入项目名称");
    if (!name?.trim()) return;
    setProjects((items) => [{ name: name.trim(), disciplines: "待配置专业", status: "待审核" }, ...items]);
    setMessage(`项目“${name.trim()}”已创建。`);
  }

  return (
    <main className="page">
      <aside className="sidebar">
        <div className="brand">AI审图</div>
        <nav>
          <a className="active" href="#">工作台</a>
          <a href="#projects">项目管理</a>
          <a href="#drawings">图纸管理</a>
          <a href="#reviews">审核任务</a>
          <a href="#reports">审核报告</a>
        </nav>
        <div className="side-note">AI辅助审图 · MVP</div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div><span className="eyebrow">CONSTRUCTION REVIEW AI</span><h1>施工图审核工作台</h1><p>上传图纸、创建项目并准备 AI 审核任务。</p></div>
          <button className="primary" onClick={createProject}>＋ 新建审核项目</button>
        </header>

        {message && <div className="notice">{message}</div>}

        <section className="stats">
          <div className="stat"><span>项目数量</span><strong>{projects.length}</strong></div>
          <div className="stat"><span>待审核项目</span><strong>{projects.filter((p) => p.status === "待审核").length}</strong></div>
          <div className="stat"><span>已选图纸</span><strong>{selectedFile ? "1" : "0"}</strong></div>
        </section>

        <section className="grid">
          <div className="card large" id="projects">
            <div className="card-head"><div><h2>项目</h2><p>创建并管理施工图审核项目</p></div><button className="ghost" onClick={createProject}>新建项目</button></div>
            {projects.map((project) => <div className="project" key={project.name}><div className="icon">{project.name.slice(0, 1)}</div><div className="project-main"><strong>{project.name}</strong><span>{project.disciplines}</span></div><div className={`status ${project.status === "审核中" ? "reviewing" : ""}`}>{project.status}</div></div>)}
          </div>

          <div className="card upload" id="drawings">
            <div className="upload-mark">↑</div>
            <h2>选择施工图</h2>
            <p>支持 PDF、JPG、PNG，单文件不超过 50MB</p>
            <label className="primary wide file-button">选择图纸文件<input type="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" onChange={chooseFile} /></label>
            {selectedFile && <div className="selected-file">已选择：{selectedFile}</div>}
            <small>当前为前端选择与校验；真实文件上传将在后端完成。</small>
          </div>
        </section>

        <section className="card" id="reviews">
          <div className="card-head"><div><h2>审核任务</h2><p>真实任务队列将在后端接入后启用</p></div></div>
          <div className="empty">尚未创建真实审核任务。</div>
        </section>

        <section className="card" id="reports">
          <div className="card-head"><div><h2>审核报告</h2><p>AI 发现的问题将按风险等级归档</p></div></div>
          <div className="empty">暂无真实审核报告。</div>
        </section>

        <footer>AI施工图审核平台 · MVP · 审核结果仅供辅助参考，不替代注册工程师、施工图审查机构或法定审批。</footer>
      </section>
    </main>
  );
}
