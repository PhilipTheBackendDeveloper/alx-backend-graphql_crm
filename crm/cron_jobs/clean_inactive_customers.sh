#!/bin/bash

# Log file (use Windows-friendly /c/ path)
LOG_FILE="/c/tmp/customer_cleanup_log.txt"

# Navigate to project root (2 levels up from crm/cron_jobs)
cd "$(dirname "$0")/../.."

# Run Django cleanup command using your Python path
deleted_count=$("C:/Users/Eric Hackman/AppData/Local/Programs/Python/Python313/python.exe" manage.py shell -c '
from datetime import datetime, timedelta
from crm.models import Customer
cutoff = datetime.now() - timedelta(days=365)
deleted, _ = Customer.objects.filter(last_order_date__lt=cutoff).delete()
print(deleted)
')

# Log timestamp and deleted count
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted $deleted_count inactive customers" >> "$LOG_FILE"
