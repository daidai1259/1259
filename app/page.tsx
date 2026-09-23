const stats = [
  ["待审核图纸", "12"],
  ["发现问题", "38"],
  ["已完成项目", "6"],
];

export default function Home() {
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
        <div className="side-note">AI辅助审图 · 第一版</div>
      </aside>

      <section className="content">
        <header className="topbar">
          <div><span className="eyebrow">CONSTRUCTION REVIEW AI</span><h1>施工图审核工作台</h1><p>上传图纸，创建审核任务，让 AI 帮你发现图纸中的潜在问题。</p></div>
          <button className="primary">＋ 新建审核项目</button>
        </header>

        <section className="stats">
          {stats.map(([label, value]) => <div className="stat" key={label}><span>{label}</span><strong>{value}</strong></div>)}
        </section>

        <section className="grid">
          <div className="card large" id="projects">
            <div className="card-head"><div><h2>最近项目</h2><p>管理正在进行的施工图审核项目</p></div><button className="ghost">查看全部</button></div>
            <div className="project">
              <div className="icon">建</div><div className="project-main"><strong>示例办公楼项目</strong><span>建筑 · 结构 · 给排水 · 电气</span></div><div className="status">待审核</div>
            </div>
            <div className="project">
              <div className="icon">住</div><div className="project-main"><strong>住宅楼施工图</strong><span>建筑 · 结构</span></div><div className="status reviewing">审核中</div>
            </div>
          </div>

          <div className="card upload" id="drawings">
            <div className="upload-mark">↑</div>
            <h2>上传施工图</h2>
            <p>支持 PDF、JPG、PNG</p>
            <button className="primary wide">选择图纸文件</button>
            <small>文件上传后即可创建 AI 审核任务</small>
          </div>
        </section>

        <section className="card" id="reviews">
          <div className="card-head"><div><h2>审核任务</h2><p>AI 审核任务进度与结果</p></div></div>
          <div className="task"><div><strong>住宅楼施工图 · 第一版</strong><span>正在分析 24 张图纸</span></div><div className="progress"><i style={{width:"68%"}}></i></div><b>68%</b></div>
          <div className="task"><div><strong>示例办公楼项目</strong><span>等待开始</span></div><div className="progress"><i style={{width:"0%"}}></i></div><b>0%</b></div>
        </section>

        <section className="card" id="reports">
          <div className="card-head"><div><h2>最近发现的问题</h2><p>问题将按风险等级分类</p></div></div>
          <div className="issues">
            <div><span className="dot danger"></span><div><strong>结构图与建筑图尺寸可能不一致</strong><p>住宅楼施工图 · 2F · A-203 / S-102</p></div><em>高风险</em></div>
            <div><span className="dot warn"></span><div><strong>门窗编号存在缺失</strong><p>示例办公楼 · 3F · A-305</p></div><em>一般</em></div>
          </div>
        </section>

        <footer>AI施工图审核平台 · MVP · 审核结果仅供辅助参考</footer>
      </section>
    </main>
  );
}
