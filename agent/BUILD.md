# Vishnorex Biometric Agent - Build Instructions

This guide explains how to create a standalone executable (.exe) from the Python agent.

## Why Build an Executable?

- ✅ **No Python installation required** on target machines
- ✅ **Single file distribution** - easier deployment
- ✅ **Professional appearance** - looks like a native Windows app
- ✅ **Simpler for end users** - just double-click to run

---

## Prerequisites

1. Python 3.8+ installed
2. Agent dependencies installed (`pip install -r requirements.txt`)
3. PyInstaller installed (`pip install pyinstaller`)

---

## Build Instructions

### Method 1: Using PyInstaller (Recommended)

#### Step 1: Install PyInstaller

```cmd
pip install pyinstaller
```

#### Step 2: Create Build

Navigate to the agent directory:
```cmd
cd "d:\Vishnorex-srk-Final\SM-DL-AWMS-SAC\SRK other version\Staff Management\agent"
```

Run PyInstaller:
```cmd
pyinstaller --onefile --windowed --name="VishnorexBiometricAgent" --icon=icon.ico biometric_agent.py
```

**Options explained:**
- `--onefile`: Bundle everything into a single .exe
- `--windowed`: No console window (GUI only)
- `--name`: Output filename
- `--icon`: Application icon (optional)

#### Step 3: Locate Executable

The compiled .exe will be in:
```
agent\dist\VishnorexBiometricAgent.exe
```

#### Step 4: Test Executable

Double-click `VishnorexBiometricAgent.exe` to run.

---

### Method 2: Advanced Build with Spec File

For more control, create a spec file:

**agent.spec:**
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['biometric_agent.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../zk_biometric.py', '.'),  # Include zk_biometric module
    ],
    hiddenimports=['PyQt5.sip'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VishnorexBiometricAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)
```

Build with:
```cmd
pyinstaller agent.spec
```

---

## Distribution Package

Create a deployment package with:

```
VishnorexBiometricAgent/
├── VishnorexBiometricAgent.exe    (compiled executable)
├── config.json.example             (sample configuration)
├── README.md                       (user documentation)
├── QUICKSTART.md                   (quick start guide)
├── install_service.py              (service installer)
├── nssm.exe                        (service manager)
└── icon.ico                        (application icon)
```

### Create Installer (Optional)

Use **Inno Setup** or **NSIS** to create a professional installer:

**Example Inno Setup script** (`installer.iss`):
```inno
[Setup]
AppName=Vishnorex Biometric Agent
AppVersion=1.0.0
DefaultDirName={pf}\VishnorexBiometricAgent
DefaultGroupName=Vishnorex
OutputBaseFilename=VishnorexBiometricAgent-Setup
Compression=lzma2
SolidCompression=yes

[Files]
Source: "dist\VishnorexBiometricAgent.exe"; DestDir: "{app}"
Source: "config.json.example"; DestDir: "{app}"
Source: "README.md"; DestDir: "{app}"
Source: "QUICKSTART.md"; DestDir: "{app}"
Source: "nssm.exe"; DestDir: "{app}"
Source: "install_service.py"; DestDir: "{app}"

[Icons]
Name: "{group}\Vishnorex Biometric Agent"; Filename: "{app}\VishnorexBiometricAgent.exe"
Name: "{group}\Uninstall"; Filename: "{uninstallexe}"
```

Compile with Inno Setup to create `VishnorexBiometricAgent-Setup.exe`.

---

## Troubleshooting Build Issues

### Issue: "Module not found" error

**Solution**: Add missing modules to `hiddenimports` in spec file:
```python
hiddenimports=['PyQt5.sip', 'requests', 'threading']
```

### Issue: zk_biometric.py not found

**Solution**: Add to `datas` in spec file:
```python
datas=[('../zk_biometric.py', '.')],
```

### Issue: Executable size too large

**Solutions**:
1. Use UPX compression: `--upx` flag (already enabled)
2. Exclude unnecessary packages:
   ```python
   excludes=['tkinter', 'matplotlib', 'pandas']
   ```

### Issue: Antivirus flags executable

**Solution**: 
1. Code-sign the executable (requires certificate)
2. Add exclusion to antivirus
3. Use `--windowed` to avoid console window (looks less suspicious)

---

## Testing the Build

### Basic Test
```cmd
dist\VishnorexBiometricAgent.exe
```

Should open the GUI window.

### Service Test
```cmd
cd dist
python ..\install_service.py
```

Should install the service successfully.

---

## Automated Build Script

Create `build.bat`:
```batch
@echo off
echo Building Vishnorex Biometric Agent...

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller

REM Clean previous build
rmdir /s /q build dist
del /f VishnorexBiometricAgent.spec

REM Build executable
pyinstaller --onefile --windowed --name="VishnorexBiometricAgent" --icon=icon.ico biometric_agent.py

REM Copy additional files to dist
copy config.json.example dist\
copy README.md dist\
copy QUICKSTART.md dist\
copy install_service.py dist\
copy nssm.exe dist\ 2>nul

echo.
echo Build complete! Executable is in dist\ folder
pause
```

Run with:
```cmd
build.bat
```

---

## Version Information

To embed version information in the .exe:

**version_info.txt:**
```
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, 0, 0),
    prodvers=(1, 0, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Vishnorex'),
        StringStruct(u'FileDescription', u'Vishnorex Biometric Agent'),
        StringStruct(u'FileVersion', u'1.0.0.0'),
        StringStruct(u'InternalName', u'VishnorexBiometricAgent'),
        StringStruct(u'OriginalFilename', u'VishnorexBiometricAgent.exe'),
        StringStruct(u'ProductName', u'Vishnorex Staff Management System'),
        StringStruct(u'ProductVersion', u'1.0.0.0')])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
```

Build with version info:
```cmd
pyinstaller --onefile --windowed --version-file=version_info.txt biometric_agent.py
```

---

## Best Practices

1. ✅ **Test thoroughly** before distributing
2. ✅ **Include documentation** (README, QUICKSTART)
3. ✅ **Provide sample config** (config.json.example)
4. ✅ **Use proper icon** (professional appearance)
5. ✅ **Sign executable** (for production use)
6. ✅ **Version your builds** (track releases)
7. ✅ **Keep source separate** (don't distribute .py files)

---

## Next Steps

After building:
1. Test on a clean Windows machine (no Python installed)
2. Create user guide for your specific organization
3. Set up update mechanism (auto-update or manual download)
4. Consider code signing for production deployment

---

## Support

For build issues, check:
- PyInstaller documentation: https://pyinstaller.org/
- Spec file reference: https://pyinstaller.org/en/stable/spec-files.html
- Common issues: https://github.com/pyinstaller/pyinstaller/wiki
