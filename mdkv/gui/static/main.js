let primaryId = null;
let currentTrackId = null;

async function api(path, opts) {
  const r = await fetch(path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts));
  if (!r.ok) throw new Error(await r.text());
  return r.headers.get('content-type')?.includes('application/json') ? r.json() : r.text();
}

async function refresh() {
  try {
    const doc = await api('/api/document');
    const p = doc.tracks.find(t => t.type === 'primary');
    primaryId = p ? p.id : (doc.tracks[0]?.id || null);
  } catch (e) {
    // no document loaded yet
  }
  // Always load the combined markdown (all tracks) into the editor
  try {
    const md = await api('/api/render/markdown');
    document.getElementById('left').value = md.markdown;
  } catch {}
  try {
    await populateTrackSelect();
    await renderSelectedTrack();
  } catch {}
}

async function loadPath(p) {
  await api('/api/open', { method: 'POST', body: JSON.stringify({ path: p }) });
  await refresh();
  setStatus('Loaded ' + p);
}

async function save() {
  const content = document.getElementById('left').value;
  // naive: push entire combined markdown by splitting to primary track only for demo
  // In a full implementation, we'd parse markers per track. Here we set primary.
  if (primaryId) {
    // language not critical for update; server keeps previous if omitted
    await api('/api/track', { method: 'POST', body: JSON.stringify({ id: primaryId, type: 'primary', content }) });
  }
  await api('/api/save', { method: 'POST' });
  setStatus('Saved');
}

async function validate() {
  const r = await api('/api/validate', { method: 'POST' });
  setStatus(r.ok ? 'Validation OK' : 'Validation failed: ' + r.error);
}

function setStatus(msg) {
  document.getElementById('status').textContent = msg;
}

function debounce(fn, ms) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), ms);
  };
}

const liveUpdate = debounce(async () => {
  try {
    const combined = document.getElementById('left').value;
    const sections = parseCombinedTracks(combined);
    // push all sections so edits to any track are persisted
    for (const s of sections) {
      await api('/api/track', { method: 'POST', body: JSON.stringify({ id: s.id, content: s.content }) });
    }
    await renderSelectedTrack();
    setStatus('Live updated');
  } catch (e) {
    // ignore during typing
  }
}, 300);

async function populateTrackSelect() {
  try {
    const select = document.getElementById('trackSelect');
    const tracks = await api('/api/tracks');
    // Build options
    select.innerHTML = '';
    // All option first
    const allOpt = document.createElement('option');
    allOpt.value = '__ALL__';
    allOpt.textContent = 'All tracks';
    select.appendChild(allOpt);
    let firstId = null;
    for (const t of tracks) {
      const opt = document.createElement('option');
      opt.value = t.id;
      const label = t.type === 'primary' && t.language ? 'English (primary)' : `${t.type}${t.language ? ' (' + t.language + ')' : ''}`;
      opt.textContent = label;
      select.appendChild(opt);
      if (!firstId) firstId = t.id;
    }
    if (!currentTrackId) currentTrackId = firstId;
    select.value = currentTrackId || '__ALL__';
    // Ensure change handler is bound once
    if (!select.dataset.bound) {
      select.addEventListener('change', renderSelectedTrack);
      select.dataset.bound = '1';
    }
  } catch (e) {
    // no doc yet
  }
}

async function renderSelectedTrack() {
  const select = document.getElementById('trackSelect');
  currentTrackId = select.value || currentTrackId;
  if (!currentTrackId) return;
  const html = currentTrackId === '__ALL__' ? await api('/api/render/all_html') : await api(`/api/render/track_html?track_id=${encodeURIComponent(currentTrackId)}`);
  document.getElementById('right').srcdoc = html;
}

function parseCombinedTracks(text) {
  const re = /<!--\s*track:([^\s]+)\s+type:[^>]*?-->/g;
  const matches = [];
  let m;
  while ((m = re.exec(text)) !== null) {
    matches.push({ index: m.index, id: m[1], headerLen: m[0].length });
  }
  const sections = [];
  for (let i = 0; i < matches.length; i++) {
    const start = matches[i].index + matches[i].headerLen;
    const end = i + 1 < matches.length ? matches[i + 1].index : text.length;
    let content = text.slice(start, end);
    content = content.replace(/^\s+/, '');
    sections.push({ id: matches[i].id, content });
  }
  return sections;
}

async function setEditorFromSelection() {
  const select = document.getElementById('trackSelect');
  const tid = select.value || currentTrackId;
  if (!tid) return;
  if (tid === '__ALL__') {
    const md = await api('/api/render/markdown');
    document.getElementById('left').value = md.markdown;
  } else {
    const t = await api(`/api/track/${encodeURIComponent(tid)}`);
    document.getElementById('left').value = t.content || '';
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btnOpen').addEventListener('click', async () => {
    const p = document.getElementById('openPath').value;
    if (p) await loadPath(p);
  });
  document.getElementById('btnSave').addEventListener('click', save);
  document.getElementById('btnValidate').addEventListener('click', validate);
  document.getElementById('left').addEventListener('input', liveUpdate);
  await populateTrackSelect();
  await renderSelectedTrack();
  // initial populate if a document is preloaded
  refresh();
});


