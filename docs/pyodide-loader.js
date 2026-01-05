// docs/pyodide-loader.js
const PY_FILES = [
  { name: "cadl_interp.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_interp.py" },
  { name: "cadl_fe.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_fe.py" },
  { name: "cadl_interp_walk.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_interp_walk.py" },
  { name: "cadl_symtab.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_symtab.py" },
  { name: "dumpast.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/dumpast.py" },
  { name: "cadl_ascii_render.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_ascii_render.py" },
  { name: "cadl_lexer.py", url: "https://raw.githubusercontent.com/twill386/Cat-ASCII-Design-Language/main/src/cadl_lexer.py" },
];

const SAMPLE_PROGRAM = `
cat Miso {
    mood = "sleepy";
    ears = "pointy";
}
draw Miso;
`;

let pyodide;
const ui = {
  status: document.getElementById("py-status"),
  loadBtn: document.getElementById("py-load-btn"),
  runBtn: document.getElementById("py-run-btn"),
  output: document.getElementById("py-output"),
};

async function loadCadl() {
  ui.status.textContent = "Loading Pyodide…";
  pyodide = await loadPyodide();

  ui.status.textContent = "Fetching CADL files…";
  for (const { name, url } of PY_FILES) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Fetch failed for ${name}: ${res.status}`);
    pyodide.FS.writeFile(name, await res.text());
  }

  ui.status.textContent = "Importing CADL…";
  await pyodide.runPythonAsync(`
import importlib.util, sys
spec = importlib.util.spec_from_file_location("cadl_interp", "cadl_interp.py")
cadl_interp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cadl_interp)
sys.modules["cadl_interp"] = cadl_interp
`);
  ui.status.textContent = "Loaded. Ready.";
}

async function runCadlSample() {
  if (!pyodide) return;
  ui.status.textContent = "Running sample…";
  const result = await pyodide.runPythonAsync(`
import io, contextlib, cadl_interp
source = """${SAMPLE_PROGRAM}"""
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cadl_interp.interp(source, exceptions=True)
buf.getvalue()
`);
  ui.output.textContent = (result && result.trim()) ? result : "Ran sample (no output).";
  ui.status.textContent = "Sample finished.";
}

ui.loadBtn?.addEventListener("click", () => loadCadl().catch(handleError));
ui.runBtn?.addEventListener("click", () => runCadlSample().catch(handleError));

function handleError(err) {
  console.error(err);
  ui.status.textContent = "Error: " + err.message;
}
