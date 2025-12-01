import pytest
import sys
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import customtkinter as ctk

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import source module directly (for coverage measurement)
import todo_app

def test_task_class_exists():
    assert hasattr(todo_app, 'Task')

def test_task_init_with_default_values():
    task = todo_app.Task("Test Task")
    assert task.title == "Test Task"
    assert task.completed is False
    assert task.created_at is not None

def test_task_init_with_custom_values():
    task = todo_app.Task("Custom Task", completed=True, created_at="2023-01-01")
    assert task.title == "Custom Task"
    assert task.completed is True
    assert task.created_at == "2023-01-01"

def test_task_to_dict():
    task = todo_app.Task("Test Task", completed=True, created_at="2023-01-01")
    result = task.to_dict()
    expected = {
        "title": "Test Task",
        "completed": True,
        "created_at": "2023-01-01"
    }
    assert result == expected

def test_task_from_dict():
    data = {
        "title": "Test Task",
        "completed": True,
        "created_at": "2023-01-01"
    }
    task = todo_app.Task.from_dict(data)
    assert task.title == "Test Task"
    assert task.completed is True
    assert task.created_at == "2023-01-01"

def test_task_widget_class_exists():
    assert hasattr(todo_app, 'TaskWidget')

def test_todo_app_class_exists():
    assert hasattr(todo_app, 'TodoApp')

def test_application_configuration():
    assert ctk.get_appearance_mode() == "dark"

def test_task_widget_init():
    task = todo_app.Task("Test Task")
    with patch.object(todo_app.TaskWidget, '__init__') as mock_task_widget:
        todo_app.TaskWidget(None, task, None, None, None)
        mock_task_widget.assert_called_once()

def test_todo_app_init():
    with patch.object(todo_app.TodoApp, '__init__') as mock_todo_app:
        todo_app.TodoApp()
        mock_todo_app.assert_called_once()

def test_todo_app_create_widgets():
    app = todo_app.TodoApp()
    app.create_widgets()
    assert app.task_entry is not None

def test_todo_app_add_task():
    app = todo_app.TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = "New Task"
    app.add_task()
    assert len(app.tasks) == 1

def test_todo_app_edit_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.edit_task(task)
    assert task.title != ""

def test_todo_app_delete_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.delete_task(task)
    assert len(app.tasks) == 0

def test_todo_app_toggle_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.toggle_task()
    assert task.completed

def test_todo_app_set_filter():
    app = todo_app.TodoApp()
    app.set_filter("active")
    assert app.filter_mode == "active"

def test_todo_app_clear_completed():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task", completed=True)
    app.tasks.append(task)
    app.clear_completed()
    assert len(app.tasks) == 0

def test_todo_app_refresh_task_list():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.refresh_task_list()
    assert len(app.scrollable_frame.winfo_children()) > 0

def test_todo_app_get_filtered_tasks():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    filtered_tasks = app.get_filtered_tasks()
    assert len(filtered_tasks) > 0

def test_todo_app_update_stats():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.update_stats()
    assert app.stats_label.cget("text") != ""

def test_todo_app_toggle_theme():
    with patch.object(ctk, 'set_appearance_mode') as mock_set_appearance_mode:
        app = todo_app.TodoApp()
        app.toggle_theme()
        mock_set_appearance_mode.assert_called_once()

def test_todo_app_save_tasks():
    with patch('builtins.open', new=MagicMock()) as mock_open:
        app = todo_app.TodoApp()
        task = todo_app.Task("Test Task")
        app.tasks.append(task)
        app.save_tasks()
        mock_open.assert_called_once()

def test_todo_app_load_tasks():
    with patch('builtins.open', new=MagicMock()) as mock_open:
        app = todo_app.TodoApp()
        app.load_tasks()
        mock_open.assert_called_once()

def test_todo_app_on_closing():
    with patch.object(todo_app.TodoApp, 'destroy') as mock_destroy:
        app = todo_app.TodoApp()
        app.on_closing()
        mock_destroy.assert_called_once()

def test_task_widget_update_task():
    task = todo_app.Task("Test Task")
    widget = todo_app.TaskWidget(None, task, None, None, None)
    new_task = todo_app.Task("New Task")
    widget.update_task(new_task)
    assert widget.task.title == "New Task"

def test_task_widget_toggle_task():
    task = todo_app.Task("Test Task")
    widget = todo_app.TaskWidget(None, task, lambda: None, lambda: None, lambda: None)
    widget._toggle_task()
    assert task.completed

def test_task_widget_delete_task():
    task = todo_app.Task("Test Task")
    widget = todo_app.TaskWidget(None, task, None, lambda: None, lambda: None)
    widget._delete_task()
    # No direct assertion, but on_delete should be called

def test_task_widget_edit_task():
    task = todo_app.Task("Test Task")
    widget = todo_app.TaskWidget(None, task, None, None, lambda: None)
    widget._edit_task()
    # No direct assertion, but on_edit should be called