import pytest
import sys
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import customtkinter as ctk

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import source module directly (for coverage measurement)
import todo_app
from todo_app import Task, TaskWidget, TodoApp

def test_add_task_with_valid_title():
    app = TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = "Test Task"
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    app.add_task()
    
    assert len(app.tasks) == 1
    assert app.tasks[0].title == "Test Task"
    assert app.tasks[0].completed is False
    app.task_entry.delete.assert_called_once_with(0, "end")
    app.save_tasks.assert_called_once()
    app.refresh_task_list.assert_called_once()

def test_add_task_with_empty_string():
    app = TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = ""
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    app.add_task()
    
    assert len(app.tasks) == 0
    app.save_tasks.assert_not_called()
    app.refresh_task_list.assert_not_called()

def test_add_task_with_whitespace_only():
    app = TodoApp()
    app.task_entry = MagicMock()
    app.task_entry.get.return_value = "   "
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    app.add_task()
    
    assert len(app.tasks) == 0
    app.save_tasks.assert_not_called()
    app.refresh_task_list.assert_not_called()

def test_add_task_with_very_long_title():
    app = TodoApp()
    app.task_entry = MagicMock()
    long_title = "A" * 500
    app.task_entry.get.return_value = long_title
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    app.add_task()
    
    assert len(app.tasks) == 1
    assert app.tasks[0].title == long_title

def test_toggle_task_completion():
    task = Task("Test Task", completed=False)
    app = TodoApp()
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.update_stats = MagicMock()
    
    app.toggle_task()
    
    assert task.completed is True
    app.save_tasks.assert_called_once()
    app.update_stats.assert_called_once()

def test_delete_task():
    task = Task("Test Task")
    app = TodoApp()
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    app.delete_task(task)
    
    assert len(app.tasks) == 0
    app.save_tasks.assert_called_once()
    app.refresh_task_list.assert_called_once()

def test_edit_task_with_valid_title():
    task = Task("Old Title")
    app = TodoApp()
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog:
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = "New Title"
        mock_dialog.return_value = mock_instance
        app.edit_task(task)
        
        assert task.title == "New Title"

def test_task_init():
    task = Task("Test Task")
    assert task.title == "Test Task"
    assert task.completed is False
    assert task.created_at is not None

def test_task_to_dict():
    task = Task("Test Task")
    task_dict = task.to_dict()
    assert task_dict["title"] == "Test Task"
    assert task_dict["completed"] == False
    assert task_dict["created_at"] is not None

def test_task_from_dict():
    task_data = {
        "title": "Test Task",
        "completed": True,
        "created_at": datetime.now().isoformat()
    }
    task = Task.from_dict(task_data)
    assert task.title == "Test Task"
    assert task.completed is True
    assert task.created_at == task_data["created_at"]

def test_todo_app_init():
    app = TodoApp()
    assert app.tasks == []
    assert app.filter_mode == "all"

def test_todo_app_load_tasks():
    app = TodoApp()
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('builtins.open', new=MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value = mock_file
            mock_file.read.return_value = json.dumps({
                "tasks": [
                    {"title": "Test Task", "completed": True, "created_at": datetime.now().isoformat()}
                ],
                "theme": "dark"
            })
            app.load_tasks()
            assert len(app.tasks) == 1
            assert app.tasks[0].title == "Test Task"
            assert app.tasks[0].completed is True

def test_todo_app_save_tasks():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    with patch('builtins.open', new=MagicMock()) as mock_open:
        mock_file = MagicMock()
        mock_open.return_value = mock_file
        app.save_tasks()
        mock_file.write.assert_called_once()

def test_todo_app_update_stats():
    app = TodoApp()
    app.tasks = [Task("Test Task", completed=True), Task("Test Task 2")]
    app.update_stats()
    assert app.stats_label.cget("text") == "2 tasks • 1 active • 1 completed"

def test_todo_app_refresh_task_list():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    with patch.object(app, 'get_filtered_tasks') as mock_get_filtered_tasks:
        mock_get_filtered_tasks.return_value = app.tasks
        app.refresh_task_list()
        assert len(app.scrollable_frame.winfo_children()) == 1

def test_todo_app_get_filtered_tasks():
    app = TodoApp()
    app.tasks = [Task("Test Task", completed=True), Task("Test Task 2")]
    app.filter_mode = "active"
    filtered_tasks = app.get_filtered_tasks()
    assert len(filtered_tasks) == 1
    assert filtered_tasks[0].title == "Test Task 2"

def test_task_widget_init():
    task = Task("Test Task")
    with patch.object(ctk.CTkFrame, '__init__') as mock_init:
        TaskWidget(None, task, None, None, None)
        mock_init.assert_called_once()

def test_customtkinter_import():
    try:
        import customtkinter as ctk
    except ImportError:
        pytest.fail("customtkinter import failed")

def test_load_tasks_with_invalid_json():
    app = TodoApp()
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = True
        with patch('builtins.open', new=MagicMock()) as mock_open:
            mock_file = MagicMock()
            mock_open.return_value = mock_file
            mock_file.read.return_value = "Invalid JSON"
            app.load_tasks()
            assert len(app.tasks) == 0

def test_load_tasks_with_missing_file():
    app = TodoApp()
    with patch('os.path.exists') as mock_exists:
        mock_exists.return_value = False
        app.load_tasks()
        assert len(app.tasks) == 0

def test_save_tasks_with_permission_error():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    with patch('builtins.open', new=MagicMock(side_effect=PermissionError())):
        with pytest.raises(PermissionError):
            app.save_tasks()

def test_task_title_validation():
    with pytest.raises(TypeError):
        Task(123)

def test_task_title_sanitization():
    task = Task("Test Task   ")
    assert task.title == "Test Task   "

def test_edit_task_with_empty_title():
    task = Task("Old Title")
    app = TodoApp()
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog:
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = ""
        mock_dialog.return_value = mock_instance
        app.edit_task(task)
        
        assert task.title == "Old Title"

def test_edit_task_with_whitespace_only_title():
    task = Task("Old Title")
    app = TodoApp()
    app.tasks = [task]
    app.save_tasks = MagicMock()
    app.refresh_task_list = MagicMock()
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog:
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = "   "
        mock_dialog.return_value = mock_instance
        app.edit_task(task)
        
        assert task.title == "Old Title"