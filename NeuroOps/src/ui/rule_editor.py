import json
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
                             QLineEdit, QTextEdit, QPushButton, QLabel, QFrame, QMessageBox, QComboBox)
from PyQt6.QtCore import Qt

class RuleEditorWidget(QWidget):
    def __init__(self, rules_path=None, parent=None):
        super().__init__(parent)
        if rules_path is None:
            # Resolve relative to this file: src/ui/rule_editor.py -> NeuroOps/configs/rules.json
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.rules_path = os.path.join(base_dir, "configs", "rules.json")
        else:
            self.rules_path = rules_path
            
        self.rules_data = {"rules": []}
        self.setup_ui()
        self.load_rules()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        
        # Left: Rule List
        left_panel = QFrame()
        left_layout = QVBoxLayout(left_panel)
        left_layout.addWidget(QLabel("DEFINED RULES"))
        
        self.rule_list = QListWidget()
        self.rule_list.currentRowChanged.connect(self.display_rule)
        left_layout.addWidget(self.rule_list)
        
        btn_add = QPushButton("+ NEW RULE")
        btn_add.clicked.connect(self.add_new_rule)
        left_layout.addWidget(btn_add)
        
        layout.addWidget(left_panel, stretch=1)
        
        # Right: Editor
        self.editor_panel = QFrame()
        self.editor_panel.setEnabled(False)
        r_layout = QVBoxLayout(self.editor_panel)
        
        r_layout.addWidget(QLabel("Rule Name:"))
        self.input_name = QLineEdit()
        r_layout.addWidget(self.input_name)
        
        r_layout.addWidget(QLabel("Condition (Python Expr using 'input'):"))
        self.input_condition = QTextEdit()
        self.input_condition.setPlaceholderText("e.g. input.confidence > 0.8")
        self.input_condition.setFixedHeight(60)
        r_layout.addWidget(self.input_condition)
        
        r_layout.addWidget(QLabel("Actions:"))
        self.input_actions = QTextEdit()
        self.input_actions.setPlaceholderText("JSON List of actions...")
        r_layout.addWidget(self.input_actions)
        
        btn_save = QPushButton("SAVE CHANGES")
        btn_save.clicked.connect(self.save_rule_changes)
        r_layout.addWidget(btn_save)
        
        btn_delete = QPushButton("DELETE RULE")
        btn_delete.setStyleSheet("color: #ff5555; border-color: #ff5555;")
        btn_delete.clicked.connect(self.delete_rule)
        r_layout.addWidget(btn_delete)
        
        r_layout.addStretch()
        
        layout.addWidget(self.editor_panel, stretch=2)

    def load_rules(self):
        if os.path.exists(self.rules_path):
            with open(self.rules_path, 'r') as f:
                try:
                    self.rules_data = json.load(f)
                except:
                    self.rules_data = {"rules": []}
        
        self.rule_list.clear()
        for rule in self.rules_data.get("rules", []):
            self.rule_list.addItem(rule.get("name", "Unnamed Rule"))

    def display_rule(self, index):
        if index < 0:
            self.editor_panel.setEnabled(False)
            return
            
        self.editor_panel.setEnabled(True)
        rule = self.rules_data["rules"][index]
        self.input_name.setText(rule.get("name", ""))
        self.input_condition.setText(rule.get("condition", ""))
        self.input_actions.setText(json.dumps(rule.get("actions", []), indent=2))

    def save_rule_changes(self):
        idx = self.rule_list.currentRow()
        if idx < 0: return
        
        try:
            actions = json.loads(self.input_actions.toPlainText())
        except:
            QMessageBox.warning(self, "Error", "Invalid JSON in actions")
            return
            
        rule = {
            "name": self.input_name.text(),
            "condition": self.input_condition.toPlainText(),
            "actions": actions
        }
        
        self.rules_data["rules"][idx] = rule
        self.save_to_file()
        self.rule_list.item(idx).setText(rule["name"])
        QMessageBox.information(self, "Saved", "Rule updated successfully.")

    def add_new_rule(self):
        new_rule = {
            "name": "New Rule",
            "condition": "input.confidence > 0.5",
            "actions": [{"type": "alert", "message": "New Alert", "severity": "info"}]
        }
        self.rules_data["rules"].append(new_rule)
        self.save_to_file()
        self.rule_list.addItem(new_rule["name"])
        self.rule_list.setCurrentRow(len(self.rules_data["rules"]) - 1)

    def delete_rule(self):
        idx = self.rule_list.currentRow()
        if idx < 0: return
        
        del self.rules_data["rules"][idx]
        self.save_to_file()
        self.dummy_reload_list()

    def dummy_reload_list(self):
        self.rule_list.clear()
        for rule in self.rules_data.get("rules", []):
            self.rule_list.addItem(rule.get("name", "Unnamed Rule"))

    def save_to_file(self):
        with open(self.rules_path, 'w') as f:
            json.dump(self.rules_data, f, indent=2)
