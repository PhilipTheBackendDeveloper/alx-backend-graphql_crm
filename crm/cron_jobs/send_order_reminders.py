#!/usr/bin/env python3
import os
import sys
import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Define constants
GRAPHQL_ENDPOINT = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"

def main():
    # Define time window (orders within last 7 days)
    now = datetime.datetime.now()
    seven_days_ago = now - datetime.timedelta(days=7)

    # Prepare GraphQL query
    query = gql("""
        query GetRecentOrders($startDate: DateTime!) {
            orders(orderDate_Gte: $startDate) {
                id
                customer {
                    email
                }
            }
        }
    """)

    # Configure GraphQL client
    transport = RequestsHTTPTransport(url=GRAPHQL_ENDPOINT, verify=False)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    try:
        # Execute query
        variables = {"startDate": seven_days_ago.isoformat()}
        response = client.execute(query, variable_values=variables)

        # Write results to log
        with open(LOG_FILE, "a") as f:
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            orders = response.get("orders", [])
            for order in orders:
                order_id = order["id"]
                email = order["customer"]["email"]
                f.write(f"{timestamp} - Order ID: {order_id}, Customer: {email}\n")

        print("Order reminders processed!")

    except Exception as e:
        with open(LOG_FILE, "a") as f:
            timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"{timestamp} - Error: {str(e)}\n")
        print(f"Error processing reminders: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
