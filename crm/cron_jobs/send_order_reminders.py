#!/usr/bin/env python3
"""
send_order_reminders.py
This script queries pending orders (from the past 7 days)
via GraphQL and logs reminders to /tmp/order_reminders_log.txt
"""

import datetime
import logging
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure logging
LOG_FILE = "/tmp/order_reminders_log.txt"
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format="%(asctime)s - %(message)s")


def main():
    # GraphQL endpoint
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=False,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Calculate the date range for the last 7 days
    today = datetime.date.today()
    last_week = today - datetime.timedelta(days=7)

    # GraphQL query
    query = gql("""
    query GetRecentOrders($lastWeek: Date!, $today: Date!) {
        orders(filter: { order_date_Gte: $lastWeek, order_date_Lte: $today }) {
            id
            customer {
                email
            }
        }
    }
    """)

    variables = {"lastWeek": str(last_week), "today": str(today)}

    try:
        response = client.execute(query, variable_values=variables)
        orders = response.get("orders", [])

        if not orders:
            logging.info("No recent orders found.")
        else:
            for order in orders:
                order_id = order.get("id")
                customer_email = order.get("customer", {}).get("email")
                logging.info(
                    f"Reminder sent for Order ID {order_id} - Customer Email: {customer_email}")

        print("Order reminders processed!")

    except Exception as e:
        logging.error(f"Error processing order reminders: {e}")
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
