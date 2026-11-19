const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const bootLines = [
  'initializing school systems...',
  'loading campus environment...',
  'connecting learning modules...',
  'synchronizing demo records...',
  'preparing your workspace...',
  'rendering the third dimension...',
  'all systems ready. welcome back.'
];

function runBootSequence() {
  const screen = $('#bootScreen');
  const app = $('#appShell');
  const line = $('#bootLine');
  const progress = $('#bootProgress');
  const percent = $('#bootPercent');
  let value = 0;
  let lineIndex = 0;
  const tick = () => {
    value = Math.min(100, value + (value < 45 ? 4 : value < 82 ? 3 : 2));
    const nextIndex = Math.min(bootLines.length - 1, Math.floor(value / 15));
    if (nextIndex !== lineIndex) {
      lineIndex = nextIndex;
      line.textContent = bootLines[lineIndex];
    }
    progress.style.width = `${value}%`;
    percent.textContent = `${String(value).padStart(2, '0')}%`;
    if (value >= 100) {
      window.setTimeout(() => {
        screen.classList.add('done');
        app.classList.add('ready');
        app.setAttribute('aria-hidden', 'false');
        setTimeout(() => screen.remove(), 1000);
      }, 240);
      return;
    }
    window.setTimeout(tick, prefersReducedMotion ? 20 : 92);
  };
  tick();
}

const sampleStudents = [
  {name:'Ayesha Malik', id:'ST-2086', grade:'Grade 7', section:'Blue', status:'Active'},
  {name:'Hassan Ahmed', id:'ST-2085', grade:'Grade 10', section:'Gold', status:'Active'},
  {name:'Mariam Noor', id:'ST-2084', grade:'Grade 8', section:'Silver', status:'Active'},
  {name:'Zain Raza', id:'ST-2083', grade:'Grade 9', section:'Emerald', status:'Pending'},
  {name:'Sara Iqbal', id:'ST-2082', grade:'Grade 6', section:'Blue', status:'Active'},
  {name:'Hamza Farooq', id:'ST-2081', grade:'Grade 11', section:'Gold', status:'Active'},
  {name:'Noor Fatima', id:'ST-2080', grade:'Grade 12', section:'Silver', status:'Active'}
];
let students = loadStudents();
function loadStudents() {
  try { const saved = JSON.parse(localStorage.getItem('techvalorpk-demo-students')); return Array.isArray(saved) ? saved : sampleStudents; }
  catch { return sampleStudents; }
}
function persistStudents() {
  try { localStorage.setItem('techvalorpk-demo-students', JSON.stringify(students)); }
  catch { toast('Browser storage is unavailable. The record will not persist after refresh.'); }
}

