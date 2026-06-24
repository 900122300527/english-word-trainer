let currentWord = null;
let groupsCache = [];

function setStatus(text){ document.getElementById('status').textContent = text || ''; }
function openAdd(){ fillAddGroupSelect(); document.getElementById('addModal').classList.remove('hidden'); }
function closeAdd(){ document.getElementById('addModal').classList.add('hidden'); }
function openGroup(){ document.getElementById('groupModal').classList.remove('hidden'); }
function closeGroup(){ document.getElementById('groupModal').classList.add('hidden'); }
function selectedGroup(){ return document.getElementById('groupFilter').value || 'all'; }

async function changeGroup(){
  await loadRandom();
  await loadWords();
}

async function loadGroups(){
  const res = await fetch('/api/groups');
  groupsCache = await res.json();

  const current = selectedGroup();
  const groupFilter = document.getElementById('groupFilter');
  groupFilter.innerHTML = '<option value="all">Все слова</option>';
  groupsCache.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g.id;
    opt.textContent = `${g.name} (${g.word_count})`;
    groupFilter.appendChild(opt);
  });
  if([...groupFilter.options].some(o => o.value === current)) groupFilter.value = current;
  fillAddGroupSelect();
}

function fillAddGroupSelect(){
  const sel = document.getElementById('newGroupSelect');
  if(!sel) return;
  const current = selectedGroup();
  sel.innerHTML = '';
  groupsCache.forEach(g => {
    const opt = document.createElement('option');
    opt.value = g.id;
    opt.textContent = g.name;
    sel.appendChild(opt);
  });
  if(current !== 'all' && [...sel.options].some(o => o.value === current)) sel.value = current;
}

async function addGroup(){
  const name = document.getElementById('groupName').value.trim();
  if(!name){ alert('Введите название группы'); return; }
  const res = await fetch('/api/groups/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name})
  });
  const data = await res.json();
  if(!res.ok){ alert(data.error || 'Ошибка'); return; }
  document.getElementById('groupName').value = '';
  closeGroup();
  await loadGroups();
  document.getElementById('groupFilter').value = String(data.id);
  await changeGroup();
}

async function loadRandom(){
  setStatus('');
  document.getElementById('translation').classList.add('hidden');
  const res = await fetch('/api/random?group_id=' + encodeURIComponent(selectedGroup()));
  const data = await res.json();
  if(!res.ok){
    currentWord = null;
    document.getElementById('wordId').textContent = '';
    document.getElementById('word').textContent = 'Нет слов';
    document.getElementById('wordGroup').textContent = '';
    document.getElementById('transcription').textContent = '';
    document.getElementById('translation').textContent = data.error || 'В группе нет слов';
    document.getElementById('translation').classList.remove('hidden');
    return;
  }
  currentWord = data;
  document.getElementById('wordId').textContent = currentWord.id;
  document.getElementById('word').textContent = currentWord.word;
  document.getElementById('wordGroup').textContent = currentWord.group_name || '';
  document.getElementById('transcription').textContent = currentWord.transcription || '';
  document.getElementById('translation').textContent = currentWord.translation || 'перевод не указан';
}

function toggleTranslation(){
  document.getElementById('translation').classList.toggle('hidden');
}

async function playWord(){
  if(!currentWord) return;
  setStatus('Генерирую озвучку...');
  const voice = document.getElementById('voice').value;
  const res = await fetch('/speak', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ text: currentWord.word, voice })
  });
  const data = await res.json();
  if(!res.ok){
    alert(data.error || 'Озвучка не запустилась');
    setStatus('Ошибка озвучки');
    return;
  }
  const player = document.getElementById('player');
  player.src = data.audio_url + '?v=' + Date.now();
  try{
    await player.play();
    setStatus('');
  }catch(e){
    player.hidden = false;
    setStatus('Нажми Play на аудиоплеере ниже');
  }
}

async function markWord(status){
  if(!currentWord) return;
  await fetch('/api/mark', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ id: currentWord.id, status })
  });
  if(status === 'known') setStatus('Отмечено: знаю');
  else setStatus('Отмечено: не знаю');
  await refreshCounters();
}

async function refreshCounters(){
  const res = await fetch('/api/words');
  const words = await res.json();
  document.getElementById('total').textContent = words.length;
  document.getElementById('known').textContent = words.filter(w => w.known === 1).length;
}

async function loadWords(){
  const res = await fetch('/api/words?group_id=' + encodeURIComponent(selectedGroup()));
  const words = await res.json();
  const box = document.getElementById('wordsList');
  box.innerHTML = '';
  words.forEach(w => {
    const div = document.createElement('div');
    div.className = 'word-item';
    div.innerHTML = `<b>${escapeHtml(w.word)}</b><span>${escapeHtml(w.translation || '')}</span><span>${escapeHtml(w.transcription || '')}</span><span class="mini-group">${escapeHtml(w.group_name || '')}</span><button onclick="deleteWord(${w.id})">Удалить</button>`;
    box.appendChild(div);
  });
  await refreshCounters();
}

async function addWord(){
  const word = document.getElementById('newWord').value.trim();
  const transcription = document.getElementById('newTranscription').value.trim();
  const translation = document.getElementById('newTranslation').value.trim();
  const group_id = document.getElementById('newGroupSelect').value;
  const new_group = document.getElementById('newGroupName').value.trim();
  if(!word){ alert('Введите слово'); return; }
  const res = await fetch('/api/add', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({word, transcription, translation, group_id, new_group})
  });
  const data = await res.json();
  if(!res.ok){ alert(data.error || 'Ошибка'); return; }
  document.getElementById('newWord').value = '';
  document.getElementById('newTranscription').value = '';
  document.getElementById('newTranslation').value = '';
  document.getElementById('newGroupName').value = '';
  closeAdd();
  await loadGroups();
  await loadWords();
  await loadRandom();
}

async function deleteWord(id){
  await fetch('/api/delete/' + id, {method:'POST'});
  await loadGroups();
  await loadWords();
  await loadRandom();
}

function escapeHtml(s){
  return String(s).replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}

async function start(){
  await loadGroups();
  await loadRandom();
  await loadWords();
}

start();
