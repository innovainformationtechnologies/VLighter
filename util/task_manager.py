from util.tasks import AppTask, ScriptTask
from util.daily_config import DailyConfig
from util.message_bus import MessageBus
from util.logger import Logger
import schedule, os
import time
import threading

class TaskManager:
	def __init__(self, config, message_bus=None):
		self.config = config
		# print("Initializing Task Manager with config:", config)
		self.message_bus = message_bus
		self.tasks = []
		# self.build_task_list(config)
		self.message_bus.request("task_manager", "logger", "debug", f"Task Manager initialized with {self.tasks}.")
		self.message_bus.listen("task_manager", "run_all_tasks", self.run_all_tasks)
		self.message_bus.listen("task_manager", "stop_all_tasks", self.stop_all_tasks)
		self.message_bus.listen("task_manager", "add_task", self.add_task)
		self.message_bus.listen("task_manager", "add_task_data", self.add_task_data)
		self.message_bus.listen("task_manager", "run_task", self.run_task)
		self.message_bus.listen("task_manager", "stop_task", self.stop_task)
		self.message_bus.listen("task_manager", "get_tasks", self.get_tasks)
		self.message_bus.listen("task_manager", "get_running_tasks", self.get_running_tasks)
		

	# ----------------------------
	# TASK LIST
	# Add, remove, or reorder tasks here as needed.
	# Each task runs in sequence with a short delay between them.
	# ----------------------------

	def build_task_list(self,config):
		task_list = []
		segment_data = self.message_bus.request("task_manager", "segment_manager", "get_current_segment_data")
		if segment_data:
			task_list = segment_data["task_list"]
		self.message_bus.request("task_manager", "logger", "debug", f"Daily Tasks: {task_list}")
		task_data = config["tasks"]
		for task_name in task_list: #config["tasks"]:
			task_cfg = task_data[task_name]
			print("task config: ", task_cfg)
			self.add_task(task_cfg)
		return task_list

	def get_tasks(self, key=None):
		self.message_bus.request("task_manager", "logger", "debug", f"Tasks: {self.tasks}")
		return [task.name for task in self.tasks]

	def get_running_tasks(self, key=None):
		running_tasks = [task for task in self.tasks if task.running]
		self.message_bus.request("task_manager", "logger", "debug", f"Tasks: {running_tasks}")
		return [task.name for task in running_tasks]

	def add_task(self, task_name):
		self.message_bus.request("task_manager", "logger", "debug", f"Adding Task: {task_name}")
		task_config = self.message_bus.request("task_manager", "config_manager", "get_task_config", task_name)
		match task_config["type"]:
			case "AppTask":
				self.message_bus.request("task_manager", "logger", "debug", f"Adding AppTask: {task_config['name']} with path {task_config['path']}")
				task = AppTask(name=task_config["name"], config=task_config, path=task_config["path"])
			case "ScriptTask":
				self.message_bus.request("task_manager", "logger", "debug", f"Adding ScriptTask: {task_config['name']} with path {task_config['path']}")
				task = ScriptTask(name=task_config["name"], config=task_config, path=os.path.join(os.getcwd(), "scripts", task_config["path"]))
		self.tasks.append(task)

	def add_task_data(self, task_name, task_data):
		task_config = task_data
		if self.message_bus:
			task_config = self.message_bus.request("task_manager", "logger", "debug", f"Adding Task: {task_name} with data: {task_config}")
		match task_config["type"]:
			case "AppTask":
				self.message_bus.request("task_manager", "logger", "debug", f"Adding AppTask: {task_config['name']} with path {task_config['path']}")
				task = AppTask(name=task_config["name"], config=task_config, path=task_config["path"])
			case "ScriptTask":
				self.message_bus.request("task_manager", "logger", "debug", f"Adding ScriptTask: {task_config['name']} with path {task_config['path']}")
				task = ScriptTask(name=task_config["name"], config=task_config, path=os.path.join(os.getcwd(), "scripts", task_config["path"]))
		self.tasks.append(task)

	def run_all_tasks(self, kwargs={}):
		for task in self.tasks:
			if task.config.get("skip"):
				self.message_bus.request("task_manager","logger", "info", f"Skipping {task.name} (skip=True in config)")
				continue
			task.run(message_bus=self.message_bus)

			try:
				self.message_bus.request("task_manager","logger", "info", f"Waiting {task.config['delay']} seconds before next task...")
				time.sleep(task.config["delay"])
			except KeyError:
				self.message_bus.request("task_manager","logger", "info", "Waiting 2 seconds before next task...")
				time.sleep(2)

			if task.config.get("halt"):
				input(f"{task.name} has halt=True. Press Enter to continue with next tasks...")

		self.message_bus.request("task_manager","logger", "info", "All tasks started.")

	def stop_all_tasks(self, kwargs={}):
		for task in self.tasks:
			task.stop(message_bus=self.message_bus)

	def run_task(self, task_name):
		self.message_bus.request("task_manager", "logger", "debug", f"Attempting to run task: {task_name}")
		for task in self.tasks:
			print(task)
			self.message_bus.request("task_manager", "logger", "debug", f"Checking task: {task}")
			if task.name.lower() == task_name.lower():
				task.run(message_bus=self.message_bus)
				self.message_bus.request("task_manager", "logger", "info", f"Running Task: {task_name}")
				return
		self.message_bus.request("task_manager", "logger", "error", f"Task {task_name} not found.")
		return

	def stop_task(self, task_name):
		for task in self.tasks:
			if task.name == task_name:
				task.stop(message_bus=self.message_bus)
				self.message_bus.request("task_manager", "logger", "info", f"Stopped Task: {task_name}")
				return 
		self.message_bus.request("task_manager", "logger", "error", f"Task {task_name} not found.")