"""
Windows Service Installer for Vishnorex Biometric Agent
Creates a Windows service that auto-starts with system
"""

import sys
import os
import subprocess
from pathlib import Path


def install_service():
    """Install agent as Windows service using NSSM"""
    print("=" * 60)
    print("Vishnorex Biometric Agent - Service Installer")
    print("=" * 60)
    print()
    
    # Check if running as administrator
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("ERROR: This installer must be run as Administrator!")
        print("Right-click and select 'Run as administrator'")
        input("\nPress Enter to exit...")
        return
    
    # Get paths
    agent_dir = Path(__file__).parent.absolute()
    agent_script = agent_dir / "biometric_agent.py"
    python_exe = sys.executable
    
    print(f"Agent Directory: {agent_dir}")
    print(f"Agent Script: {agent_script}")
    print(f"Python Executable: {python_exe}")
    print()
    
    # Check if NSSM is available
    nssm_path = agent_dir / "nssm.exe"
    if not nssm_path.exists():
        print("NSSM (Non-Sucking Service Manager) not found!")
        print(f"Please download nssm.exe from https://nssm.cc/download")
        print(f"and place it in: {agent_dir}")
        input("\nPress Enter to exit...")
        return
    
    service_name = "VishnorexBiometricAgent"
    
    # Check if service already exists
    try:
        result = subprocess.run([str(nssm_path), "status", service_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Service '{service_name}' already exists!")
            choice = input("Do you want to reinstall? (y/n): ")
            if choice.lower() == 'y':
                print("Removing existing service...")
                subprocess.run([str(nssm_path), "stop", service_name], check=False)
                subprocess.run([str(nssm_path), "remove", service_name, "confirm"], check=False)
                print("Existing service removed.")
            else:
                print("Installation cancelled.")
                input("\nPress Enter to exit...")
                return
    except:
        pass
    
    print(f"\nInstalling service '{service_name}'...")
    
    # Install service
    try:
        # Install service with pythonw (no console window)
        pythonw_exe = str(Path(python_exe).parent / "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = python_exe
        
        subprocess.run([
            str(nssm_path), "install", service_name,
            pythonw_exe, str(agent_script)
        ], check=True)
        
        # Set service description
        subprocess.run([
            str(nssm_path), "set", service_name,
            "Description", "Vishnorex Biometric Device Agent - Syncs attendance from local ZK devices"
        ], check=True)
        
        # Set startup type to automatic
        subprocess.run([
            str(nssm_path), "set", service_name,
            "Start", "SERVICE_AUTO_START"
        ], check=True)
        
        # Set working directory
        subprocess.run([
            str(nssm_path), "set", service_name,
            "AppDirectory", str(agent_dir.parent)
        ], check=True)
        
        # Set log files
        subprocess.run([
            str(nssm_path), "set", service_name,
            "AppStdout", str(agent_dir / "service_output.log")
        ], check=True)
        
        subprocess.run([
            str(nssm_path), "set", service_name,
            "AppStderr", str(agent_dir / "service_error.log")
        ], check=True)
        
        print(f"\n✓ Service '{service_name}' installed successfully!")
        print()
        print("Next steps:")
        print(f"1. Configure the agent (run biometric_agent.py manually first)")
        print(f"2. Start the service: nssm start {service_name}")
        print(f"3. Or start manually from Windows Services")
        print()
        
        choice = input("Do you want to start the service now? (y/n): ")
        if choice.lower() == 'y':
            print(f"Starting service...")
            result = subprocess.run([str(nssm_path), "start", service_name], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Service started successfully!")
            else:
                print(f"Failed to start service: {result.stderr}")
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Installation failed: {e}")
        print("Please check the error messages above.")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
    
    input("\nPress Enter to exit...")


def uninstall_service():
    """Uninstall Windows service"""
    print("=" * 60)
    print("Vishnorex Biometric Agent - Service Uninstaller")
    print("=" * 60)
    print()
    
    # Check if running as administrator
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False
    
    if not is_admin:
        print("ERROR: This uninstaller must be run as Administrator!")
        print("Right-click and select 'Run as administrator'")
        input("\nPress Enter to exit...")
        return
    
    agent_dir = Path(__file__).parent.absolute()
    nssm_path = agent_dir / "nssm.exe"
    service_name = "VishnorexBiometricAgent"
    
    if not nssm_path.exists():
        print("NSSM not found! Cannot uninstall service.")
        input("\nPress Enter to exit...")
        return
    
    print(f"Uninstalling service '{service_name}'...")
    
    try:
        # Stop service
        subprocess.run([str(nssm_path), "stop", service_name], check=False)
        print("Service stopped.")
        
        # Remove service
        result = subprocess.run([str(nssm_path), "remove", service_name, "confirm"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✓ Service '{service_name}' uninstalled successfully!")
        else:
            print(f"Service removal completed with warnings.")
            
    except Exception as e:
        print(f"✗ Uninstallation error: {e}")
    
    input("\nPress Enter to exit...")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'uninstall':
        uninstall_service()
    else:
        install_service()
