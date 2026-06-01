import os
import time
import requests
import schedule
import threading
import subprocess
import json
from util.tasks import AppTask, ScriptTask
from util.message_bus import MessageBus
from util.pass_man import PassMan
from util.daily_config import DailyConfig
from util.seg_manager import SegmentManager
from util.sched_manager import ScheduleManager
from util.logger import Logger
from util.task_manager import TaskManager
from util.config_manager import ConfigManager

# ----------------------------
# PATHS
# ----------------------------



# ----------------------------
# MAIN
# ----------------------------

def main():
	# get config
	# config = read_config()

	#initialize utils
	cm = ConfigManager()
	message_bus = MessageBus(cm.config)
	cm.set_message_bus(message_bus)

	# logger
	cwd = os.getcwd()
	log_path = os.path.join(cwd, "static", "logs", f"{time.strftime('%Y-%m-%d')}_log.txt")
	logger = Logger(log_file=log_path, bus=message_bus, debug=cm.get("debug"))
	pass_man = PassMan(config=cm.config, bus=message_bus)
	# sched manager
	sched_manager = ScheduleManager(message_bus)
	# seg manager
	seg_manager = SegmentManager(message_bus)
	# daily_config = DailyConfig(cm.config, message_bus)
	task_manager = TaskManager(cm.config, message_bus)
	
	# run tasks
	if cm.get("follow_schedule") == True:
		task_manager.build_task_list(cm.config)
		task_manager.run_all_tasks()
		message_bus.request("Main", "logger", "success", "All tasks started.")
	else: 
		message_bus.request("Main", "logger", "info", "Autostart is disabled.")
		initial_segment = cm.get("initial_segment")
		message_bus.request("Main", "logger", "info", f"Initial segment: {initial_segment}")
		if initial_segment != None:
			seg_manager.run(cm.get("initial_segment"))
			message_bus.request("Main", "logger", "success", "All tasks started.")
		else:
			message_bus.request("Main", "logger", "warning", "Autostart is disabled and no initial segment set. No tasks started.")
			message_bus.request("Main", "logger", "info", "Please set an initial segment to run tasks.")
    

	input("Press Enter to exit...")


if __name__ == "__main__":
    main()
