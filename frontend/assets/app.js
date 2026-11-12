// Utilidades compartidas del frontend: llamadas a la API (Python/FastAPI), sesión, menú lateral y avisos.
const BACK = '/api';  // la API de Python (FastAPI) responde en /api
const $ = s => document.querySelector(s);
const money = n => '$' + Number(n || 0).toFixed(2);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

function aviso(texto) {
  let t = $('#toast');
  if (!t) { t = document.createElement('div'); t.id = 'toast'; t.className = 'toast'; t.setAttribute('role', 'status'); document.body.appendChild(t); }
  t.textContent = texto; t.style.display = 'block';
  clearTimeout(aviso.t); aviso.t = setTimeout(() => t.style.display = 'none', 3000);
}

async function api(ruta, { metodo = 'GET', consulta, cuerpo } = {}) {
  const q = consulta ? '?' + new URLSearchParams(consulta) : '';
  const r = await fetch(BACK + ruta + q, {
    method: metodo, credentials: 'same-origin',
    headers: cuerpo ? { 'Content-Type': 'application/json' } : {},
    body: cuerpo ? JSON.stringify(cuerpo) : undefined,
  });
  const d = await r.json().catch(() => ({}));
  if (r.status === 401 && !location.pathname.endsWith('login.html')) { location.href = '../usuarios/login.html'; throw new Error('Tu sesión expiró'); }
  if (!r.ok) throw new Error(d.error || 'Error del servidor');
  return d;
}
// Envuelve un manejador para que cualquier error se muestre como aviso
const seguro = f => async (...a) => { try { await f(...a); } catch (e) { aviso(e.message); } };

const MENU = [
  ['ventas/registrar_venta.html', 'Registrar venta', null],
  ['ventas/ticket_venta.html', 'Tickets y cotizaciones', null],
  ['inventario/productos.html', 'Productos', 'Inventario'],
  ['inventario/registrar_producto.html', 'Registrar producto', 'Inventario'],
  ['reportes/reporte_ventas.html', 'Reporte de ventas', 'Reportes'],
  ['reportes/reporte_inventario.html', 'Reporte de inventario', 'Reportes'],
  ['usuarios/registro_usuarios.html', 'Usuarios y respaldos', 'owner'],
];
const tiene = (u, p) => !p || u.rol === 'Propietario' || (p !== 'owner' && u.permisos.includes(p));

// Verifica la sesión y el permiso de la página; dibuja el menú. Devuelve el usuario o null.
async function iniciar(requisito) {
  let u;
  try { u = await api('/usuarios/me'); } catch (e) { return null; }
  if (!tiene(u, requisito)) { location.href = '../ventas/registrar_venta.html'; return null; }
  $('#nav').innerHTML = '<div class="logo">Triates <mark>POS</mark></div>'
    + MENU.filter(m => tiene(u, m[2])).map(m => `<a href="../${m[0]}" class="${location.pathname.endsWith(m[0].split('/')[1]) ? 'on' : ''}">${m[1]}</a>`).join('')
    + `<div class="who">${esc(u.nombre)}<br><button onclick="cerrarSesion()">Cerrar sesión</button></div>`;
  return u;
}
async function cerrarSesion() {
  try { await api('/usuarios/logout', { metodo: 'POST' }); } catch (e) {}
  location.href = '../usuarios/login.html';
}
