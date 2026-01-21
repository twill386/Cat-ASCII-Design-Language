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

let pyodide;
const ui = {
  status: document.getElementById("py-status"),
  loadBtn: document.getElementById("py-load-btn"),
  runBtn: document.getElementById("py-run-btn"),
  output: document.getElementById("py-output"),
};

function enhanceCadlInput() {
  const el = document.getElementById("cadl-input");
  if (!el) return;

  const pairs = {
    "{": "}",
    "(": ")",
    "[": "]",
    "\"": "\"",
    "'": "'",
  };

  el.addEventListener("keydown", (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const { selectionStart, selectionEnd, value } = el;
      const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
      const lineEndIndex = value.indexOf("\n", selectionEnd);
      const lineEnd = lineEndIndex === -1 ? value.length : lineEndIndex;
      const lines = value.slice(lineStart, lineEnd).split("\n");

      if (e.shiftKey) {
        let removed = 0;
        const newText = lines
          .map((line) => {
            if (line.startsWith("  ")) {
              removed += 2;
              return line.slice(2);
            }
            if (line.startsWith("\t")) {
              removed += 1;
              return line.slice(1);
            }
            return line;
          })
          .join("\n");
        el.value = value.slice(0, lineStart) + newText + value.slice(lineEnd);
        el.selectionStart = Math.max(selectionStart - 2, lineStart);
        el.selectionEnd = Math.max(selectionEnd - removed, lineStart);
      } else if (selectionStart !== selectionEnd) {
        const newText = lines.map((line) => "  " + line).join("\n");
        el.value = value.slice(0, lineStart) + newText + value.slice(lineEnd);
        el.selectionStart = selectionStart + 2;
        el.selectionEnd = selectionEnd + 2 * lines.length;
      } else {
        const insert = "  ";
        el.value = value.slice(0, selectionStart) + insert + value.slice(selectionEnd);
        el.selectionStart = el.selectionEnd = selectionStart + insert.length;
      }
      return;
    }

    if (e.key === "Enter") {
      const { selectionStart, selectionEnd, value } = el;
      const lineStart = value.lastIndexOf("\n", selectionStart - 1) + 1;
      const line = value.slice(lineStart, selectionStart);
      const baseIndent = (line.match(/^\s+/) || [""])[0];
      const trimmedLine = line.trimEnd();
      const indentUnit = "  ";
      let newIndent = baseIndent;
      if (trimmedLine.trimStart().startsWith("}")) {
        if (newIndent.startsWith(indentUnit)) {
          newIndent = newIndent.slice(indentUnit.length);
        } else if (newIndent.startsWith("\t")) {
          newIndent = newIndent.slice(1);
        }
      }
      const extraIndent = trimmedLine.endsWith("{") ? indentUnit : "";
      const insert = "\n" + newIndent + extraIndent;
      if (insert !== "\n") {
        e.preventDefault();
        el.value = value.slice(0, selectionStart) + insert + value.slice(selectionEnd);
        el.selectionStart = el.selectionEnd = selectionStart + insert.length;
      }
      return;
    }

    if (!e.ctrlKey && !e.metaKey && !e.altKey && pairs[e.key]) {
      e.preventDefault();
      const { selectionStart, selectionEnd, value } = el;
      const open = e.key;
      const close = pairs[open];
      if (selectionStart !== selectionEnd) {
        const selected = value.slice(selectionStart, selectionEnd);
        el.value =
          value.slice(0, selectionStart) +
          open +
          selected +
          close +
          value.slice(selectionEnd);
        el.selectionStart = selectionStart + 1;
        el.selectionEnd = selectionEnd + 1;
      } else {
        el.value =
          value.slice(0, selectionStart) +
          open +
          close +
          value.slice(selectionEnd);
        el.selectionStart = el.selectionEnd = selectionStart + 1;
      }
    }
  });
}

function getProgramSource() {
  const inputEl = document.getElementById("cadl-input");
  if (inputEl && "value" in inputEl) {
    return (inputEl.value || "").trim();
  }
  const sampleEl = document.getElementById("cadl-sample");
  return (sampleEl?.textContent || "").trim();
}

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
  ui.status.textContent = "CADL is Ready.";
}

async function runCadlSample() {
  if (!pyodide) return;
  const source = getProgramSource();
  if (!source) {
    ui.status.textContent = "No sample source found.";
    return;
  }
  ui.status.textContent = "Running sample…";
  const result = await pyodide.runPythonAsync(`
import io, contextlib, cadl_interp
source = ${JSON.stringify(source)}
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    cadl_interp.interp(source, exceptions=True)
buf.getvalue()
`);
  ui.output.textContent = (result && result.trim()) ? result : "Ran sample (no output).";
  ui.status.textContent = "Executed.";
}

ui.loadBtn?.addEventListener("click", () => loadCadl().catch(handleError));
ui.runBtn?.addEventListener("click", () => runCadlSample().catch(handleError));
enhanceCadlInput();

function handleError(err) {
  console.error(err);
  ui.status.textContent = "Error: " + err.message;
}
