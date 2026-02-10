#!/usr/bin/env python3
import sqlite3

try:
    db = sqlite3.connect('vishnorex.db')
    cursor = db.cursor()
    
    print("🔧 Making 'Bharathiyar' school visible...")
    
    # Update the school to make it visible
    cursor.execute('UPDATE schools SET is_hidden = 0 WHERE name = ?', ('Bharathiyar',))
    db.commit()
    
    # Verify the update
    school = cursor.execute('SELECT id, name, is_hidden FROM schools WHERE name = ?', ('Bharathiyar',)).fetchone()
    if school:
        print(f"✅ Updated school: ID: {school[0]}, Name: '{school[1]}', Hidden: {school[2]}")
    
    # Check visible schools again
    visible_schools = cursor.execute('SELECT id, name FROM schools WHERE is_hidden = 0 OR is_hidden IS NULL ORDER BY name').fetchall()
    print(f"\n✅ Visible schools now: {len(visible_schools)}")
    for school in visible_schools:
        print(f"   ID: {school[0]}, Name: '{school[1]}'")
    
    db.close()
    print("\n🎉 School is now visible on login page!")
    
except Exception as e:
    print(f"❌ Error updating database: {e}")
