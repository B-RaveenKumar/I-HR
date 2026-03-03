"""
Dynamic Branding Implementation - Verification Script
Checks if all components are properly configured
"""
import sqlite3
import os
from pathlib import Path

DB_PATH = 'vishnorex.db'

def check_database_schema():
    """Verify database has required columns"""
    print("📊 Checking Database Schema...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(schools)")
    columns = {col[1]: col[2] for col in cursor.fetchall()}
    
    required_columns = ['logo_path', 'branding_enabled']
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"   ❌ Missing columns: {missing}")
        return False
    
    print("   ✅ All required columns exist")
    
    # Show current configuration
    cursor.execute("SELECT id, name, logo_path, branding_enabled FROM schools")
    schools = cursor.fetchall()
    
    print(f"\n   📋 Current Schools Configuration:")
    for school in schools:
        school_id, name, logo_path, branding = school
        logo_status = "✅ Has logo" if logo_path else "⚠️  No logo"
        branding_status = "Enabled" if branding else "Disabled"
        print(f"      {name} (ID: {school_id})")
        print(f"         Logo: {logo_status} ({logo_path if logo_path else 'None'})")
        print(f"         Branding: {branding_status}")
    
    conn.close()
    return True

def check_logo_files():
    """Verify logo files exist"""
    print("\n🖼️  Checking Logo Files...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, logo_path FROM schools WHERE logo_path IS NOT NULL")
    schools = cursor.fetchall()
    
    all_exist = True
    for name, logo_path in schools:
        if os.path.exists(logo_path):
            print(f"   ✅ {name}: {logo_path}")
        else:
            print(f"   ❌ {name}: {logo_path} (FILE NOT FOUND)")
            all_exist = False
    
    conn.close()
    return all_exist

def check_upload_directories():
    """Verify upload directories exist"""
    print("\n📁 Checking Directory Structure...")
    required_dirs = [
        'static/uploads',
        'static/uploads/logos',
        'static/images'
    ]
    
    all_exist = True
    for directory in required_dirs:
        if os.path.exists(directory):
            print(f"   ✅ {directory}")
        else:
            print(f"   ❌ {directory} (MISSING)")
            all_exist = False
    
    return all_exist

def check_template_files():
    """Verify templates have been updated"""
    print("\n📄 Checking Template Files...")
    template_dir = 'templates'
    
    templates_to_check = [
        'admin_dashboard.html',
        'staff_dashboard.html',
        'staff_management.html',
        'salary_management.html',
        'admin_reports.html',
        'admin_settings.html',
        'department_shifts.html',
        'staff_my_profile.html',
        'shift_management.html'
    ]
    
    updated_count = 0
    for template in templates_to_check:
        filepath = os.path.join(template_dir, template)
        if not os.path.exists(filepath):
            print(f"   ⚠️  {template} (NOT FOUND)")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # Check for dynamic branding markers
            has_institution_check = 'institution.logo_path' in content
            has_branding_check = 'institution.branding_enabled' in content
            
            if has_institution_check and has_branding_check:
                print(f"   ✅ {template}")
                updated_count += 1
            else:
                print(f"   ⚠️  {template} (may not be updated)")
    
    return updated_count == len(templates_to_check)

def check_css_files():
    """Verify CSS files have logo styling"""
    print("\n🎨 Checking CSS Files...")
    css_files = [
        'static/css/admin_dashboard.css',
        'static/css/salary_management.css'
    ]
    
    all_updated = True
    for css_file in css_files:
        if not os.path.exists(css_file):
            print(f"   ⚠️  {css_file} (NOT FOUND)")
            all_updated = False
            continue
        
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
            has_logo_class = '.institution-logo' in content
            
            if has_logo_class:
                print(f"   ✅ {css_file}")
            else:
                print(f"   ⚠️  {css_file} (may need logo styles)")
                all_updated = False
    
    return all_updated

def check_app_py():
    """Verify app.py has context processor"""
    print("\n⚙️  Checking app.py...")
    
    if not os.path.exists('app.py'):
        print("   ❌ app.py not found")
        return False
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        has_context_processor = '@app.context_processor' in content and 'inject_institution_branding' in content
        has_login_updates = 'institution_name' in content and 'institution_logo' in content
        
        if has_context_processor:
            print("   ✅ Context processor found")
        else:
            print("   ❌ Context processor missing")
        
        if has_login_updates:
            print("   ✅ Login updates found")
        else:
            print("   ❌ Login updates missing")
        
        return has_context_processor and has_login_updates

def generate_test_instructions():
    """Generate testing instructions"""
    print("\n" + "="*60)
    print("📝 TESTING INSTRUCTIONS")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM schools LIMIT 2")
    schools = cursor.fetchall()
    conn.close()
    
    if schools:
        print("\n✅ Ready to Test! Follow these steps:\n")
        print("1. Restart Flask Application:")
        print("   python app.py\n")
        
        for idx, (school_id, name) in enumerate(schools, 1):
            print(f"{idx + 1}. Test {name}:")
            print(f"   - Select '{name}' from login page")
            print(f"   - Log in with admin/staff credentials")
            print(f"   - Expected: Sidebar shows '{name}' with custom logo")
            print()
        
        print(f"{len(schools) + 2}. Navigate to different pages:")
        print("   - Staff Management")
        print("   - Salary Management")
        print("   - Admin Reports")
        print("   - Expected: Same branding appears consistently\n")
        
        print(f"{len(schools) + 3}. Test Fallback:")
        print("   - Run: UPDATE schools SET branding_enabled = 0 WHERE id = 1;")
        print("   - Log in again")
        print("   - Expected: Shows default 'VishnoRex' branding\n")

if __name__ == '__main__':
    print("="*60)
    print("DYNAMIC BRANDING IMPLEMENTATION VERIFICATION")
    print("="*60)
    print()
    
    results = {
        'Database Schema': check_database_schema(),
        'Logo Files': check_logo_files(),
        'Directory Structure': check_upload_directories(),
        'Template Updates': check_template_files(),
        'CSS Updates': check_css_files(),
        'Backend Updates': check_app_py()
    }
    
    print("\n" + "="*60)
    print("📊 VERIFICATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "🎉" * 20)
        print("✅ ALL CHECKS PASSED!")
        print("🎉" * 20)
        generate_test_instructions()
    else:
        print("\n" + "⚠️ " * 20)
        print("❌ SOME CHECKS FAILED")
        print("Please review the issues above and run migration script if needed.")
        print("⚠️ " * 20)
    
    print("\n" + "="*60)
    print("For detailed documentation, see:")
    print("  - DYNAMIC_BRANDING_IMPLEMENTATION.md (complete guide)")
    print("  - DYNAMIC_BRANDING_QUICKSTART.md (quick reference)")
    print("="*60)
