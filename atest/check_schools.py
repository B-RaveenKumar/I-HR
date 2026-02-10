#!/usr/bin/env python3
import sqlite3

try:
    db = sqlite3.connect('vishnorex.db')
    db.row_factory = sqlite3.Row
    cursor = db.cursor()
    
    # Check if schools table exists
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schools'").fetchall()
    if not tables:
        print("❌ Schools table does not exist!")
        db.close()
        exit()
    
    # Check schools table structure
    columns = cursor.execute("PRAGMA table_info(schools)").fetchall()
    print("📊 Schools table structure:")
    for col in columns:
        print(f"   - {col['name']} ({col['type']})")
    
    # Get all schools
    schools = cursor.execute('SELECT id, name, is_hidden FROM schools ORDER BY name').fetchall()
    print(f"\n🏫 Total schools in database: {len(schools)}")
    
    if len(schools) == 0:
        print("❌ No schools found in database!")
    else:
        print("\n📋 Schools list:")
        for school in schools:
            hidden_status = school[2] if len(school) > 2 and school[2] is not None else "NULL"
            print(f"   ID: {school[0]}, Name: '{school[1]}', Hidden: {hidden_status}")
    
    # Check visible schools (what the login page should show)
    visible_schools = cursor.execute('SELECT id, name FROM schools WHERE is_hidden = 0 OR is_hidden IS NULL ORDER BY name').fetchall()
    print(f"\n✅ Visible schools (shown on login): {len(visible_schools)}")
    for school in visible_schools:
        print(f"   ID: {school[0]}, Name: '{school[1]}'")
    
    db.close()
    print("\n✅ Database check completed!")
    
except Exception as e:
    print(f"❌ Error checking database: {e}")
