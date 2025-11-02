# CRM Celery Setup

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt

2. Install and run Redis
# On Linux/macOS
redis-server

# On Windows, use WSL or download Redis for Windows

3. Apply migrations
python manage.py migrate

4. Start Django server
python manage.py runserver

5. Start Celery worker
celery -A crm worker -l info

6. Start Celery Beat
celery -A crm beat -l info

7. Verify logs
cat /tmp/crm_report_log.txt

Notes

The task generate_crm_report runs every Monday at 6:00 AM.

Ensure the GraphQL endpoint is accessible at http://localhost:8000/graphql.