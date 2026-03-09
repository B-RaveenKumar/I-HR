#!/usr/bin/env python3
"""
Add Sample Students to Database
This script adds sample student accounts for testing the student portal
"""

import sqlite3
from werkzeug.security import generate_password_hash
import os

def add_sample_students():
    """Add sample students to the database"""
    
    # Connect to database
    db_path = 'attendance.db'
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Please run the main application first to create the database.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if students table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='students'")
    if not cursor.fetchone():
        print("❌ Students table doesn't exist. Please run the application first.")
        conn.close()
        return
    
    # Get available schools
    cursor.execute("SELECT id, name FROM schools")
    schools = cursor.fetchall()
    
    if not schools:
        print("❌ No schools found. Please add a school first.")
        conn.close()
        return
    
    print(f"✓ Found {len(schools)} school(s)")
    
    # Use first school for sample data
    school_id = schools[0][0]
    school_name = schools[0][1]
    print(f"✓ Using school: {school_name} (ID: {school_id})")
    
    # Sample students data
    sample_students = [
        {
            'student_id': 'STU001',
            'password': 'password123',  # Will be hashed
            'full_name': 'Rahul Kumar',
            'first_name': 'Rahul',
            'last_name': 'Kumar',
            'email': 'rahul.kumar@example.com',
            'phone': '9876543210',
            'class': '10th',
            'section': 'A',
            'roll_number': '01',
            'gender': 'Male',
            'date_of_birth': '2010-05-15',
            'date_of_admission': '2023-04-01',
            'parent_name': 'Mr. Rajesh Kumar',
            'parent_phone': '9876543211',
            'parent_email': 'rajesh.kumar@example.com',
            'address': '123 Main Street, City',
            'theme_preference': 'light'
        },
        {
            'student_id': 'STU002',
            'password': 'password123',
            'full_name': 'Priya Sharma',
            'first_name': 'Priya',
            'last_name': 'Sharma',
            'email': 'priya.sharma@example.com',
            'phone': '9876543212',
            'class': '10th',
            'section': 'A',
            'roll_number': '02',
            'gender': 'Female',
            'date_of_birth': '2010-08-22',
            'date_of_admission': '2023-04-01',
            'parent_name': 'Mr. Suresh Sharma',
            'parent_phone': '9876543213',
            'parent_email': 'suresh.sharma@example.com',
            'address': '456 Park Avenue, City',
            'theme_preference': 'blue'
        },
        {
            'student_id': 'STU003',
            'password': 'password123',
            'full_name': 'Arjun Patel',
            'first_name': 'Arjun',
            'last_name': 'Patel',
            'email': 'arjun.patel@example.com',
            'phone': '9876543214',
            'class': '10th',
            'section': 'B',
            'roll_number': '01',
            'gender': 'Male',
            'date_of_birth': '2010-03-10',
            'date_of_admission': '2023-04-01',
            'parent_name': 'Mr. Mahesh Patel',
            'parent_phone': '9876543215',
            'parent_email': 'mahesh.patel@example.com',
            'address': '789 Oak Road, City',
            'theme_preference': 'dark'
        },
        {
            'student_id': 'STU004',
            'password': 'password123',
            'full_name': 'Sneha Reddy',
            'first_name': 'Sneha',
            'last_name': 'Reddy',
            'email': 'sneha.reddy@example.com',
            'phone': '9876543216',
            'class': '10th',
            'section': 'B',
            'roll_number': '02',
            'gender': 'Female',
            'date_of_birth': '2010-11-30',
            'date_of_admission': '2023-04-01',
            'parent_name': 'Mr. Ramesh Reddy',
            'parent_phone': '9876543217',
            'parent_email': 'ramesh.reddy@example.com',
            'address': '321 Elm Street, City',
            'theme_preference': 'green'
        },
        {
            'student_id': 'STU005',
            'password': 'password123',
            'full_name': 'Vikram Singh',
            'first_name': 'Vikram',
            'last_name': 'Singh',
            'email': 'vikram.singh@example.com',
            'phone': '9876543218',
            'class': '9th',
            'section': 'A',
            'roll_number': '01',
            'gender': 'Male',
            'date_of_birth': '2011-01-20',
            'date_of_admission': '2023-04-01',
            'parent_name': 'Mr. Harpreet Singh',
            'parent_phone': '9876543219',
            'parent_email': 'harpreet.singh@example.com',
            'address': '555 Maple Drive, City',
            'theme_preference': 'light'
        }
    ]
    
    added_count = 0
    
    for student in sample_students:
        try:
            # Check if student already exists
            cursor.execute(
                "SELECT id FROM students WHERE school_id = ? AND student_id = ?",
                (school_id, student['student_id'])
            )
            
            if cursor.fetchone():
                print(f"⚠ Student {student['student_id']} already exists, skipping...")
                continue
            
            # Hash password
            password_hash = generate_password_hash(student['password'])
            
            # Insert student
            cursor.execute('''
                INSERT INTO students (
                    school_id, student_id, password, full_name, first_name, last_name,
                    email, phone, class, section, roll_number, gender,
                    date_of_birth, date_of_admission, parent_name, parent_phone,
                    parent_email, address, theme_preference
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                school_id, student['student_id'], password_hash, student['full_name'],
                student['first_name'], student['last_name'], student['email'],
                student['phone'], student['class'], student['section'],
                student['roll_number'], student['gender'], student['date_of_birth'],
                student['date_of_admission'], student['parent_name'],
                student['parent_phone'], student['parent_email'],
                student['address'], student['theme_preference']
            ))
            
            print(f"✓ Added student: {student['full_name']} ({student['student_id']})")
            added_count += 1
            
        except Exception as e:
            print(f"❌ Error adding student {student['student_id']}: {e}")
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"✅ Successfully added {added_count} student(s)")
    print(f"{'='*60}")
    
    if added_count > 0:
        print("\n📋 Student Login Credentials:")
        print("-" * 60)
        for student in sample_students[:added_count]:
            print(f"Student ID: {student['student_id']}")
            print(f"Name: {student['full_name']}")
            print(f"Password: password123")
            print(f"Class: {student['class']}-{student['section']}")
            print("-" * 60)
        
        print("\n🌐 Access Student Portal:")
        print(f"URL: http://localhost:5500/student/login")
        print(f"School: {school_name}")
        print("\n💡 Use any of the above credentials to login")

if __name__ == '__main__':
    print("="*60)
    print("Adding Sample Students to Database")
    print("="*60)
    print()
    
    add_sample_students()
