const { app, BrowserWindow, shell } = require('electron');
const path = require('path');
const fs = require('fs');

function getTargetUrl() {
  if (process.env.IHR_APP_URL) {
    return process.env.IHR_APP_URL;
  }

  const capacitorConfigPath = path.join(__dirname, '..', 'capacitor.config.json');
  try {
    const capacitorConfig = JSON.parse(fs.readFileSync(capacitorConfigPath, 'utf8'));
    if (capacitorConfig.server && capacitorConfig.server.url) {
      return capacitorConfig.server.url;
    }
  } catch (error) {
    // Ignore parse/read errors and fall back to localhost.
  }

  return 'http://127.0.0.1:5000';
}

function createWindow() {
  const mainWindow = new BrowserWindow({
    width: 1400,
    height: 950,
    minWidth: 1100,
    minHeight: 720,
    backgroundColor: '#0f172a',
    icon: path.join(__dirname, '..', 'static', 'images', 'favicon.ico'),
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  const targetUrl = getTargetUrl();
  mainWindow.loadURL(targetUrl);

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
    }
    return { action: 'deny' };
  });
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});