import os, json
import subprocess
import threading


# ----------------------------
# BASE TASK
# ----------------------------

class Task:
	"""Base class for all startup tasks."""
	def __init__(self, name, config={}):
		self.name = name
		self.config = config
		self.running = False

	def run(self, message_bus=None):
		raise NotImplementedError(f"Task '{self.name}' must implement run()")

	def stop(self, message_bus=None):
		raise NotImplementedError(f"Task '{self.name}' must implement stop()")

	def __repr__(self):
		return f"<{self.__class__.__name__}: {self.name}>"


# ----------------------------
# APP TASK
# Launches an application via a path or shortcut (.lnk)
# ----------------------------

class AppTask(Task):
	def __init__(self, name, path,config={}):
		super().__init__(name, config)
		self.path = path

	def run(self, message_bus=None):
		if not message_bus:
			print(f"  [ERROR] No message bus provided for {self.name}")
			return {"error": "No message bus provided"}
		print(f"Launching {self.name}...")
		if not os.path.exists(self.path):
			message_bus.request(self.name, "logger", "error", f"Path not found: {self.path}")
			return
		try:
			os.startfile(self.path)
			message_bus.request(self.name, "logger", "log", f"{self.name} launched.")
			print(f"  [OK] {self.name} launched.")
		except Exception as e:
			message_bus.request(self.name, "logger", "error", f"Failed to launch {self.name}: {e}")
			print(f"  [ERROR] Failed to launch {self.name}: {e}")


# ----------------------------
# SCRIPT TASK
# Runs another Python script as a subprocess
# ----------------------------

class ScriptTask(Task):
	def __init__(self, name, path, config={}):
		super().__init__(name, config)
		self.config = config
		self.path = path
		self.process = None
		self.running = False

	def run(self, message_bus):
		# config arg -> listener:event:data
		# example: {"listener": "PassMan", "event": "get_password", "data": "network_pass"}
		if not message_bus:
			print(f"  [ERROR] No message bus provided for {self.name}")
			return {"error": "No message bus provided"}
		args = []
		for arg in self.config["args"]:
			res = message_bus.request(self.name, arg["listener"], arg["event"], arg["data"])
			if res is not None:
				if isinstance(res, str):
					args.append(res)
					continue
				if isinstance(res, dict):
					args.append(json.dumps(res))
					continue
				else:
					args.append(str(res))
					continue
		# print(args)
		message_bus.request(self.name, "logger", "log", f"Running script: {self.name}...")
		if not os.path.exists(self.path):
			print(f"  [ERROR] Script not found: {self.path}")
			return
		try:
			self.process = subprocess.Popen(["python", self.path] + (args))
			self.running = True
			message_bus.request(self.name, "logger", "log", f"{self.name} started.")
			
		except Exception as e:
			message_bus.request(self.name, "logger", "error", f"Failed to run {self.name}: {e}")

	def stop(self, message_bus=None):
		if not message_bus:
			print(f"  [ERROR] No message bus provided for {self.name}")
			return {"error": "No message bus provided"}
		if hasattr(self, 'process') and self.process.poll() is None:
			self.process.terminate()
			message_bus.request(self.name, "logger", "log", f"{self.name} stopped.")
			self.running = False
		else:
			message_bus.request(self.name, "logger", "error", f"{self.name} is not running.")
