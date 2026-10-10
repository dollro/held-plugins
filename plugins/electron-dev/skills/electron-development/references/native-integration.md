# Native OS Integration

## System Menu Bar

```javascript
const { Menu, app, shell } = require('electron');

function createApplicationMenu(mainWindow) {
  const isMac = process.platform === 'darwin';

  const template = [
    // App menu (macOS only)
    ...(isMac ? [{
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        {
          label: 'Preferences...',
          accelerator: 'Cmd+,',
          click: () => mainWindow.webContents.send('menu:preferences')
        },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' }
      ]
    }] : []),

    // File menu
    {
      label: 'File',
      submenu: [
        {
          label: 'New',
          accelerator: 'CmdOrCtrl+N',
          click: () => mainWindow.webContents.send('menu:new')
        },
        {
          label: 'Open...',
          accelerator: 'CmdOrCtrl+O',
          click: async () => {
            const { filePaths } = await dialog.showOpenDialog(mainWindow, {
              properties: ['openFile'],
              filters: [{ name: 'Documents', extensions: ['txt', 'md'] }]
            });
            if (filePaths.length > 0) {
              mainWindow.webContents.send('menu:open', filePaths[0]);
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Save',
          accelerator: 'CmdOrCtrl+S',
          click: () => mainWindow.webContents.send('menu:save')
        },
        { type: 'separator' },
        isMac ? { role: 'close' } : { role: 'quit' }
      ]
    },

    // Edit menu
    {
      label: 'Edit',
      submenu: [
        { role: 'undo' },
        { role: 'redo' },
        { type: 'separator' },
        { role: 'cut' },
        { role: 'copy' },
        { role: 'paste' },
        ...(isMac ? [
          { role: 'pasteAndMatchStyle' },
          { role: 'delete' },
          { role: 'selectAll' },
        ] : [
          { role: 'delete' },
          { type: 'separator' },
          { role: 'selectAll' }
        ])
      ]
    },

    // View menu
    {
      label: 'View',
      submenu: [
        { role: 'reload' },
        { role: 'forceReload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'resetZoom' },
        { role: 'zoomIn' },
        { role: 'zoomOut' },
        { type: 'separator' },
        { role: 'togglefullscreen' }
      ]
    },

    // Help menu
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => shell.openExternal('https://yourapp.com/docs')
        },
        {
          label: 'Report Issue',
          click: () => shell.openExternal('https://github.com/yourapp/issues')
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}
```

## Context Menus

```javascript
// preload.js - Expose context menu API
contextBridge.exposeInMainWorld('electronAPI', {
  showContextMenu: (menuId, data) => {
    ipcRenderer.send('context-menu:show', menuId, data);
  }
});

// main.js - Handle context menu
ipcMain.on('context-menu:show', (event, menuId, data) => {
  const window = BrowserWindow.fromWebContents(event.sender);

  const menus = {
    'text-selection': [
      { label: 'Copy', role: 'copy' },
      { label: 'Cut', role: 'cut' },
      { label: 'Paste', role: 'paste' },
      { type: 'separator' },
      {
        label: 'Search Google',
        click: () => {
          shell.openExternal(`https://google.com/search?q=${encodeURIComponent(data.text)}`);
        }
      }
    ],
    'file-item': [
      {
        label: 'Open',
        click: () => event.sender.send('context-menu:action', 'open', data)
      },
      {
        label: 'Delete',
        click: () => event.sender.send('context-menu:action', 'delete', data)
      },
      { type: 'separator' },
      {
        label: 'Show in Finder',
        click: () => shell.showItemInFolder(data.path)
      }
    ]
  };

  const template = menus[menuId] || [];
  const menu = Menu.buildFromTemplate(template);
  menu.popup({ window });
});

// renderer.js - Trigger context menu
document.addEventListener('contextmenu', (event) => {
  event.preventDefault();

  const selection = window.getSelection().toString();
  if (selection) {
    window.electronAPI.showContextMenu('text-selection', { text: selection });
  } else if (event.target.dataset.filePath) {
    window.electronAPI.showContextMenu('file-item', {
      path: event.target.dataset.filePath
    });
  }
});
```

## File Associations

```javascript
// package.json - electron-builder configuration
{
  "build": {
    "fileAssociations": [
      {
        "ext": "myapp",
        "name": "MyApp Document",
        "description": "MyApp Document File",
        "mimeType": "application/x-myapp",
        "role": "Editor",
        "icon": "icons/document.icns"
      }
    ],
    "protocols": [
      {
        "name": "MyApp Protocol",
        "schemes": ["myapp"]
      }
    ]
  }
}

// main.js - Handle file open events
app.on('open-file', (event, filePath) => {
  event.preventDefault();

  if (mainWindow) {
    mainWindow.webContents.send('file:open-external', filePath);
  } else {
    // Store for when window is ready
    global.fileToOpen = filePath;
  }
});

