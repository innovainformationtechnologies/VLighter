import flask
from flask import send_from_directory, request
import flask_cors
import mimetypes
import threading

class MessageBus:
	def __init__(self, config):
		self.listeners = {}
		self.config = config
		self.app = None
		threading.Thread(target=self.setup_endpoint).start()
		print("[MessageBus] Initialized message bus")
	
	# create flask endpoint for message bus to receive messages from UI or other external sources
	def setup_endpoint(self):
		self.app = flask.Flask(__name__)
		flask_cors.CORS(self.app, resources={r"/*": {"origins": "*"}})
		self.app.config["CORS_HEADERS"] = "Content-Type"

		@self.app.route("/message_bus", methods=["POST", "OPTIONS"])
		def handle_message():
			if request.method == "OPTIONS":
				return "", 204
			try:
				data = request.get_json()
				listener = data.get("listener")
				event = data.get("event")
				payload = data.get("data")
				return self.request("HTTP", listener, event, payload)
			except Exception as e:
				print(f"\033[91m[MessageBus] Error handling message: {e}")
				return "", 500
		self.app.run(host="0.0.0.0", port=5500)

	def listen(self, listener_name, event_name, callback):
		if self.config.get("debug") == True:
			print(f"\033[96m[MessageBus] Registering listener '{listener_name}' for event '{event_name}'")
		#check if listener_name already exists, if not create it.
		if listener_name not in self.listeners:
			self.listeners[listener_name] = {}
		
		#check if event_name already exists under listener, if not create it
		if event_name not in self.listeners[listener_name]:
			self.listeners[listener_name][event_name] = None

		#add callback to event
		self.listeners[listener_name][event_name] = callback
	
	def request(self, requester, listener_name, event_name, data=None):
		if self.config.get("debug") == True:
			print(f"\033[96m[MessageBus] Requester [{requester}] requesting event '{event_name}' from listener '{listener_name}'")
		if listener_name not in self.listeners:
			return 
		if listener_name in self.listeners and event_name in self.listeners[listener_name]:
			callback = self.listeners[listener_name][event_name]
			if callback:
				if self.config.get("debug"):
					print(f"\033[96m[MessageBus] [{requester}] Calling callback for event '{event_name}' from listener '{listener_name}'")
				return callback(data)