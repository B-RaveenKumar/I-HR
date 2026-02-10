import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app


def run_test():
    results = []
    with app.test_client() as client:
        # Simulate admin session
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['user_type'] = 'admin'
            sess['school_id'] = 1
        for fmt in ['excel', 'csv']:
            url = f"/generate_admin_report?report_type=daily_attendance&date=2024-09-15&format={fmt}&department="
            resp = client.get(url)
            results.append({
                'format': fmt,
                'status_code': resp.status_code,
                'content_type': resp.headers.get('Content-Type'),
                'disposition': resp.headers.get('Content-Disposition'),
                'length': len(resp.data)
            })
    return results


if __name__ == '__main__':
    for r in run_test():
        print(f"Format={r['format']} status={r['status_code']} type={r['content_type']} len={r['length']}")
        print(f"Disposition: {r['disposition']}")
        print('-'*80)

