#!/bin/bash

# Navigate to project directory
cd "$(dirname "$0")/../.."

# Run Django shell command to delete inactive customers
deleted_count=$(python3 manage.py shell <<EOF
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

cutoff_date = timezone.now() - timedelta(days=365)
deleted, _ = Customer.objects.filter(last_order_date__lt=cutoff_date).delete()
print(deleted)
EOF
)

# Log result with timestamp
echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted $deleted_count inactive customers" >> /tmp/customer_cleanup_log.txt
