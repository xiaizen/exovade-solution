import json
import os
import zen
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class RulesWatcher(FileSystemEventHandler):
    def __init__(self, filepath, callback):
        self.filepath = os.path.abspath(filepath)
        self.callback = callback
    
    def on_modified(self, event):
        if os.path.abspath(event.src_path) == self.filepath:
            print(f"[DECISION CORE] Rules modified: {self.filepath}")
            self.callback()

class DecisionCore:
    def __init__(self, rules_path=None):
        if rules_path is None:
             # Resolve relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.rules_path = os.path.join(base_dir, "configs", "rules.json")
        else:
            self.rules_path = rules_path
            
        self.engine = zen.ZenEngine()
        self.rules = {}
        self._load_rules()
        
        # Start Watcher
        self._start_watcher()

    def _start_watcher(self):
        try:
            self.observer = Observer()
            folder = os.path.dirname(self.rules_path)
            handler = RulesWatcher(self.rules_path, self._load_rules)
            self.observer.schedule(handler, folder, recursive=False)
            self.observer.start()
        except Exception as e:
            print(f"[DECISION CORE] Watcher failed: {e}")

    def _load_rules(self):
        # Zen Engine expects JDM. Mapping our simple JSON to Zen if needed, 
        # or using our simple eval for prototype if Zen JDM structure is complex.
        # For this prototype, we stick to our loading logic but now it's hot-swappable.
        
        # Wait a brief moment for file write to complete
        time.sleep(0.1)
        
        if os.path.exists(self.rules_path):
            try:
                with open(self.rules_path, 'r') as f:
                    self.rules = json.load(f)
                print("[DECISION CORE] Rules loaded successfully.")
            except Exception as e:
                 print(f"[DECISION CORE] Error loading rules: {e}")
                 self.rules = {"rules": []}
        else:
            self.rules = {"rules": []}

    def evaluate(self, context):
        """
        Evaluating rules against context.
        """
        # For prototype simplicity we use our Python eval loop.
        # Ideally this delegates to self.engine.evaluate(jdm, context)
        
        triggered_actions = []
        for rule in self.rules.get("rules", []):
            try:
                allowed_names = {"input": context}
                condition = rule.get("condition", "False")
                if eval(condition, {"__builtins__": {}}, allowed_names):
                    triggered_actions.extend(rule.get("actions", []))
            except Exception as e:
                # print(f"Rule Evaluation Error: {e}")
                pass
                
        return triggered_actions
    
    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
