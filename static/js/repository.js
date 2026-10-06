/**
 * DevFlow AI - Repository Management & Upload Logic
 */

function handleFileSelected(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    document.getElementById('zipFileLabel').innerText = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    const defaultName = file.name.replace(/\.zip$/i, '').replace(/[^a-zA-Z0-9-_]/g, '-');
    const nameInput = document.getElementById('uploadRepoName');
    if (!nameInput.value) {
      nameInput.value = defaultName;
    }
  }
}

async function submitZipUpload() {
  const fileInput = document.getElementById('zipFileInput');
  if (!fileInput.files || fileInput.files.length === 0) {
    alert("Please select a .zip repository archive first.");
    return;
  }

  const file = fileInput.files[0];
  const name = document.getElementById('uploadRepoName').value.trim() || file.name.replace(/\.zip$/i, '');

  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);

  const btn = document.getElementById('btnUploadZip');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Extracting & Indexing...';

  try {
    const res = await fetch('/api/repositories/upload', {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      alert(`Repository '${data.repository.name}' uploaded and vector indexed!`);
      // Close modal if open
      const modalEl = document.getElementById('uploadRepoModal');
      if (modalEl) {
        const modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
      }
      window.location.reload();
    } else {
      alert("Upload failed: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    alert("Upload error: " + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-cloud-arrow-up me-1"></i> Upload & Auto-Index RAG';
  }
}

async function submitConnectRepoForm() {
  const name = document.getElementById('connectRepoName').value.trim();
  const pathOrUrl = document.getElementById('connectRepoPath').value.trim();

  if (!name) {
    alert("Please provide a repository name.");
    return;
  }

  try {
    const res = await fetch('/api/repositories/connect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: name,
        local_path: pathOrUrl.startsWith('http') ? '' : pathOrUrl,
        url: pathOrUrl.startsWith('http') ? pathOrUrl : ''
      })
    });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      alert(`Repository '${name}' connected and indexed!`);
      window.location.reload();
    } else {
      alert("Error: " + (data.error || "Failed to connect repository"));
    }
  } catch (err) {
    alert("Error: " + err);
  }
}

async function reindexRepo(repoId) {
  const btn = event.target;
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>';
  try {
    const res = await fetch(`/api/repositories/${repoId}/index`, { method: 'POST' });
    const data = await res.json();
    alert(`Repository indexed: ${data.total_files || 0} files, ${data.total_chunks || 0} vector chunks.`);
    window.location.reload();
  } catch (err) {
    alert("Re-index error: " + err);
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<i class="fa-solid fa-rotate me-1"></i> Re-index';
  }
}

async function deleteRepo(repoId, repoName) {
  if (!confirm(`Are you sure you want to delete repository "${repoName}"? This will remove all associated workflows and vector indexes.`)) {
    return;
  }
  try {
    const res = await fetch(`/api/repositories/${repoId}`, { method: 'DELETE' });
    const data = await res.json();
    if (res.ok && data.status === 'success') {
      window.location.reload();
    } else {
      alert("Delete failed: " + (data.error || "Unknown error"));
    }
  } catch (err) {
    alert("Delete error: " + err);
  }
}


