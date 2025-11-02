import requests 
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime

GRAPHQL_ENDPOINT = 'http://localhost:8000/graphql'

@shared_task
def generate_crm_report():
    transport = RequestsHTTPTransport(
        url=GRAPHQL_ENDPOINT,
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query = gql("""
    query {
        allCustomers {
            totalCount
        }
        allOrders {
            totalCount
            edges {
                node {
                    totalAmount
                }
            }
        }
    }
    """)

    result = client.execute(query)
    total_customers = result['allCustomers']['totalCount']
    total_orders = result['allOrders']['totalCount']
    total_revenue = sum(
        edge['node']['totalAmount'] for edge in result['allOrders']['edges']
    )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"{timestamp} - Report: {total_customers} customers, {total_orders} orders, {total_revenue} revenue\n"

    with open("/tmp/crm_report_log.txt", "a") as f:
        f.write(log_line)

    return log_line
