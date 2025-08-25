import azure.functions as func
import logging


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.function_name(name="CosmosDBTrigger")
@app.cosmos_db_trigger_v3(
    arg_name="documents",
    database_name="my-database",
    collection_name="my-container",
    connection_string_setting="CosmosDBConnectionString",
    lease_collection_name="leases",
    create_lease_collection_if_not_exists=True)
@app.generic_output_binding(
    arg_name="signalr_message", 
    type="signalR", 
    hub_name="agentsHub")
def cosmosdb_trigger(
    documents: func.DocumentList,
    signalr_message: func.Out[str]
) -> func.HttpResponse:
    if documents:
        logging.info(f"{len(documents)} document changes detected.")
        message = {
            "target": "newMessage",
            "arguments": [doc.to_dict() for doc in documents]
        }
        signalr_message.set(message)
    else:
        logging.info("No document changes detected.")


@app.function_name(name="Negotiate")
@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
@app.generic_input_binding(
    arg_name="connectionInfo", 
    type="signalRConnectionInfo", 
    hubName="agentsHub", 
    connectionStringSetting="AzureSignalRConnectionString")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    return func.HttpResponse(connectionInfo)