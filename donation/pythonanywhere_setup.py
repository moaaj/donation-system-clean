#!/usr/bin/env python3
"""
PythonAnywhere Setup Script for Django Donation App
Run this in PythonAnywhere console after uploading your files
"""

import os
import subprocess
import sys

def run_command(command, description):
    """Run a command and print the result"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Success!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - Error!")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False

def main():
    print("🚀 Setting up Django Donation App on PythonAnywhere...")
    
    # Change to project directory
    project_dir = "/home/moaaj/donation"  # Adjust username as needed
    
    if os.path.exists(project_dir):
        os.chdir(project_dir)
        print(f"📁 Changed to directory: {project_dir}")
    else:
        print(f"❌ Project directory not found: {project_dir}")
        print("Please upload your donation folder first!")
        return
    
    # Install requirements
    run_command("pip3.11 install --user -r requirements.txt", "Installing requirements")
    
    # Run migrations
    run_command("python3.11 manage.py migrate", "Running database migrations")
    
    # Collect static files
    run_command("python3.11 manage.py collectstatic --noinput", "Collecting static files")
    
    # Create superuser (optional)
    print("\n🔑 To create a superuser later, run:")
    print("python3.11 manage.py createsuperuser")
    
    print("\n🎉 Setup complete!")
    print("Now go to the Web tab and configure your Django app!")

if __name__ == "__main__":
    main()
