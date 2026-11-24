const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const listeners={};
const context=vm.createContext({console,URLSearchParams,Intl,Date,FormData,location:{pathname:'/bandeja',search:''},history:{},document:{addEventListener(){},querySelector(){return null},querySelectorAll(){return[]}},window:{addEventListener(name,handler){listeners[name]=handler;}},setInterval(){},setTimeout(){},clearTimeout(){},localStorage:{}});
for(const file of ['app.js','enhancements.js','portal-v4.js','portal-v5.js','portal-v6.js','portal-v7.js'])vm.runInContext(fs.readFileSync('static/'+file,'utf8'),context,{filename:file});
vm.runInContext(`user={id:2,role:'staff',name:'Funcionario'};boot={catalog:[{id:'x',name:'Trámite'}]};workloadV6={waiting:3,online:12,active:null};`,context);
assert.equal(vm.runInContext(`humanTone('Cerrada')`,context),'rejected');
const side=vm.runInContext('sidebar()',context);assert(side.indexOf('Fila presencial')<side.indexOf('Bandeja de solicitudes'));assert(side.includes('data-count="waiting">3'));assert(side.includes('data-count="online">12'));
const table=vm.runInContext(`requestTable([{id:42,folio:'SOL-42',user_id:1,owner_name:'Persona',type_id:'x',created:'2026-11-01',status:'En revisión'}],true)`,context);assert(table.includes('Fecha de ingreso'));assert(table.includes('href="/expedientes/42"'));assert(!table.includes('Abrir expediente'));
const events=vm.runInContext(`timelineHtml({request:{status:'En revisión'},events:[{id:5,status:'Recibida',note:'<script>bad</script>',created:'2026-11-01T10:00:00-03:00',actor_name:'Sistema'}]})`,context);assert(events.includes('data-v6="edit-event"'));assert(events.includes('data-v7="undo-event"'));assert(events.includes('&lt;script&gt;'));assert(!events.includes('Anotaciones rectificadas'));
console.log('Interfaz: scripts inicializados juntos; contadores, color de cierre, folios enlazados e historial seguro comprobados.');

vm.runInContext('render=()=>{globalThis.latestRouterCalled=true;}',context);listeners.popstate();assert.equal(vm.runInContext('latestRouterCalled',context),true);

const card=vm.runInContext(`documentCard({name:'Documento de identidad',status:'En revisión',document:{id:75,name:'identidad.pdf',size:1024,created:'2026-11-24',review_status:'En revisión',ai_review:JSON.stringify({decision:'observar',reason:'Titular diferente',source:'Microsoft Foundry',checks:[]})}},true,42,false)`,context);
assert(card.includes('IA sugiere: rechazarlo'));assert(card.includes('Generar sugerencia con IA'));assert(card.includes('data-document="75"'));assert(!card.includes('Usar documento existente'));
const missing=vm.runInContext(`documentCard({name:'Antecedente de domicilio',status:'Falta documento',document:null},true,42,false)`,context);assert(missing.includes('Notificar al ciudadano'));assert(!missing.includes('Usar documento existente'));
const citizenCard=vm.runInContext(`documentCard({name:'Documento de identidad',status:'Falta documento',document:null},false,42,false)`,context);assert(!citizenCard.includes('Notificar al ciudadano'));assert(!citizenCard.includes('Generar sugerencia con IA'));
assert(!fs.readFileSync('static/app.js','utf8').includes("panel('Asistencia de revisión'"));