const moduleConfigs = {
  students: {title:'Students', subtitle:'Your student directory, organized and easy to manage.', stats:[['Enrolled students','1,284'],['New this month','42'],['Pending profiles','18']], columns:['STUDENT','STUDENT ID','GRADE','SECTION','STATUS'], getRows:()=>students.map(s=>[s.name,s.id,s.grade,s.section,s.status])},
  staff: {title:'Faculty & staff', subtitle:'Keep your teaching and administrative teams connected.', stats:[['Total team members','86'],['Teaching faculty','78'],['On leave today','4']], columns:['TEAM MEMBER','EMPLOYEE ID','DEPARTMENT','ROLE','STATUS'], rows:[['Sarah Khan','EMP-014','Sciences','Teacher','Active'],['Robert James','EMP-022','Mathematics','Head of department','Active'],['Mina Farooq','EMP-031','Administration','Coordinator','Active'],['Usman Tariq','EMP-044','Languages','Teacher','On leave'],['Hira Abbas','EMP-051','Student affairs','Counsellor','Active']]},
  classes: {title:'Classes & subjects', subtitle:'A clear view of academic groups, rooms and assigned teachers.', stats:[['Active classes','38'],['Subjects','24'],['Room utilization','89%']], columns:['CLASS','SECTION','HOMEROOM TEACHER','STUDENTS','STATUS'], rows:[['Grade 7','Blue','Sarah Khan','32','Active'],['Grade 8','Silver','Robert James','30','Active'],['Grade 9','Emerald','Mina Farooq','34','Active'],['Grade 10','Gold','Usman Tariq','31','Active'],['Grade 11','Blue','Hira Abbas','28','Active']]},
  attendance: {title:'Attendance', subtitle:'Monitor daily presence and follow up on absences.', stats:[['Present today','1,243'],['Absent today','41'],['Attendance rate','96.8%']], columns:['CLASS','TEACHER','ENROLLED','PRESENT','ATTENDANCE'], rows:[['Grade 7 - Blue','Sarah Khan','32','31','96.9%'],['Grade 8 - Silver','Robert James','30','29','96.7%'],['Grade 9 - Emerald','Mina Farooq','34','32','94.1%'],['Grade 10 - Gold','Usman Tariq','31','31','100%'],['Grade 11 - Blue','Hira Abbas','28','27','96.4%']]},
  exams: {title:'Examinations', subtitle:'Plan assessments, manage schedules and review published results.', stats:[['Scheduled exams','12'],['Results published','8'],['Awaiting review','4']], columns:['ASSESSMENT','GRADE','DATE','CANDIDATES','STATUS'], rows:[['Mid-term assessment','Grade 10','22 Nov 2026','128','Scheduled'],['Science exhibition','Grades 8–10','19 Nov 2026','96','In progress'],['English proficiency','Grade 9','25 Nov 2026','112','Scheduled'],['Mathematics quiz','Grade 7','27 Nov 2026','104','Published']]},
  fees: {title:'Fees & finance', subtitle:'Track collections, outstanding balances and payment activity.', stats:[['Collected this month','PKR 4.8M'],['Collection target','82%'],['Outstanding invoices','PKR 1.1M']], columns:['INVOICE','STUDENT','DUE DATE','AMOUNT','STATUS'], rows:[['INV-2026-089','Ayesha Malik','20 Nov 2026','PKR 18,500','Paid'],['INV-2026-090','Hassan Ahmed','20 Nov 2026','PKR 18,500','Pending'],['INV-2026-091','Mariam Noor','21 Nov 2026','PKR 17,000','Paid'],['INV-2026-092','Zain Raza','22 Nov 2026','PKR 18,500','Pending']]},
  library: {title:'Library', subtitle:'A living catalogue of books, borrowers and returns.', stats:[['Catalogue titles','3,420'],['Currently borrowed','186'],['Overdue returns','12']], columns:['BOOK TITLE','AUTHOR','CATEGORY','COPIES','AVAILABILITY'], rows:[['The Design of Everyday Things','Don Norman','Design','6','Available'],['A Brief History of Time','Stephen Hawking','Science','4','Available'],['The Hobbit','J. R. R. Tolkien','Fiction','2','Borrowed'],['Clean Code','Robert C. Martin','Technology','3','Available']]},
  transport: {title:'Transport', subtitle:'Keep routes, vehicles and student journeys coordinated.', stats:[['Active routes','14'],['Registered vehicles','18'],['Students on transport','426']], columns:['ROUTE','VEHICLE','DRIVER','STUDENTS','STATUS'], rows:[['North route','BUS-04','Imran Shah','36','On route'],['West route','BUS-09','Bilal Ahmed','31','Active'],['Central route','BUS-12','Kamran Ali','28','Active'],['East route','BUS-15','Fahad Malik','34','On route']]},
  analytics: {title:'Analytics & reports', subtitle:'Turn school activity into clear, useful decisions.', stats:[['Attendance average','96.8%'],['Academic pass rate','92.4%'],['Fee collection','82%']], columns:['REPORT','PERIOD','OWNER','LAST UPDATED','STATUS'], rows:[['Campus performance','November 2026','Alex Morgan','Today, 09:32','Ready'],['Attendance summary','Week 47','Sarah Khan','Today, 09:10','Ready'],['Fee collection report','November 2026','Finance office','Yesterday','Ready'],['Assessment outcomes','Term 2','Robert James','18 Nov 2026','Ready']]},
  calendar: {title:'School calendar', subtitle:'One shared schedule for learning, events and school operations.', stats:[['Events this month','18'],['Upcoming assessments','4'],['Next school break','18 days']], columns:['EVENT','DATE','LOCATION','AUDIENCE','STATUS'], rows:[['Science exhibition','19 Nov 2026','Auditorium','Grades 8–10','Today'],['Parent-teacher meeting','20 Nov 2026','Conference hall','All grades','Upcoming'],['Mid-term assessments','22 Nov 2026','Exam blocks','Grades 6–12','Upcoming'],['Sports day','28 Nov 2026','Sports ground','All school','Upcoming']]}
};

