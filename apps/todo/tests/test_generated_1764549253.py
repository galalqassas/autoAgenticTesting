import sys
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

import pytest

# ---------- Mock customtkinter ----------
class _DummyWidget:
    def __init__(self, *args, **kwargs):
        self._config = {}
        self._children = []

    def grid(self, *args, **kwargs):
        pass

    def configure(self, **kwargs):
        self._config.update(kwargs)

    def bind(self, *args, **kwargs):
        pass

    def destroy(self):
        pass

    def winfo_children(self):
        return self._children

    def grid_columnconfigure(self, *args, **kwargs):
        pass

class CTk(_DummyWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_text = ""
        self.geometry_text = ""
        self._protocols = {}

    def title(self, text):
        self.title_text = text

    def geometry(self, text):
        self.geometry_text = text

    def minsize(self, w, h):
        pass

    def protocol(self, name, func):
        self._protocols[name] = func

    def mainloop(self):
        pass

    def destroy(self):
        pass

class CTkFrame(_DummyWidget):
    pass

class CTkLabel(_DummyWidget):
    def __init__(self, master=None, text="", **kwargs):
        super().__init__(master, **kwargs)
        self.text = text

class CTkButton(_DummyWidget):
    def __init__(self, master=None, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command

class CTkCheckBox(_DummyWidget):
    def __init__(self, master=None, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command
        self._selected = False

    def select(self):
        self._selected = True

    def deselect(self):
        self._selected = False

class CTkEntry(_DummyWidget):
    def __init__(self, master=None, placeholder_text="", **kwargs):
        super().__init__(master, **kwargs)
        self._value = ""
        self.placeholder = placeholder_text

    def get(self):
        return self._value

    def delete(self, start, end):
        self._value = ""

    def insert(self, index, text):
        self._value = text

    def bind(self, event, func):
        pass

class CTkSwitch(_DummyWidget):
    def __init__(self, master=None, command=None, **kwargs):
        super().__init__(master, **kwargs)
        self.command = command

class CTkScrollableFrame(_DummyWidget):
    pass

class CTkFont:
    def __init__(self, size=10, **kwargs):
        self.size = size

def set_appearance_mode(mode):
    set_appearance_mode.current = mode

def get_appearance_mode():
    return getattr(set_appearance_mode, "current", "dark")

def set_default_color_theme(theme):
    pass

class CTkInputDialog:
    # Simple mock dialog; test will patch get_input
    def __init__(self, text="", title=""):
        self._entry = MagicMock()
        self._entry.insert = MagicMock()

    def get_input(self):
        return None

# Insert mock module into sys.modules before importing todo_app
mock_ctk = MagicMock()
mock_ctk.CTk = CTk
mock_ctk.CTkFrame = CTkFrame
mock_ctk.CTkLabel = CTkLabel
mock_ctk.CTkButton = CTkButton
mock_ctk.CTkCheckBox = CTkCheckBox
mock_ctk.CTkEntry = CTkEntry
mock_ctk.CTkSwitch = CTkSwitch
mock_ctk.CTkScrollableFrame = CTkScrollableFrame
mock_ctk.CTkFont = CTkFont
mock_ctk.set_appearance_mode = set_appearance_mode
mock_ctk.get_appearance_mode = get_appearance_mode
mock_ctk.set_default_color_theme = set_default_color_theme
mock_ctk.CTkInputDialog = CTkInputDialog

sys.modules["customtkinter"] = mock_ctk

# Now import the source module
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
import todo_app

# ---------- Fixtures ----------
@pytest.fixture
def app(tmp_path):
    """Create a TodoApp instance with a temporary data file."""
    # Ensure a fresh data file path
    data_file = tmp_path / "tasks.json"
    with patch.object(todo_app.TodoApp, "data_file", str(data_file)):
        # Patch save_tasks to avoid actual file I/O unless explicitly tested
        with patch.object(todo_app.TodoApp, "save_tasks", MagicMock()) as mock_save:
            instance = todo_app.TodoApp()
            yield instance
            # Cleanup
            instance.destroy()

# ---------- Helper ----------
def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

# ---------- Tests ----------
def test_add_valid_task(app):
    app.task_entry.insert(0, "Buy milk")
    app.add_task()
    assert len(app.tasks) == 1
    assert app.tasks[0].title == "Buy milk"
    # Entry should be cleared
    assert app.task_entry.get() == ""
    # Stats label should reflect one task
    assert "1 task" in app.stats_label._config.get("text", "")

def test_add_empty_task_is_ignored(app):
    app.task_entry.insert(0, "   ")
    app.add_task()
    assert len(app.tasks) == 0
    # No change to stats
    assert "0 tasks" in app.stats_label._config.get("text", "")

def test_toggle_task_completion_updates_state_and_stats(app):
    # Add a task first
    app.task_entry.insert(0, "Read book")
    app.add_task()
    task = app.tasks[0]
    assert not task.completed

    # Simulate toggle via the widget's callback
    # The widget is created during refresh; retrieve it
    widget = app.scrollable_frame.winfo_children()[0]
    widget._toggle_task()  # flips completed and calls app.toggle_task()
    assert task.completed
    # Stats should now show 0 active, 1 completed
    stats = app.stats_label._config.get("text", "")
    assert "0 active" in stats and "1 completed" in stats

def test_delete_task_removes_it(app):
    app.task_entry.insert(0, "Task to delete")
    app.add_task()
    assert len(app.tasks) == 1
    task = app.tasks[0]

    # Retrieve widget and invoke delete
    widget = app.scrollable_frame.winfo_children()[0]
    widget._delete_task()
    assert len(app.tasks) == 0
    # Stats should reflect no tasks
    assert "No tasks" in app.stats_label._config.get("text", "")

def test_edit_task_with_valid_title(app):
    app.task_entry.insert(0, "Old title")
    app.add_task()
    task = app.tasks[0]

    # Patch the input dialog to return a new title
    with patch.object(todo_app, "ctk"):
        with patch.object(todo_app.ctk, "CTkInputDialog") as mock_dialog_cls:
            mock_dialog = MagicMock()
            mock_dialog.get_input.return_value = "New title"
            mock_dialog_cls.return_value = mock_dialog

            app.edit_task(task)

    assert task.title == "New title"
    # Verify stats unchanged but UI refreshed (widget text updated)
    widget = app.scrollable_frame.winfo_children()[0]
    assert widget.label.text == "New title"

def test_edit_task_with_empty_title_keeps_original(app):
    app.task_entry.insert(0, "Stay same")
    app.add_task()
    task = app.tasks[0]

    with patch.object(todo_app, "ctk"):
        with patch.object(todo_app.ctk, "CTkInputDialog") as mock_dialog_cls:
            mock_dialog = MagicMock()
            mock_dialog.get_input.return_value = "   "  # whitespace only
            mock_dialog_cls.return_value = mock_dialog

            app.edit_task(task)

    assert task.title == "Stay same"
    widget = app.scrollable_frame.winfo_children()[0]
    assert widget.label.text == "Stay same"

def test_theme_toggle_switches_appearance_and_emoji(app):
    # Initial mode is dark per set_appearance_mode default
    assert todo_app.ctk.get_appearance_mode() == "dark"
    app.toggle_theme()
    assert todo_app.ctk.get_appearance_mode() == "light"
    assert app.theme_switch._config.get("text") == "☀️"
    # Toggle back
    app.toggle_theme()
    assert todo_app.ctk.get_appearance_mode() == "dark"
    assert app.theme_switch._config.get("text") == "🌙"

def test_load_tasks_missing_file_starts_empty(app):
    # Ensure the data file does not exist
    with patch("os.path.exists", return_value=False):
        app.load_tasks()
    assert app.tasks == []
    assert "No tasks" in app.stats_label._config.get("text", "")

def test_load_tasks_malformed_json_results_in_empty_list(app):
    malformed = "{ this is not json"
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=malformed)), \
         patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
        app.load_tasks()
    assert app.tasks == []
    assert "No tasks" in app.stats_label._config.get("text", "")

def test_clear_completed_removes_only_completed(app):
    # Add two tasks, one completed
    app.task_entry.insert(0, "Active task")
    app.add_task()
    app.task_entry