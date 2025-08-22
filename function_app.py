import os
import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="HttpTrigger")
@app.route(route="http_trigger")
@app.cosmos_db_output(
    arg_name="outputDocument", 
    database_name="my-database", 
    container_name="my-container", 
    connection="CosmosDB")
def http_trigger(
    req: func.HttpRequest,
    outputDocument: func.Out[func.Document]
) -> func.HttpResponse:
    import os  
    logging.info(f"CosmosDB string: {os.getenv('CosmosDB')}")
    logging.info('Python HTTP trigger function processed a request.')
    logging.info('Python Cosmos DB trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            name = req_body.get('name')

    if name:
        outputDocument.set(func.Document.from_dict({"id": name}))
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )