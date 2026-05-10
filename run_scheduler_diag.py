import os
import pymysql
import re
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import json

DATABASE_URL = os.getenv('DATABASE_URL', 'mysql+pymysql://root:Vish0803@mysql-env-94i0cda6di.ap-south-1a.lb.nimbuz.tech:32261/ihrdb')

def _parse_mysql_url(url):
    url = re.sub(r'^mysql\+pymysql://', '', url)
    m = re.match(r'(?P<user>[^:]+):(?P<password>[^@]*)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<db>.+)', url)
    return {'user':m.group('user'),'password':m.group('password'),'host':m.group('host'),'port':int(m.group('port') or 3306),'database':m.group('db'),'charset':'utf8mb4','autocommit':True}

def get_db():
    params = _parse_mysql_url(DATABASE_URL)
    conn = pymysql.connect(**params)
    return conn

def run_once():
    print(f"[{datetime.datetime.now()}] Manual Scheduler Start")
    conn = get_db()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    
    now = datetime.datetime.now()
    cur.execute('''
        SELECT * FROM scheduled_reports 
        WHERE active = 1 
        AND (last_run IS NULL OR DATE(last_run) < CURDATE())
        AND (hour < %s OR (hour = %s AND minute <= %s))
    ''', (now.hour, now.hour, now.minute))
    schedules = cur.fetchall()
    
    print(f"Found {len(schedules)} schedules to process.")
    
    for s in schedules:
        print(f"Processing ID {s['id']} ({s['report_type']}) for {s['email']}")
        # For testing, we'll skip the actual report generation and just try sending a test email
        # to verify SMTP works.
        
        school_id = s['school_id']
        cur.execute("SELECT setting_value FROM system_settings WHERE setting_key = 'company_otp_provider_config'")
        res = cur.fetchone()
        if not res:
            print("  ✗ Error: SMTP config missing")
            continue
            
        config = json.loads(res['setting_value'])
        smtp_host = config.get('smtp_host')
        smtp_port = int(config.get('smtp_port', 587))
        smtp_from = config.get('smtp_from_email')
        smtp_user = config.get('smtp_username') or smtp_from
        smtp_pass = config.get('smtp_password')
        
        print(f"  Connecting to {smtp_host}:{smtp_port}...")
        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                if config.get('smtp_use_tls', True):
                    server.starttls()
            
            print(f"  Logging in as {smtp_user}...")
            server.login(smtp_user, smtp_pass)
            
            msg = MIMEMultipart()
            msg['From'] = smtp_from
            msg['To'] = s['email']
            msg['Subject'] = "Diagnostic: Scheduled Report Test"
            msg.attach(MIMEText("This is a diagnostic email from the scheduled report system.", 'plain'))
            
            print(f"  Sending test mail...")
            server.sendmail(smtp_from, [s['email']], msg.as_string())
            server.quit()
            
            print("  ✓ Success! Updating last_run.")
            cur.execute("UPDATE scheduled_reports SET last_run = %s WHERE id = %s", (now, s['id']))
            conn.commit()
        except Exception as e:
            print(f"  ✗ FAILED: {e}")

    conn.close()

if __name__ == "__main__":
    run_once()
