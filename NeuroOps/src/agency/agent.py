from .mqtt_client import MQTTClient

class AutonomousAgent:
    def __init__(self):
        self.mqtt = MQTTClient()
        self.tools = {
            "trigger_alarm": self.trigger_alarm,
            "lockdown_facility": self.lockdown,
            "notify_security": self.notify_security
        }

    def execute_action(self, action_name, params=None):
        if action_name in self.tools:
            print(f"[AGENT] Executing tool: {action_name}")
            return self.tools[action_name](params)
        else:
            print(f"[AGENT] Unknown tool: {action_name}")
            return False

    def trigger_alarm(self, params):
        zone = params.get("zone", "all")
        self.mqtt.publish("facility/alarm", {"status": "ON", "zone": zone})
        return f"Alarm triggered for zone {zone}"

    def lockdown(self, params):
        reason = params.get("reason", "security_breach")
        self.mqtt.publish("facility/locks", {"command": "LOCK_ALL", "reason": reason})
        return "Facility Lockdown Process Initiated"

    def notify_security(self, params):
        msg = params.get("message", "Check feed")
        self.mqtt.publish("security/alerts", {"priority": "HIGH", "msg": msg})
        return "Security Notified"
