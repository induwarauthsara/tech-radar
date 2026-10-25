const state = { view: "news", news: [], repos: [], developers: [], query: "", category: "all" };
const $ = (id) => document.getElementById(id);
const esc = (value = "") => String(value).replace(/[&<>"']/g, ch => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
const safeUrl = (value = "") => { try { const u = new URL(value); return ["https:","http:"].includes(u.protocol) ? u.href : "#"; } catch { return "#"; } };
const dateText = (value) => { if (!value) return "RECENT"; const d = new Date(value); return Number.isNaN(d.getTime()) ? "RECENT" : d.toLocaleDateString(undefined,{month:"short",day:"numeric"}).toUpperCase(); };
async function load(path) { const response = await fetch(path + "?v=" + Date.now(), {cache:"no-store"}); if (!response.ok) throw new Error("Could not load " + path); return response.json(); }
function renderNews() {
  const items = state.news.filter(item => (state.category === "all" || item.category === state.category) && (JSON.stringify(item).toLowerCase().includes(state.query.toLowerCase())));
  $("news-view").innerHTML = items.length ? items.map(item => `<article class="news-card"><div class="card-top"><span class="tag">${esc(item.category || "Technology")}</span><span class="date">${esc(dateText(item.published))}</span></div><h3>${esc(item.title)}</h3><p>${esc(item.summary || item.description || "Open the source for more details.")}</p><div class="card-bottom"><span class="source" title="${esc(item.source)}">${esc(item.source || "Source")}</span><a class="open-link" href="${esc(safeUrl(item.url))}" target="_blank" rel="noreferrer">Read source ↗</a></div></article>`).join("") : '<div class="empty">No updates match your search. Try another keyword or topic.</div>';
  $("status").textContent = `${items.length} update${items.length===1?"":"s"} · sourced from public feeds`;
}
function renderRepos() {
  const items = state.repos.filter(item => JSON.stringify(item).toLowerCase().includes(state.query.toLowerCase()));
  $("repos-view").innerHTML = items.length ? items.map((r,i) => `<article class="repo-card"><div class="card-top"><span class="tag">${esc(r.trend_period || "Trending")}</span><span class="repo-owner">#${String(i+1).padStart(2,"0")}</span></div><h3>${esc(r.full_name || r.name || "GitHub repository")}</h3><p class="description">${esc(r.description || "No description provided. Visit the repository to explore its code and documentation.")}</p><div class="repo-stats"><span>★ ${esc(r.stars_label || "Stars on GitHub")}</span><span>${esc(r.language || "Open source")}</span></div><div class="card-bottom"><span class="source">${esc(r.language || "Repository")}</span><a class="open-link" href="${esc(safeUrl(r.url))}" target="_blank" rel="noreferrer">Explore ↗</a></div></article>`).join("") : '<div class="empty">No repositories match your search. New repositories are collected daily.</div>';
  $("status").textContent = `${items.length} distinct repository pick${items.length===1?"":"s"} · repeats are excluded using saved history`;
}
function renderDevelopers() {
  const items = state.developers.filter(d => JSON.stringify(d).toLowerCase().includes(state.query.toLowerCase()));
  $("developers-view").innerHTML = items.length ? items.map(d => `<article class="developer-card"><div class="card-top"><span class="tag">TRENDING</span></div><h3>${esc(d.name || d.username)}</h3><p>${esc(d.username ? "@"+d.username : "GitHub developer")}</p><a href="${esc(safeUrl(d.url))}" target="_blank" rel="noreferrer">View profile ↗</a></article>`).join("") : '<div class="empty">No developer results available. Check back after the next update.</div>';
  $("status").textContent = `${items.length} trending developer profile${items.length===1?"":"s"}`;
}
function updateFilters() {
  const isNews = state.view === "news";
  $("category-filter").classList.toggle("hidden", !isNews);
  $("search").placeholder = isNews ? "Search updates…" : state.view === "repos" ? "Search repositories…" : "Search developers…";
  $("filters").classList.toggle("hidden", state.view === "developers");
  $("news-view").classList.toggle("hidden", !isNews);
  $("repos-view").classList.toggle("hidden", state.view !== "repos");
  $("developers-view").classList.toggle("hidden", state.view !== "developers");
  document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active",tab.dataset.view===state.view));
  $("section-kicker").textContent = isNews ? "THE LATEST" : state.view === "repos" ? "OPEN SOURCE RADAR" : "PEOPLE TO FOLLOW";
  $("section-title").textContent = isNews ? "Technology signals" : state.view === "repos" ? "Repositories worth exploring" : "Developers on the rise";
  $("section-description").textContent = isNews ? "Recent stories from public feeds and engineering blogs." : state.view === "repos" ? "Fresh picks from GitHub Trending, with previously featured repositories excluded." : "Profiles appearing on GitHub's public trending developers page.";
  if (isNews) renderNews(); else if (state.view === "repos") renderRepos(); else renderDevelopers();
}
document.querySelectorAll(".tab").forEach(tab => tab.addEventListener("click", () => { state.view = tab.dataset.view; state.query = ""; $("search").value = ""; updateFilters(); }));
$("search").addEventListener("input", e => { state.query = e.target.value; updateFilters(); });
$("category-filter").addEventListener("change", e => { state.category = e.target.value; renderNews(); });
(async function init() {
  try {
    const [news, repos, history] = await Promise.all([load("data/tech-updates.json"),load("data/github-repositories.json"),load("data/history.json")]);
    state.news = news.items || [];
    state.repos = repos.items || [];
    state.developers = repos.developers || [];
    const categories = [...new Set(state.news.map(x=>x.category).filter(Boolean))].sort();
    $("category-filter").innerHTML = '<option value="all">All topics</option>' + categories.map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join("");
    const updated = news.updated_at || repos.updated_at || history.updated_at;
    $("updated-label").textContent = updated ? "Updated " + new Date(updated).toLocaleString(undefined,{month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}) : "Waiting for first update";
    $("news-count").textContent = state.news.length;
    $("repo-count").textContent = state.repos.length;
    updateFilters();
  } catch (error) {
    $("status").textContent = "Radar data could not be loaded. The first scheduled collection may not have run yet.";
    $("news-view").innerHTML = '<div class="empty">Please check back after GitHub Actions completes its first run. You can also open the repository to inspect the workflow.</div>';
    console.error(error);
  }
})();