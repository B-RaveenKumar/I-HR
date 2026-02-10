#!/usr/bin/env python3
import sqlite3
from datetime import datetime

try:
    db = sqlite3.connect('vishnorex.db')
    cursor = db.cursor()
    
    print("🏫 Adding sample schools to the database...")
    
    schools_to_add = [
        ("St. Mary's Higher Secondary School", "123 Main Street, Chennai", "contact@stmarys.edu", "9876543210"),
        ("Government Higher Secondary School", "456 Government Road, Bangalore", "info@ghss.gov.in", "9876543211"),
        ("Holy Cross Matriculation School", "789 Church Street, Coimbatore", "admin@holycross.edu", "9876543212"),
        ("DAV Public School", "321 Park Avenue, Madurai", "office@dav.edu.in", "9876543213")
    ]
    
    for school_name, address, email, phone in schools_to_add:
        # Check if school already exists
        existing = cursor.execute('SELECT id FROM schools WHERE name = ?', (school_name,)).fetchone()
        if not existing:
            cursor.execute('''
                INSERT INTO schools (name, address, contact_email, contact_phone, created_at, is_hidden)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (school_name, address, email, phone, datetime.now(), 0))
            print(f"✅ Added: {school_name}")
        else:
            print(f"⚠️ Already exists: {school_name}")
    
    db.commit()
    
    # Show all visible schools
    visible_schools = cursor.execute('SELECT id, name FROM schools WHERE is_hidden = 0 OR is_hidden IS NULL ORDER BY name').fetchall()
    print(f"\n📋 All visible schools ({len(visible_schools)}):")
    for school in visible_schools:
        print(f"   ID: {school[0]}, Name: '{school[1]}'")
    
    db.close()
    print("\n🎉 Sample schools added successfully!")
    
except Exception as e:
    print(f"❌ Error adding schools: {e}")
