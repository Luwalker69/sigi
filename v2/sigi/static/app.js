'use strict';
const $ = id => document.getElementById(id);
const csrf = document.querySelector('meta[name="sigi-csrf"]').content;
let state = null;
let busy = false;

function notice(text = '') { $('notice').textContent = text; $('notice').hidden = !text; }
function money(value) { return Number(value || 0).toLocaleString('fr-FR', {minimumFractionDigits: 6, maximumFractionDigits: 6}) + ' $'; }
function render() {
  if (!state) return;
  $('connection-label').textContent = state.connected ? (state.demo ? 'Démo sans IA' : 'SIGI connecté') : 'À connecter';
  $('connection-dot').classList.toggle('connected', state.connected);
  $('disconnect').hidden = !state.connected || state.demo;
  $('connect-form').hidden = state.connected;
  $('demo-banner').hidden = !state.demo;
  $('message').disabled = !state.connected || busy;
  $('send').disabled = !state.connected || busy || !$('message').value.trim();
  $('new-chat').disabled = !state.connected || busy;
  $('new-chat-mobile').disabled = !state.connected || busy;
  $('disconnect').disabled = busy;
  $('connect-button').disabled = busy;
  $('model-label').textContent = state.connected ? state.model + ' · ' + (state.agent?.tools?.length || 3) + ' outils' : 'Connecte ta clé pour commencer';
  $('agent-note').textContent = state.agent?.project_root ? 'Code source et documentation accessibles. Les améliorations sont préparées sous forme de propositions.' : 'Sources indisponibles ici. Les outils du dossier de travail restent accessibles.';
  $('cost').textContent = money(state.spent_usd);
  $('mobile-cost').textContent = 'Coût : ' + money(state.spent_usd);
  $('budget-label').textContent = 'Budget SIGI : ' + Number(state.budget_usd).toLocaleString('fr-FR') + ' $';
  $('budget-fill').style.width = Math.min(100, 100 * (Number(state.spent_usd) + Number(state.reserved_usd)) / Math.max(.000001, Number(state.budget_usd))) + '%';
  $('usage-status').textContent = Number(state.reserved_usd) ? 'COÛT À CONFIRMER' : 'USD';
  $('welcome').hidden = state.messages.length > 0;
  $('thinking').hidden = !busy || !state.connected;
  $('messages').replaceChildren();
  for (const message of state.messages) {
    const article = document.createElement('article');
    article.className = 'message ' + (message.role === 'user' ? 'user' : 'assistant');
    if (message.role !== 'user') {
      const label = document.createElement('div'); label.className = 'label';
      const mark = document.createElement('span'); mark.className = 'mini-mark'; mark.textContent = 's.';
      const name = document.createElement('span'); name.textContent = 'SIGI';
      label.append(mark, name);
      if (message.status && message.status !== 'completed') {
        const badge = document.createElement('span'); badge.className = 'error-badge'; badge.textContent = 'Demande interrompue'; label.append(badge);
      }
      article.append(label);
      if (message.actions?.length) {
        const actions = document.createElement('div'); actions.className = 'tool-actions';
        const labels = {agent_info:'Inventaire de l’agent', project_tree:'Exploration du projet', project_read:'Lecture du code', project_search:'Recherche dans le code', project_check_syntax:'Analyse de syntaxe', project_propose_change:'Proposition de modification', list_files:'Liste des fichiers', read_file:'Lecture d’un fichier', write_file:'Création d’un fichier'};
        for (const action of message.actions) {
          const item = document.createElement('span'); item.textContent = (action.status === 'succeeded' ? '✓ ' : '⚠ ') + (labels[action.name] || action.name); actions.append(item);
        }
        article.append(actions);
      }
    }
    const text = document.createElement('div'); text.className = 'text'; text.textContent = message.content;
    article.append(text); $('messages').append(article);
  }
}

async function api(path, payload) {
  const response = await fetch(path, {method: 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', 'X-SIGI-CSRF': csrf}, body: JSON.stringify(payload)});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Action interrompue. Actualise la page avant de réessayer.');
  return data;
}

$('connect-form').addEventListener('submit', async event => {
  event.preventDefault(); if (busy) return;
  const key = $('api-key').value; $('api-key').value = '';
  busy = true; notice(); $('connect-button').textContent = 'Connexion…'; render();
  try { state = await api('/api/connect', {key}); }
  catch (error) { notice(error instanceof TypeError ? 'Serveur injoignable. Vérifie que le terminal SIGI est ouvert.' : error.message); }
  finally { busy = false; $('connect-button').textContent = 'Connecter →'; render(); if (state?.connected) $('message').focus(); }
});

$('chat-form').addEventListener('submit', async event => {
  event.preventDefault(); const message = $('message').value.trim();
  if (busy || !state?.connected || !message) return;
  const previous = state; state = {...state, messages: [...state.messages, {role: 'user', content: message}]};
  $('message').value = ''; $('message').style.height = 'auto'; busy = true; notice(); render();
  window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
  try { state = await api('/api/chat', {message}); }
  catch (error) { state = previous; $('message').value = message; notice(error instanceof TypeError ? 'Réponse interrompue. Actualise la page pour vérifier son état avant de renvoyer.' : error.message); }
  finally { busy = false; render(); $('message').focus(); window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'}); }
});

$('message').addEventListener('input', () => { $('message').style.height = 'auto'; $('message').style.height = Math.min(160, $('message').scrollHeight) + 'px'; renderSend(); });
function renderSend() { $('send').disabled = busy || !state?.connected || !$('message').value.trim(); }
$('message').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); $('chat-form').requestSubmit(); } });
for (const button of document.querySelectorAll('[data-prompt]')) button.addEventListener('click', () => {
  if (!state?.connected) { notice('Connecte d’abord ta clé Gemini pour commencer.'); $('api-key').focus(); return; }
  $('message').value = button.dataset.prompt; renderSend(); $('message').focus();
});
async function openNewChat() {
  if (busy || !state.connected) return;
  if (state.messages.length && !confirm('Ouvrir une nouvelle conversation ? Les journaux de celle-ci restent enregistrés.')) return;
  try { state = await api('/api/new', {}); notice(); render(); $('message').focus(); } catch (error) { notice(error.message); }
}
$('new-chat').addEventListener('click', openNewChat);
$('new-chat-mobile').addEventListener('click', openNewChat);
$('disconnect').addEventListener('click', async () => {
  if (busy) return;
  try { state = await api('/api/disconnect', {}); notice(); render(); } catch (error) { notice(error.message); }
});
async function start() {
  try {
    const response = await fetch('/api/state', {credentials: 'same-origin'});
    const data = await response.json(); if (!response.ok) throw new Error(data.error);
    state = data; render();
  } catch (error) { notice('Impossible de joindre SIGI. Garde le terminal ouvert puis actualise cette page.'); $('connection-label').textContent = 'Hors connexion'; }
}
start();
