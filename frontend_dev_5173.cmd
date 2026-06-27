@echo off
cd /d "%~dp0frontend"
set "PATH=C:\Users\gram\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;%PATH%"
set "VITE_API_BASE_URL=http://127.0.0.1:8010"
"C:\Users\gram\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd" dev --host 127.0.0.1 --port 5173
