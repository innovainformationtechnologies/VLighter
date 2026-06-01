import json
import datetime

class ScheduleManager:
	def __init__(self, message_bus=None):
		self.message_bus = message_bus
		self.config = None
		self.weekly_schedule = self._get_weekly_schedule()
		message_bus.request("schedule_manager", "logger", "info", f"[ScheduleManager] Weekly Schedule: {self.weekly_schedule}")
		message_bus.listen("schedule_manager", "get_for_day", self.get_for_day)
		message_bus.listen("schedule_manager", "set_for_day", self.set_for_day)
		message_bus.listen("schedule_manager", "get_weekly_schedule", self.get_weekly_schedule)


	def _get_weekly_schedule(self):
		config = self.message_bus.request("schedule_manager", "config_manager", "get", "weekly_schedule")
		return config

	def get_for_day(self, day):
		todays_schedule = self.weekly_schedule.get(day, {})
		self.message_bus.request("scehedule_manager", "logger", "debug", f"[ScheduleManager] Todays Schedule: {todays_schedule}")
		return todays_schedule

	def set_for_day(self, day, segments):
		self.weekly_schedule[day] = segments
	
	def get_weekly_schedule(self, key=None):
		res = self.weekly_schedule or self._get_weekly_schedule()
		self.message_bus.request("scehedule_manager", "logger", "debug", f"[ScheduleManager] Weekly Schedule: {res}")
		return res
		