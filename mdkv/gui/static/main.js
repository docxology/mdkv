let editorTrackId = null;
let editorRevision = 0;
let editorDirty = false;
let liveTimer = null;
let operations = Promise.resolve();
let editorLocked = false;
let renderSequence = 0;
let selectedTrackIds = new Set();
let selectionMode = 'all';

async function api(path, opts) {
  const r = await fetch(path, Object.assign({ headers: { 'Content-Type': 'application/json' } }, opts));
  if (!r.ok) throw new Error(await r.text());
  return r.headers.get('content-type')?.includes('application/json') ? r.json() : r.text();
}

function setStatus(message) {
  document.getElementById('status').textContent = message;
}

function enqueue(action) {
  const result = operations.then(action);
  operations = result.catch(() => {});
  return result;
}

function editorSnapshot() {
  return { id: editorTrackId, content: document.getElementById('left').value, revision: editorRevision, dirty: editorDirty };
}

async function persistEditor(snapshot) {
  if (!snapshot.id || !snapshot.dirty) return;
  await api('/api/track', {
    method: 'PUT', body: JSON.stringify({ id: snapshot.id, content: snapshot.content })
  });
  if (editorTrackId === snapshot.id && editorRevision === snapshot.revision) editorDirty = false;
}

async function editorAction(action) {
  if (editorLocked) return;
  editorLocked = true;
  clearTimeout(liveTimer);
  const snapshot = editorSnapshot();
  const controls = ['left', 'editorTrack', 'btnOpen', 'libSelect', 'btnSave'];
  for (const id of controls) document.getElementById(id).disabled = true;
  try {
    await enqueue(async () => {
      // Flush before changing the track/document or saving the container.
      await persistEditor(snapshot);
      await action();
    });
  } catch (error) {
    document.getElementById('editorTrack').value = editorTrackId || '';
    setStatus(error.message);
  } finally {
    editorLocked = false;
    for (const id of controls) document.getElementById(id).disabled = false;
    document.getElementById('left').disabled = !editorTrackId;
  }
}

function liveUpdate() {
  editorRevision += 1;
  editorDirty = true;
  clearTimeout(liveTimer);
  const snapshot = editorSnapshot();
  liveTimer = setTimeout(() => {
    enqueue(async () => {
      await persistEditor(snapshot);
      await renderSelectedTracks();
      setStatus('Live updated');
    }).catch(error => setStatus('Update failed: ' + error.message));
  }, 300);
}

async function selectEditorTrack(id) {
  const track = id ? await api('/api/track?track_id=' + encodeURIComponent(id)) : null;
  editorTrackId = track ? track.id : null;
  editorRevision += 1;
  editorDirty = false;
  document.getElementById('editorTrack').value = editorTrackId || '';
  document.getElementById('left').value = track ? track.content : '';
  document.getElementById('left').disabled = editorLocked || !track;
}

async function refresh(preferredId = editorTrackId) {
  const doc = await api('/api/document');
  const select = document.getElementById('editorTrack');
  select.replaceChildren();
  for (const track of doc.tracks) {
    const option = document.createElement('option');
    option.value = track.id;
    option.textContent = track.id + ' — ' + track.type + (track.language ? ' (' + track.language + ')' : '');
    select.appendChild(option);
  }
  const selected = doc.tracks.find(track => track.id === preferredId) || doc.tracks.find(track => track.type === 'primary') || doc.tracks[0];
  await selectEditorTrack(selected?.id || null);
  await populateTrackFilters();
  await renderSelectedTracks();
}

async function loadPath(path) {
  await editorAction(async () => {
    await api('/api/open', { method: 'POST', body: JSON.stringify({ path }) });
    // Once open succeeds, stale editor contents must never target the new document.
    renderSequence += 1;
    await selectEditorTrack(null);
    document.getElementById('editorTrack').replaceChildren();
    selectionMode = 'all';
    selectedTrackIds.clear();
    await refresh(null);
    setStatus('Loaded ' + path);
  });
}

async function save() {
  await editorAction(async () => {
    const status = await api('/api/status');
    const options = { method: 'POST' };
    if (!status.path) {
      const path = prompt('Save as local .mdkv path:');
      if (!path) {
        setStatus('Save cancelled');
        return;
      }
      options.body = JSON.stringify({ path });
    }
    await api('/api/save', options);
    await renderSelectedTracks();
    setStatus('Saved');
  });
}

async function validate() {
  await editorAction(async () => {
    const result = await api('/api/validate', { method: 'POST' });
    setStatus(result.ok ? 'Validation OK' : 'Validation failed: ' + result.error);
  });
}

async function populateTrackFilters() {
  const container = document.getElementById('trackFilters');
  const tracks = await api('/api/tracks');
  container.replaceChildren();
  const allWrapper = document.createElement('label');
  const allCb = document.createElement('input');
  allCb.type = 'checkbox';
  allCb.id = 'track_all';
  allCb.checked = selectionMode === 'all';
  allWrapper.append(allCb, document.createTextNode('All'));
  container.appendChild(allWrapper);
  allCb.addEventListener('change', () => {
    selectionMode = allCb.checked ? 'all' : 'custom';
    selectedTrackIds = new Set();
    for (const input of container.querySelectorAll('input[data-track-id]')) {
      input.checked = allCb.checked;
      if (input.checked) selectedTrackIds.add(input.dataset.trackId);
    }
    renderSelectedTracks().catch(error => setStatus(error.message));
  });
  for (const track of tracks) {
    const label = document.createElement('label');
    label.dataset.trackId = track.id;
    label.draggable = true;
    const cb = document.createElement('input');
    cb.type = 'checkbox';
    cb.value = track.id;
    cb.dataset.trackId = track.id;
    cb.checked = selectionMode === 'all' || selectedTrackIds.has(track.id);
    label.append(cb, document.createTextNode(' ' + track.id + ' — ' + track.type + (track.language ? ' (' + track.language + ')' : '')));
    container.appendChild(label);
    cb.addEventListener('change', () => {
      if (selectionMode === 'all') selectedTrackIds = new Set(tracks.map(item => item.id));
      selectionMode = 'custom';
      if (cb.checked) selectedTrackIds.add(track.id);
      else selectedTrackIds.delete(track.id);
      allCb.checked = false;
      renderSelectedTracks().catch(error => setStatus(error.message));
    });
  }
}

