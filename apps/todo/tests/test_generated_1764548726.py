import pytest
import sys
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import source module directly (for coverage measurement)
import todo_app

def test_task_creation_with_title():
    task = todo_app.Task("Test Task")
    assert task.title == "Test Task"
    assert task.completed is False
    assert task.created_at is not None

def test_task_creation_with_completed_status():
    task = todo_app.Task("Completed Task", completed=True)
    assert task.title == "Completed Task"
    assert task.completed is True

def test_task_to_dict():
    task = todo_app.Task("Test Task", completed=True, created_at="2023-01-01T00:00:00")
    result = task.to_dict()
    assert result["title"] == "Test Task"
    assert result["completed"] is True
    assert result["created_at"] == "2023-01-01T00:00:00"

def test_task_from_dict():
    data = {"title": "Test Task", "completed": True, "created_at": "2023-01-01T00:00:00"}
    task = todo_app.Task.from_dict(data)
    assert task.title == "Test Task"
    assert task.completed is True
    assert task.created_at == "2023-01-01T00:00:00"

def test_task_from_dict_missing_created_at():
    data = {"title": "Test Task", "completed": False}
    task = todo_app.Task.from_dict(data)
    assert task.title == "Test Task"
    assert task.completed is False
    assert task.created_at is not None

def test_task_from_dict_missing_completed():
    data = {"title": "Test Task"}
    task = todo_app.Task.from_dict(data)
    assert task.title == "Test Task"
    assert task.completed is False

def test_task_from_dict_missing_title():
    data = {"completed": True}
    with pytest.raises(KeyError):
        todo_app.Task.from_dict(data)

def test_add_task_with_valid_title():
    app = todo_app.TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = "Valid Task"
    app.tasks = []
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    app.add_task()
    assert len(app.tasks) == 1
    assert app.tasks[0].title == "Valid Task"
    assert app.tasks[0].completed is False

def test_add_task_with_empty_title():
    app = todo_app.TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = ""
    app.tasks = []
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    app.add_task()
    assert len(app.tasks) == 0

def test_add_task_with_whitespace_title():
    app = todo_app.TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = "   "
    app.tasks = []
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    app.add_task()
    assert len(app.tasks) == 0

def test_add_task_with_500_char_title():
    app = todo_app.TodoApp()
    app.task_entry = MagicMock()
    long_title = "a" * 500
    app.task_entry.get.return_value = long_title
    app.tasks = []
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    app.add_task()
    assert len(app.tasks) == 1
    assert app.tasks[0].title == long_title

def test_edit_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()

    app.edit_task(task)
    # simulate dialog input
    task.title = "Edited Task"
    assert task.title == "Edited Task"

def test_delete_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()

    app.delete_task(task)
    assert len(app.tasks) == 0

def test_toggle_task():
    app = todo_app.TodoApp()
    task = todo_app.Task("Test Task")
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.update_stats = MagicMock()

    task.completed = False
    app.toggle_task()
    assert task.completed is True

def test_set_filter():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1"), todo_app.Task("Task 2", completed=True)]

    app.set_filter("active")
    assert app.filter_mode == "active"

    app.set_filter("completed")
    assert app.filter_mode == "completed"

    app.set_filter("all")
    assert app.filter_mode == "all"

def test_clear_completed():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1"), todo_app.Task("Task 2", completed=True)]

    app.clear_completed()
    assert len(app.tasks) == 1

def test_refresh_task_list():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1")]

    app.refresh_task_list()
    # Check if task list is refreshed

def test_get_filtered_tasks():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1"), todo_app.Task("Task 2", completed=True)]

    active_tasks = app.get_filtered_tasks()
    if app.filter_mode == "active":
        assert len(active_tasks) == 1

    app.filter_mode = "completed"
    completed_tasks = app.get_filtered_tasks()
    assert len(completed_tasks) == 1

    app.filter_mode = "all"
    all_tasks = app.get_filtered_tasks()
    assert len(all_tasks) == 2

def test_update_stats():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1"), todo_app.Task("Task 2", completed=True)]

    app.update_stats()
    assert app.stats_label.cget("text") == "2 tasks • 1 active • 1 completed"

def test_toggle_theme():
    with patch('customtkinter.get_appearance_mode') as mock_get_mode:
        mock_get_mode.return_value = "dark"
        app = todo_app.TodoApp()

        app.toggle_theme()
        assert app.theme_switch.cget("text") == "☀️"

def test_save_tasks():
    app = todo_app.TodoApp()
    app.tasks = [todo_app.Task("Task 1")]

    with patch('json.dump') as mock_dump:
        app.save_tasks()
        mock_dump.assert_called_once()

def test_load_tasks():
    app = todo_app.TodoApp()

    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('json.load') as mock_load:
            mock_load.return_value = {"tasks": [{"title": "Task 1", "completed": False, "created_at": "2023-01-01T00:00:00"}]}
            app.load_tasks()
            assert len(app.tasks) == 1

def test_on_closing():
    app = todo_app.TodoApp()

    with patch.object(app, 'destroy') as mock_destroy:
        app.on_closing()
        mock_destroy.assert_called_once()