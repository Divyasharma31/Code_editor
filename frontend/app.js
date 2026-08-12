const API_URL = 'http://localhost:8000/api';
let editor = null;

document.addEventListener('DOMContentLoaded', () => {
    const path = window.location.pathname;
    if (path.endsWith('index.html') || path === '/' || path.endsWith('/')) {
        initDashboard();
    } else if (path.endsWith('solve.html')) {
        initSolvePage();
    }
});

// --- Dashboard Logic ---
function initDashboard() {
    loadQuestions();

    const modal = document.getElementById('addModal');
    const openBtn = document.getElementById('openModalBtn');
    const closeBtn = document.getElementById('closeModalBtn');
    const parseBtn = document.getElementById('parseBtn');

    openBtn.onclick = () => modal.style.display = 'block';
    closeBtn.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => { if (e.target == modal) modal.style.display = 'none'; }

    parseBtn.onclick = async () => {
        const promptTxt = document.getElementById('promptInput').value;
        const status = document.getElementById('parseStatus');
        
        if (!promptTxt.trim()) {
            status.innerHTML = '<span class="error">Please enter a prompt.</span>';
            return;
        }

        status.innerHTML = 'Parsing and saving...';
        
        try {
            // 1. Parse prompt
            let pRes = await fetch(`${API_URL}/parse-question`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt: promptTxt})
            });
            let parsedData = await pRes.json();

            // 2. Create question in DB
            let cRes = await fetch(`${API_URL}/questions`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(parsedData)
            });
            
            if (cRes.ok) {
                status.innerHTML = '<span class="success">Problem created successfully!</span>';
                document.getElementById('promptInput').value = '';
                setTimeout(() => {
                    modal.style.display = 'none';
                    loadQuestions();
                }, 1000);
            } else {
                throw new Error("Failed to save");
            }
        } catch (err) {
            status.innerHTML = `<span class="error">Error: ${err.message}</span>`;
        }
    };
}

async function loadQuestions() {
    const list = document.getElementById('problemList');
    if (!list) return;

    try {
        let res = await fetch(`${API_URL}/questions`);
        let questions = await res.json();
        list.innerHTML = '';
        
        if (questions.length === 0) {
            list.innerHTML = '<p style="color: var(--text-secondary)">No problems found. Add one to get started!</p>';
            return;
        }

        questions.forEach(q => {
            let card = document.createElement('div');
            card.className = 'problem-card';
            card.innerHTML = `
                <div>
                    <h3>${q.title}</h3>
                </div>
                <a href="solve.html?id=${q.id}" class="btn primary-btn">Solve</a>
            `;
            list.appendChild(card);
        });
    } catch (err) {
        list.innerHTML = '<span class="error">Failed to load questions. Is backend running?</span>';
    }
}

// --- Solve Page Logic ---
async function initSolvePage() {
    const urlParams = new URLSearchParams(window.location.search);
    const qId = urlParams.get('id');
    
    if (!qId) {
        document.getElementById('probTitle').innerText = 'No question selected';
        return;
    }

    try {
        let res = await fetch(`${API_URL}/questions/${qId}`);
        if (!res.ok) throw new Error("Question not found");
        let q = await res.json();
        
        document.getElementById('probTitle').innerText = q.title;
        document.getElementById('probDesc').innerHTML = `<pre>${q.description}</pre>`;
        document.getElementById('probTimeLimit').innerText = q.time_limit_ms;
        
        if (q.constraints) {
            document.getElementById('constraintsContainer').style.display = 'block';
            document.getElementById('probConstraints').innerText = q.constraints;
        }

        const samplesDiv = document.getElementById('probSamples');
        q.test_cases.forEach((tc, idx) => {
            samplesDiv.innerHTML += `
                <div class="tc-result" style="margin-top:10px; background:var(--bg-panel)">
                    <div class="tc-title">Example ${idx + 1}</div>
                    <strong>Input:</strong> <pre style="display:inline">${tc.input}</pre><br>
                    <strong>Output:</strong> <pre style="display:inline">${tc.expected_output}</pre>
                </div>
            `;
        });

    } catch (err) {
        document.getElementById('probTitle').innerText = 'Error loading question';
    }

    // Init Monaco Editor
    require(['vs/editor/editor.main'], function () {
        editor = monaco.editor.create(document.getElementById('editor'), {
            value: '# Write your code here\n',
            language: 'python',
            theme: 'vs-dark',
            automaticLayout: true,
            fontSize: 14
        });
    });

    const langSelect = document.getElementById('languageSelect');
    langSelect.addEventListener('change', (e) => {
        if (editor) {
            let lang = e.target.value;
            if(lang === 'javascript') lang = 'javascript'; // valid monaco ID
            if(lang === 'python') lang = 'python';
            if(lang === 'cpp') lang = 'cpp';
            monaco.editor.setModelLanguage(editor.getModel(), lang);
        }
    });

    const runBtn = document.getElementById('runBtn');
    runBtn.onclick = async () => {
        if (!editor) return;
        const code = editor.getValue();
        const lang = langSelect.value;
        const consoleOut = document.getElementById('consoleOutput');
        
        runBtn.innerText = 'Running...';
        runBtn.disabled = true;
        consoleOut.innerHTML = 'Executing on server...';

        try {
            let res = await fetch(`${API_URL}/questions/${qId}/run`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({language: lang, code: code})
            });
            let data = await res.json();
            
            if (data.status === 'Error') {
                consoleOut.innerHTML = `<span class="error">${data.message}</span>`;
            } else {
                let statusColor = data.overall_status === 'Accepted' ? 'var(--success)' : 'var(--danger)';
                let html = `<h2 style="color:${statusColor}; margin-bottom:1rem;">Status: ${data.overall_status}</h2>`;
                
                data.results.forEach(r => {
                    let tcClass = r.passed ? 'passed' : 'failed';
                    let statusLabel = r.passed ? 'Passed' : r.status;
                    
                    html += `
                        <div class="tc-result ${tcClass}">
                            <div class="tc-title">Test Case ${r.test_case} - ${statusLabel} (${r.time_taken_ms} ms)</div>
                            <div><strong>Expected:</strong> <pre style="display:inline">${r.expected_output}</pre></div>
                            <div><strong>Actual:</strong> <pre style="display:inline">${r.actual_output}</pre></div>
                            ${r.error ? `<div><strong class="error">Error:</strong> <pre>${r.error}</pre></div>` : ''}
                        </div>
                    `;
                });
                consoleOut.innerHTML = html;
            }
        } catch (err) {
            consoleOut.innerHTML = `<span class="error">Failed to connect to server.</span>`;
        } finally {
            runBtn.innerText = 'Run Code';
            runBtn.disabled = false;
        }
    };
}