async function renderSelectedTracks() {
  const sequence = ++renderSequence;
  const html = selectionMode === 'all'
    ? await api('/api/render/all_html')
    : await api('/api/render/tracks_html', { method: 'POST', body: JSON.stringify({ track_ids: [...selectedTrackIds] }) });
  if (sequence === renderSequence) document.getElementById('right').srcdoc = html;
}

const btnTheme = document.getElementById('btnTheme');
function applyTheme(dark) {
  document.body.classList.toggle('dark', dark);
  btnTheme.textContent = dark ? '☀' : '🌙';
  localStorage.setItem('mdkv-theme', dark ? 'dark' : 'light');
}
const savedTheme = localStorage.getItem('mdkv-theme') === 'dark' ||
  (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches && !localStorage.getItem('mdkv-theme'));
applyTheme(savedTheme);
btnTheme.addEventListener('click', () => applyTheme(!document.body.classList.contains('dark')));

const diffView = document.getElementById('diffView');
const panes = document.getElementById('panes');
document.getElementById('btnDiff').addEventListener('click', async () => {
  if (diffView.classList.contains('active')) {
    diffView.classList.remove('active');
    panes.style.display = 'grid';
    return;
  }
  const path = prompt('Path to other .mdkv for diff:');
  if (!path) return;
  await editorAction(async () => {
    const report = await api('/api/diff', { method: 'POST', body: JSON.stringify({ path }) });
    const pre = document.createElement('pre');
    pre.textContent = JSON.stringify(report, null, 2);
    document.getElementById('diffLeftContent').replaceChildren(pre);
    document.getElementById('diffRightContent').textContent = 'Diff report shown left.';
    diffView.classList.add('active');
    panes.style.display = 'none';
    setStatus('Diff loaded');
  });
});

let draggedElement = null;
document.addEventListener('dragstart', event => {
  const label = event.target.closest('.track-filters label[data-track-id]');
  if (!label || editorLocked) {
    event.preventDefault();
    return;
  }
  draggedElement = label;
  label.classList.add('dragging');
  event.dataTransfer.effectAllowed = 'move';
  event.dataTransfer.setData('text/plain', label.dataset.trackId);
});
document.addEventListener('dragend', () => {
  if (draggedElement) draggedElement.classList.remove('dragging');
  draggedElement = null;
  document.querySelectorAll('.drag-over').forEach(label => label.classList.remove('drag-over'));
});
document.addEventListener('dragover', event => {
  const target = event.target.closest('.track-filters label[data-track-id]');
  if (draggedElement && target && target !== draggedElement) {
    event.preventDefault();
    target.classList.add('drag-over');
  }
});
document.addEventListener('dragleave', event => {
  event.target.closest('.track-filters label[data-track-id]')?.classList.remove('drag-over');
});
document.addEventListener('drop', async event => {
  const target = event.target.closest('.track-filters label[data-track-id]');
  if (!draggedElement || !target) return;
  event.preventDefault();
  target.classList.remove('drag-over');
  const trackId = draggedElement.dataset.trackId;
  const afterId = target.dataset.trackId;
  if (trackId === afterId) return;
  await editorAction(async () => {
    await api('/api/move-track', { method: 'POST', body: JSON.stringify({ track_id: trackId, after_id: afterId }) });
    await refresh();
    setStatus('Track reordered');
  });
});

async function populateLibrarySelect() {
  const result = await api('/api/library');
  const select = document.getElementById('libSelect');
  select.replaceChildren();
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Select from library…';
  select.appendChild(placeholder);
  for (const file of result.files) {
    const option = document.createElement('option');
    option.value = file.path;
    option.textContent = file.name;
    select.appendChild(option);
  }
}

window.addEventListener('DOMContentLoaded', async () => {
  document.getElementById('btnOpen').addEventListener('click', () => {
    const path = document.getElementById('openPath').value;
    if (path) loadPath(path);
  });
  document.getElementById('libSelect').addEventListener('change', event => {
    if (event.target.value) loadPath(event.target.value);
  });
  document.getElementById('editorTrack').addEventListener('change', event => {
    const id = event.target.value;
    editorAction(async () => selectEditorTrack(id));
  });
  document.getElementById('btnSave').addEventListener('click', save);
  document.getElementById('btnValidate').addEventListener('click', validate);
  document.getElementById('left').addEventListener('input', liveUpdate);
  await editorAction(async () => {
    const status = await api('/api/status');
    if (status.loaded) await refresh(null);
    else setStatus('Open a document to edit a track.');
  });
  try {
    await populateLibrarySelect();
  } catch (error) {
    setStatus('Library unavailable: ' + error.message);
  }
});
