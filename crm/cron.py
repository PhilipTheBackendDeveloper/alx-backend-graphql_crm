from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime

def log_crm_heartbeat():
    """Logs CRM heartbeat and optionally checks GraphQL responsiveness."""
    now = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_message = f"{now} CRM is alive\n"

    # Append heartbeat to file
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(log_message)

    # Optional: Query GraphQL 'hello' field to verify endpoint
    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )

    client = Client(transport=transport, fetch_schema_from_transport=False)

    try:
        query = gql("{ hello }")
        response = client.execute(query)
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{now} GraphQL response: {response}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{now} GraphQL query failed: {e}\n")

def update_low_stock():
    """Runs every 12 hours to restock low-stock products via GraphQL mutation."""
    now = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_file = "/tmp/low_stock_updates_log.txt"

    transport = RequestsHTTPTransport(
        url="http://localhost:8000/graphql",
        verify=True,
        retries=3,
    )
    client = Client(transport=transport, fetch_schema_from_transport=False)

    mutation = gql("""
        mutation {
            updateLowStockProducts {
                updatedProducts {
                    name
                    stock
                }
                message
            }
        }
    """)

    try:
        response = client.execute(mutation)
        updated = response.get("updateLowStockProducts", {}).get("updatedProducts", [])
        message = response.get("updateLowStockProducts", {}).get("message", "")

        with open(log_file, "a") as f:
            f.write(f"{now} - {message}\n")
            for product in updated:
                f.write(f"{now} - Product: {product['name']}, Stock: {product['stock']}\n")

    except Exception as e:
        with open(log_file, "a") as f:
            f.write(f"{now} - Error executing mutation: {e}\n")