function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}
function statusHTML(value) {
  const pending = /pending|leave|scheduled|review/i.test(value);
  return `<span class="table-status ${pending ? 'pending' : ''}">${escapeHTML(value)}</span>`;
}
function renderModule(view) {
  const config = moduleConfigs[view];
  if (!config) return;
  $('#moduleTitle').textContent = config.title;
  $('#moduleSubtitle').textContent = config.subtitle;
  $('#breadcrumbCurrent').textContent = config.title;
  $('#moduleSummary').innerHTML = config.stats.map(([label,value]) => `<article class="summary-card"><span>${escapeHTML(label)}</span><b>${escapeHTML(value)}</b></article>`).join('');
  $('#moduleHead').innerHTML = `<tr>${config.columns.map(col=>`<th>${escapeHTML(col)}</th>`).join('')}</tr>`;
  const rows = config.getRows ? config.getRows() : config.rows;
  renderRows(rows, config.columns.length);
  $('#moduleSearch').value = '';
  $('#moduleAdd').style.display = view === 'students' ? 'inline-flex' : 'none';
  $('#moduleAdd').textContent = view === 'students' ? '＋ Add student' : '＋ Add record';
}
function renderRows(rows, colCount) {
  const body = $('#moduleBody');
  body.innerHTML = rows.map(row => `<tr>${row.map((cell,index) => `<td>${index === colCount - 1 ? statusHTML(cell) : escapeHTML(cell)}</td>`).join('')}</tr>`).join('') || `<tr><td colspan="${colCount}">No records match your search.</td></tr>`;
  $('#tableCount').textContent = `Showing ${rows.length} demo record${rows.length === 1 ? '' : 's'}`;
}
function setView(view) {
  const isDashboard = view === 'dashboard';
  $$('.nav-item').forEach(button => button.classList.toggle('active', button.dataset.view === view));
  $('#view-dashboard').classList.toggle('active-view', isDashboard);
  $('#view-module').classList.toggle('active-view', !isDashboard);
  $('#breadcrumbCurrent').textContent = isDashboard ? 'Overview' : (moduleConfigs[view]?.title || 'Overview');
  if (!isDashboard) renderModule(view);
  $('#sidebar').classList.remove('open');
  window.scrollTo({top:0, behavior:prefersReducedMotion?'instant':'smooth'});
}

