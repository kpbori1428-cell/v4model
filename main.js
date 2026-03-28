const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let streamlitProcess;
let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    title: "Vertex AI Agent Suite - Desktop",
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Start Streamlit server via specialized launcher
  // This ensures the correct environment and flags are used for the desktop version
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  streamlitProcess = spawn(pythonCmd, ['launcher.py']);

  streamlitProcess.stdout.on('data', (data) => {
    console.log(`Streamlit: ${data}`);
    // Once Streamlit starts, load the URL
    if (data.toString().includes('Local URL: http://localhost:8501')) {
      mainWindow.loadURL('http://localhost:8501');
    }
  });

  streamlitProcess.stderr.on('data', (data) => {
    console.error(`Streamlit Error: ${data}`);
  });

  mainWindow.on('closed', function () {
    mainWindow = null;
    if (streamlitProcess) {
      streamlitProcess.kill();
    }
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', function () {
  if (mainWindow === null) {
    createWindow();
  }
});

app.on('quit', () => {
  if (streamlitProcess) {
    streamlitProcess.kill();
  }
});
