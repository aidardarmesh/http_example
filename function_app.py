import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.function_name(name="HttpTrigger")
@app.route(route="http_trigger")
@app.generic_output_binding(
    arg_name="signalr_message", 
    type="signalR", 
    hub_name="agentsHub")
def http_trigger(
    req: func.HttpRequest,
    signalr_message: func.Out[str]
) -> func.HttpResponse:
    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = None
        if req_body:
            name = req_body.get('name')

    if name:
        message = {
            "target": "newMessage",  # the client method to invoke
            "arguments": [name]      # the data sent to clients
        }
        signalr_message.set(message)
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully and sent a message to SignalR clients.")
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
        )

@app.function_name(name="Negotiate")
@app.route(route="negotiate", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
@app.generic_input_binding(
    arg_name="connectionInfo", 
    type="signalRConnectionInfo", 
    hubName="agentsHub", 
    connectionStringSetting="AzureSignalRConnectionString")
def negotiate(req: func.HttpRequest, connectionInfo) -> func.HttpResponse:
    return func.HttpResponse(connectionInfo)