import json, datetime

class ConfigManager:
	def __init__(self):
		self.config = None
		self.read_config()

	def set_message_bus(self, message_bus):
		self.message_bus = message_bus
		message_bus.listen("config_manager", "get", self.get)
		message_bus.listen("config_manager", "get_task_config", self.get_task_config)
		message_bus.listen("config_manager", "set", self.set)
		message_bus.listen("config_manager", "write", self.write_config)

	def read_config(self, filename="vconfig.json"):
		config = json.load(open(filename, "r"))
		self.config = config

	def write_config(self, filename="vconfig.json"):
		json.dump(self.config, open(filename, "w"), indent=4)
		if self.message_bus:
			self.message_bus.request("config_manager", "logger", "debug", f"Config written to {filename} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
		else:
			print(f"Config written to {filename} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")

	def get(self, key):
		value = self.config.get(key)
		if self.message_bus:
			self.message_bus.request("config_manager", "logger", "debug", f"Config get: {key} = {value}")
		else:
			print(f"Config get: {key} = {value}")
		return value

	def get_task_config(self, task_name):
		if self.message_bus:
			self.message_bus.request("config_manager", "logger", "debug", f"Config get task: {task_name}")
		task_config = self.config["tasks"].get(task_name)
		if self.message_bus:
			self.message_bus.request("config_manager", "logger", "debug", f"Config found task: {task_name} = {task_config}")
		else:
			print(f"Config found task: {task_name} = {task_config}")
		return task_config

	def set(self, data):
		key = data.get("key")
		value = data.get("value")
		self.config[key] = value
		if self.message_bus:
			self.message_bus.request("config_manager", "logger", "debug", f"Config updated: {key} = {value}")
		else:
			print(f"Config updated: {key} = {value}")
		self.write_config()
		return self.config[key]