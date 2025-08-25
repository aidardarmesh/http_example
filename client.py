import json
import requests
import logging
import time
import sys
from signalrcore.hub_connection_builder import HubConnectionBuilder
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SignalRClient")

# Azure Function App host (your local or deployed function app)
FUNCTION_APP_URL = "https://func-adnocgpt.azurewebsites.net:443"  # Update with your Function App URL

# These will be populated after negotiation
SIGNALR_SERVICE_URL = None
HUB_NAME = "agentsHub"


def on_message(message):
    """Callback for when a message is received from the SignalR hub"""
    logger.info(f"Received message: {message}")


def on_error(error):
    """Callback for when an error occurs"""
    logger.error(f"Error: {error}")


def on_connection_open():
    """Callback for when the connection is opened"""
    logger.info("Connection opened")


def on_connection_close():
    """Callback for when the connection is closed"""
    logger.info("Connection closed")


def negotiate_with_server():
    """Perform the negotiation step with the Azure Function App to get SignalR connection details"""
    negotiate_url = f"{FUNCTION_APP_URL}/api"
    
    try:
        logger.info(f"Negotiating with Function App at: {negotiate_url}")
        response = requests.get(f"{negotiate_url}/negotiate", headers={
            "Content-Type": "application/json"
        })
        
        if response.status_code == 200:
            connection_info = response.json()
            logger.info("Negotiation successful. Connection info received.")
            logger.debug(f"Connection details: {json.dumps(connection_info, indent=2)}")
            
            # Extract connection details needed for SignalR connection
            signalr_url = connection_info.get("url")
            access_token = connection_info.get("accessToken")
            
            if signalr_url and access_token:
                # Parse the URL to get the base URL for SignalR service
                parsed_url = urlparse(signalr_url)
                global SIGNALR_SERVICE_URL
                SIGNALR_SERVICE_URL = f"wss://{parsed_url.netloc}"
                
                logger.info(f"SignalR service URL: {SIGNALR_SERVICE_URL}")
                logger.info(f"Access token received (length: {len(access_token)})")
                
                return {
                    "url": negotiate_url,
                    "accessToken": access_token
                }
            else:
                logger.error("Missing URL or access token in connection info")
                return None
        else:
            logger.error(f"Negotiation failed. Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as ex:
        logger.error(f"Exception during negotiation: {ex}")
        return None


if __name__ == "__main__":
    logger.info("Starting SignalR client...")
    
    # First negotiate with the Function App to get SignalR connection details
    connection_info = negotiate_with_server()
    if not connection_info:
        logger.error("Failed to get connection info from Function App. Exiting.")
        sys.exit(1)
        
    signalr_url = connection_info.get("url")
    access_token = connection_info.get("accessToken")
    
    # Build a connection to the SignalR hub
    try:
        logger.info("Building hub connection...")
        builder = HubConnectionBuilder()
        hub_connection = builder.with_url(
            signalr_url, 
            options={
                "verify_ssl": False,
                "skip_negotiation": True,
                "headers": {
                    "Authorization": f"Bearer {access_token}"
                }
            }
        ).configure_logging(logging.DEBUG, socket_trace=True
        ).with_automatic_reconnect({
            "type": "raw", 
            "keep_alive_interval": 10, 
            "reconnect_interval": 5, 
            "max_attempts": 5
        }).build()
        
        # Register callbacks
        hub_connection.on("newMessage", on_message)
        hub_connection.on_open(on_connection_open)
        hub_connection.on_close(on_connection_close)
        hub_connection.on_error(on_error)
        
        # Start the connection
        logger.info("Starting connection...")
        hub_connection.start()
        logger.info(f"Connection established to {SIGNALR_SERVICE_URL}")
        
        # Keep the connection alive until interrupted
        while True:
            # Just wait and listen for incoming messages
            # The on_message callback will handle any incoming messages
            
            try:
                # Sleep to prevent high CPU usage, but still keep the connection alive
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Received keyboard interrupt. Shutting down...")
                break
            
    except Exception as ex:
        logger.error(f"Exception: {ex}", exc_info=True)
    finally:
        # Stop the connection when done
        try:
            if 'hub_connection' in locals():
                logger.info("Stopping connection...")
                hub_connection.stop()
                logger.info("Connection stopped")
        except Exception as ex:
            logger.error(f"Error stopping connection: {ex}", exc_info=True)