// Handle protocol URLs
app.on('open-url', (event, url) => {
  event.preventDefault();

  const parsed = new URL(url);
  if (parsed.protocol === 'myapp:') {
    handleProtocolAction(parsed);
  }
});

// Windows: Handle via command line arguments
app.on('second-instance', (event, argv) => {
  const filePath = argv.find(arg => arg.endsWith('.myapp'));
  if (filePath && mainWindow) {
    mainWindow.webContents.send('file:open-external', filePath);
    mainWindow.focus();
  }
});
```

## System Tray

```javascript
const { Tray, Menu, nativeImage } = require('electron');

class TrayManager {
  constructor(mainWindow) {
    this.mainWindow = mainWindow;
    this.tray = null;
  }

  create() {
    // Create tray icon
    const iconPath = process.platform === 'darwin'
      ? 'icons/trayTemplate.png'  // Template image for macOS
      : 'icons/tray.png';

    const icon = nativeImage.createFromPath(iconPath);
    this.tray = new Tray(icon);

    // Set tooltip
    this.tray.setToolTip('MyApp');

    // Create context menu
    this.updateContextMenu();

    // Handle click
    this.tray.on('click', () => {
      if (this.mainWindow.isVisible()) {
        this.mainWindow.hide();
      } else {
        this.mainWindow.show();
        this.mainWindow.focus();
      }
    });

    // Handle double-click (Windows)
    this.tray.on('double-click', () => {
      this.mainWindow.show();
      this.mainWindow.focus();
    });
  }

  updateContextMenu(status = 'idle') {
    const statusIcons = {
      idle: '',
      syncing: '',
      error: ''
    };

    const contextMenu = Menu.buildFromTemplate([
      {
        label: `Status: ${statusIcons[status]} ${status}`,
        enabled: false
      },
      { type: 'separator' },
      {
        label: 'Open MyApp',
        click: () => {
          this.mainWindow.show();
          this.mainWindow.focus();
        }
      },
      {
        label: 'Preferences...',
        click: () => {
          this.mainWindow.show();
          this.mainWindow.webContents.send('menu:preferences');
        }
      },
      { type: 'separator' },
      {
        label: 'Quit',
        click: () => app.quit()
      }
    ]);

    this.tray.setContextMenu(contextMenu);
  }

  // Update icon for different states
  setIcon(state) {
    const icons = {
      normal: 'icons/tray.png',
      notification: 'icons/tray-notification.png',
      syncing: 'icons/tray-syncing.png'
    };

    const icon = nativeImage.createFromPath(icons[state] || icons.normal);
    this.tray.setImage(icon);
  }

  destroy() {
    if (this.tray) {
      this.tray.destroy();
      this.tray = null;
    }
  }
}
```

## Native Notifications

On macOS, current Electron only shows notifications from a code-signed app; unsigned dev builds will not show them (see `code-signing.md`). Renderers can also use the web `Notification` API.

```javascript
const { Notification, nativeImage } = require('electron');

class NotificationManager {
  constructor() {
    // Check if notifications are supported
    this.isSupported = Notification.isSupported();
  }

  show({ title, body, icon, actions, urgency = 'normal' }) {
    if (!this.isSupported) {
      console.warn('Notifications not supported on this platform');
      return null;
    }

    const notification = new Notification({
      title,
      body,
      icon: icon ? nativeImage.createFromPath(icon) : undefined,
      urgency, // 'low', 'normal', 'critical'
      silent: urgency === 'low',
      actions: actions || [],
      hasReply: false,
    });

    notification.on('click', () => {
      // Focus the app window
      if (mainWindow) {
        mainWindow.show();
        mainWindow.focus();
      }
    });

    notification.on('action', (event, index) => {
      // Handle action button clicks
      if (actions && actions[index]) {
        actions[index].callback?.();
      }
    });

    notification.show();
    return notification;
  }

  // Convenience methods
  info(title, body) {
    return this.show({ title, body, urgency: 'normal' });
  }

  success(title, body) {
    return this.show({
      title,
      body,
      icon: 'icons/success.png',
      urgency: 'low'
    });
  }

  error(title, body) {
    return this.show({
      title,
      body,
      icon: 'icons/error.png',
      urgency: 'critical'
    });
  }
}
```

## Clipboard and Dropped Files

- Renderers have no `clipboard` module any more (deprecated, then removed). Use the web Clipboard API there (`navigator.clipboard.readText()`, `writeText()`, `ClipboardItem`), gated by the permission handler in security.md.
- In main, the `clipboard` module remains, but its read/write methods are asynchronous in current Electron: `await` them (e.g. `await clipboard.readText()`) and don't rely on older synchronous examples. Check the [clipboard API](https://www.electronjs.org/docs/latest/api/clipboard) for your version.
- `File.path` no longer exists (removed in v32). Resolve a dropped/selected file's path in the preload with `webUtils.getPathForFile(file)` (see process-architecture.md).