function toast(message) {
  const node = document.createElement('div');
  node.className = 'toast';
  node.textContent = message;
  $('#toastStack').append(node);
  setTimeout(() => node.remove(), 3200);
}
function openStudentModal() {
  $('#modalBackdrop').hidden = false;
  $('#studentForm').reset();
  $('#modalTitle').textContent = 'Add a student';
  $('#modalDescription').textContent = 'Create a new student record in this local demo.';
  setTimeout(() => $('input[name="name"]', $('#studentForm')).focus(), 60);
}
function closeStudentModal() { $('#modalBackdrop').hidden = true; }
function downloadCSV() {
  const rows = [['Name','Student ID','Grade','Section','Status'], ...students.map(s=>[s.name,s.id,s.grade,s.section,s.status])];
  const csv = rows.map(row=>row.map(value=>`"${String(value).replace(/"/g,'""')}"`).join(',')).join('\r\n');
  const blob = new Blob([csv], {type:'text/csv;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download='techvalorpk-student-demo.csv'; a.click(); URL.revokeObjectURL(url);
  toast('Demo student list exported as CSV.');
}

function setupNavigation() {
  $$('.nav-item').forEach(button => button.addEventListener('click', () => setView(button.dataset.view)));
  $$('[data-go]').forEach(button => button.addEventListener('click', () => setView(button.dataset.go)));
  $$('[data-action="student"]').forEach(button => button.addEventListener('click', openStudentModal));
  $('#addStudentTop').addEventListener('click', openStudentModal);
  $('#moduleAdd').addEventListener('click', openStudentModal);
  $('#exportOverview').addEventListener('click', downloadCSV);
  $('#moduleExport').addEventListener('click', downloadCSV);
  $('#moduleSearch').addEventListener('input', event => {
    const current = $('.nav-item.active')?.dataset.view || 'students';
    const config = moduleConfigs[current];
    if (!config) return;
    const q = event.target.value.trim().toLowerCase();
    const source = config.getRows ? config.getRows() : config.rows;
    renderRows(source.filter(row=>row.some(cell=>String(cell).toLowerCase().includes(q))), config.columns.length);
  });
  $('#studentForm').addEventListener('submit', event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const id = String(form.get('id')).trim();
    if (students.some(student=>student.id.toLowerCase() === id.toLowerCase())) { toast('That student ID already exists in the demo.'); return; }
    students.unshift({name:String(form.get('name')).trim(),id,grade:String(form.get('grade')),section:String(form.get('section')),status:String(form.get('status'))});
    persistStudents();
    closeStudentModal();
    setView('students');
    toast('Student added to this browser’s demo workspace.');
  });
  $('#modalClose').addEventListener('click', closeStudentModal);
  $('#modalCancel').addEventListener('click', closeStudentModal);
  $('#modalBackdrop').addEventListener('click', event => { if (event.target === $('#modalBackdrop')) closeStudentModal(); });
  $('#sidebarClose').addEventListener('click', () => $('#sidebar').classList.remove('open'));
  $('#mobileMenu').addEventListener('click', () => $('#sidebar').classList.toggle('open'));
  $('#helpButton').addEventListener('click', () => toast('Help centre preview: support links will be connected in the production edition.'));
  $('#profileMenu').addEventListener('click', () => toast('Signed in as Alex Morgan · Demo administrator.'));
  $('#notificationButton').addEventListener('click', () => toast('You’re all caught up. No new notifications.'));
  $('#attendancePeriod').addEventListener('click', () => toast('Weekly attendance view selected.'));
}

function setupTheme() {
  const stored = localStorage.getItem('techvalorpk-theme');
  if (stored === 'light' || stored === 'dark') document.documentElement.dataset.theme = stored;
  $('#themeToggle').addEventListener('click', () => {
    const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('techvalorpk-theme', next);
    $('#themeToggle').textContent = next === 'dark' ? '☼' : '☾';
  });
  $('#themeToggle').textContent = document.documentElement.dataset.theme === 'dark' ? '☼' : '☾';
}

const commandItems = [
  ['⌂','Open dashboard','dashboard'],['♙','Manage students','students'],['♧','Faculty & staff','staff'],['◷','Take attendance','attendance'],['✧','Examinations','exams'],['＄','Fees & finance','fees'],['▥','Analytics & reports','analytics'],['▦','School calendar','calendar'],['＋','Add a student','add-student']
];
function setupCommandPalette() {
  const backdrop = $('#commandBackdrop');
  const input = $('#commandInput');
  const results = $('#commandResults');
  const open = () => { backdrop.hidden = false; input.value=''; draw(''); setTimeout(()=>input.focus(),30); };
  const close = () => { backdrop.hidden = true; };
  function draw(query) {
    const filtered = commandItems.filter(item=>item[1].toLowerCase().includes(query.toLowerCase()));
    results.innerHTML = filtered.map(item=>`<button class="command-result" data-command="${item[2]}"><span>${item[0]}</span><span>${item[1]}</span><kbd>↵</kbd></button>`).join('') || '<div class="command-result">No matching actions</div>';
  }
  input.addEventListener('input',()=>draw(input.value));
  results.addEventListener('click',event=>{
    const target=event.target.closest('[data-command]'); if(!target)return;
    const command=target.dataset.command; close();
    if(command==='add-student') openStudentModal(); else setView(command);
  });
  $('#searchTrigger').addEventListener('click',open);
  backdrop.addEventListener('click',event=>{if(event.target===backdrop)close();});
  document.addEventListener('keydown',event=>{
    if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();open();}
    if(event.key==='Escape'){close();closeStudentModal();}
  });
}

function setupTiltCards() {
  if (prefersReducedMotion || window.matchMedia('(pointer: coarse)').matches) return;
  $$('.tilt-card').forEach(card=>{
    card.addEventListener('pointermove',event=>{
      const rect=card.getBoundingClientRect();
      const x=(event.clientX-rect.left)/rect.width-.5;
      const y=(event.clientY-rect.top)/rect.height-.5;
      card.style.transform=`translateY(-5px) rotateX(${(-y*5).toFixed(2)}deg) rotateY(${(x*6).toFixed(2)}deg)`;
    });
    card.addEventListener('pointerleave',()=>{card.style.transform='';});
  });
}

async function setupThreeScene() {
  try {
    const module = await import('./scene.js');
    await module.mountCampusScene($('#campusCanvas'));
  } catch (error) {
    console.warn('Three.js scene unavailable; CSS hero fallback remains active.', error);
    $('#heroVisual').classList.add('scene-fallback');
  }
}

runBootSequence();
setupNavigation();
setupTheme();
setupCommandPalette();
setupTiltCards();
setupThreeScene();
