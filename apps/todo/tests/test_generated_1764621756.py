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

def test_task_init():
    task = todo_app.Task("Test Task")
    assert task.title == "Test Task"
    assert task.completed == False
    assert task.created_at is not None

def test_task_to_dict():
    task = todo_app.Task("Test Task")
    data = task.to_dict()
    assert data["title"] == "Test Task"
    assert data["completed"] == False
    assert data["created_at"] is not None

def test_task_from_dict():
    task_data = {
        "title": "Test Task",
        "completed": True,
        "created_at": datetime.now().isoformat(),
    }
    task = todo_app.Task.from_dict(task_data)
    assert task.title == task_data["title"]
    assert task.completed == task_data["completed"]
    assert task.created_at == task_data["created_at"]

def test_todo_app_init():
    app = todo_app.TodoApp()
    assert app.tasks == []
    assert app.filter_mode == "all"

def test_add_task():
    app = todo_app.TodoApp()
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        app.task_entry = MagicMock()
        app.task_entry.get.return_value = "Test Task"
        app.add_task()
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "Test Task"
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()

def test_edit_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Original Title")
    app.tasks.append(task)
    with patch('customtkinter.CTkInputDialog') as mock_dialog, \
         patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = "New Title"
        mock_dialog.return_value = mock_instance
        app.edit_task(task)
        assert task.title == "New Title"
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()

def test_delete_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        app.delete_task(task)
        assert len(app.tasks) == 0
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()

def test_toggle_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    with patch.object(app, 'save_tasks') as mock_save:
        app.toggle_task()
        mock_save.assert_called_once()

def test_set_filter():
    app = todo_app.TodoApp()
    app.set_filter("active")
    assert app.filter_mode == "active"

def test_clear_completed():
    app = todo_app.TodoApp()
    task1 = todo_app.Task("Task 1")
    task2 = todo_app.Task("Task 2", completed=True)
    app.tasks.extend([task1, task2])
    app.clear_completed()
    assert len(app.tasks) == 1
    assert app.tasks[0].title == "Task 1"

def test_refresh_task_list():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    with patch.object(app, 'get_filtered_tasks') as mock_get_filtered_tasks:
        mock_get_filtered_tasks.return_value = [task]
        app.refresh_task_list()
        # Check if task list is refreshed

def test_get_filtered_tasks():
    app = todo_app.TodoApp()
    task1 = todo_app.Task("Task 1")
    task2 = todo_app.Task("Task 2", completed=True)
    app.tasks.extend([task1, task2])
    assert len(app.get_filtered_tasks()) == 2
    app.set_filter("active")
    assert len(app.get_filtered_tasks()) == 1
    assert app.get_filtered_tasks()[0].title == "Task 1"

def test_update_stats():
    app = todo_app.TodoApp()
    task1 = todo_app.Task("Task 1")
    task2 = todo_app.Task("Task 2", completed=True)
    app.tasks.extend([task1, task2])
    app.update_stats()
    assert "2 tasks • 1 active • 1 completed" in app.stats_label.cget("text")

def test_toggle_theme():
    app = todo_app.TodoApp()
    current_mode = ctk.get_appearance_mode()
    app.toggle_theme()
    assert ctk.get_appearance_mode() != current_mode

def test_save_tasks():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    with patch('json.dump') as mock_dump:
        app.save_tasks()
        mock_dump.assert_called_once()

def test_load_tasks():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks.append(task)
    app.save_tasks()
    new_app = todo_app.TodoApp()
    assert len(new_app.tasks) == 1

def test_task_widget_init():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    with patch.object(ctk.CTkFrame, '__init__') as mock_init:
        todo_app.TaskWidget(app, task, lambda: None, lambda: None, lambda: None)
        mock_init.assert_called_once()

def test_task_widget_update_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    widget = todo_app.TaskWidget(app, task, lambda: None, lambda: None, lambda: None)
    new_task = todo_app.Task("New Task")
    widget.update_task(new_task)
    assert widget.task.title == "New Task"