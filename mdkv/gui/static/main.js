let primaryId = null;
let selectedTrackIds = new Set();
// 'all' means render all tracks regardless of selectedTrackIds
// 'custom' means render exactly selectedTrackIds (can be empty → render nothing)
let selectionMode = 'all';

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
  try {
    await populateLibrarySelect();
  } catch {}
  // Always load the combined markdown (all tracks) into the editor
  try {
    const md = await api('/api/render/markdown');
    document.getElementById('left').value = md.markdown;
  } catch {}
  try {
    await populateTrackFilters();
    await renderSelectedTracks();
  } catch {}
}

async function loadPath(p) {
  await api('/api/open', { method: 'POST', body: JSON.stringify({ path: p }) });
  await refresh();
  setStatus('Loaded ' + p);
}

async function save() {
  const content = document.getElementById('left').value;
  // Always treat the left pane as the full combined markdown.
  const sections = parseCombinedTracks(content);
  for (const s of sections) {
    await api('/api/track', { method: 'POST', body: JSON.stringify({ id: s.id, content: s.content }) });
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
    await renderSelectedTracks();
    setStatus('Live updated');
  } catch (e) {
    // ignore during typing
  }
}, 300);

async function populateTrackFilters() {
  try {
    const container = document.getElementById('trackFilters');
    const tracks = await api('/api/tracks');
    container.innerHTML = '';
    // Add an "All" checkbox for quick toggle
    const allWrapper = document.createElement('label');
    const allCb = document.createElement('input');
    allCb.type = 'checkbox';
    allCb.id = 'track_all';
    allCb.checked = selectionMode === 'all';
    allWrapper.appendChild(allCb);
    allWrapper.appendChild(document.createTextNode('All'));
    container.appendChild(allWrapper);

    const updateAllChecked = () => {
      allCb.checked = selectionMode === 'all';
    };

    allCb.addEventListener('change', async () => {
      if (allCb.checked) {
        selectionMode = 'all';
        selectedTrackIds.clear();
        // ensure all individual boxes are checked visually
        for (const input of container.querySelectorAll('input[type="checkbox"][data-track-id]')) {
          input.checked = true;
        }
        updateAllChecked();
        await renderSelectedTracks();
      } else {
        // switching off All puts us in custom mode, keep current individual checks
        selectionMode = 'custom';
        // recompute selectedTrackIds from current boxes
        selectedTrackIds = new Set(
          Array.from(container.querySelectorAll('input[type="checkbox"][data-track-id]:checked'))
            .map(cb => cb.dataset.trackId)
        );
        updateAllChecked();
        await renderSelectedTracks();
      }
    });

    for (const t of tracks) {
      const label = document.createElement('label');
      const cb = document.createElement('input');
      cb.type = 'checkbox';
      cb.value = t.id;
      cb.dataset.trackId = t.id;
      cb.checked = selectionMode === 'all' ? true : selectedTrackIds.has(t.id);
      label.appendChild(cb);
      const txt = t.type === 'primary' && t.language ? 'English (primary)' : `${t.type}${t.language ? ' (' + t.language + ')' : ''}`;
      label.appendChild(document.createTextNode(' ' + txt));
      container.appendChild(label);
      cb.addEventListener('change', async () => {
        // any manual change implies custom mode
        selectionMode = 'custom';
        if (cb.checked) {
          selectedTrackIds.add(t.id);
        } else {
          selectedTrackIds.delete(t.id);
        }
        updateAllChecked();
        await renderSelectedTracks();
      });
    }
  } catch (e) {
    // no doc yet
  }
}

async function renderSelectedTracks() {
  if (selectionMode === 'all') {
    const html = await api('/api/render/all_html');
    document.getElementById('right').srcdoc = html;
    return;
  }
  const ids = [...selectedTrackIds];
  const html = await api('/api/render/tracks_html', { method: 'POST', body: JSON.stringify({ track_ids: ids }) });
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
  // Editor always holds combined markdown for all tracks
  const md = await api('/api/render/markdown');
  document.getElementById('left').value = md.markdown;
}

window.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btnOpen').addEventListener('click', async () => {
    const p = document.getElementById('openPath').value;
    if (p) await loadPath(p);
  });
  const libSelect = document.getElementById('libSelect');
  libSelect.addEventListener('change', async () => {
    const p = libSelect.value;
    if (p) await loadPath(p);
  });
  document.getElementById('btnSave').addEventListener('click', save);
  document.getElementById('btnValidate').addEventListener('click', validate);
  document.getElementById('left').addEventListener('input', liveUpdate);
  await populateTrackFilters();
  await renderSelectedTracks();
  // initial populate if a document is preloaded
  refresh();
});

async function populateLibrarySelect() {
  try {
    const r = await api('/api/library');
    const select = document.getElementById('libSelect');
    const existing = select.value;
    select.innerHTML = '';
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = 'Select from library…';
    select.appendChild(placeholder);
    for (const f of r.files) {
      const opt = document.createElement('option');
      opt.value = f.path;
      opt.textContent = f.name;
      select.appendChild(opt);
    }
    if (existing) select.value = existing;
  } catch (e) {
    // ignore if server lacks examples
  }
}


