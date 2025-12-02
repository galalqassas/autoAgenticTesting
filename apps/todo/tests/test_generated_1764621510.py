import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime
import json
import customtkinter as ctk

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import source module directly (for coverage measurement)
import todo_app
from todo_app import Task, TodoApp, TaskWidget

def test_task_creation_with_valid_title():
    task = Task("Test Task")
    assert task.title == "Test Task"
    assert task.completed is False
    assert task.created_at is not None

def test_task_creation_with_custom_created_at():
    task = Task("Test Task", created_at="2023-01-01T00:00:00")
    assert task.created_at == "2023-01-01T00:00:00"

def test_task_to_dict():
    task = Task("Test Task", completed=True, created_at="2023-01-01T00:00:00")
    result = task.to_dict()
    assert result["title"] == "Test Task"
    assert result["completed"] is True
    assert result["created_at"] == "2023-01-01T00:00:00"

def test_task_from_dict():
    data = {"title": "Test Task", "completed": True, "created_at": "2023-01-01T00:00:00"}
    task = Task.from_dict(data)
    assert task.title == "Test Task"
    assert task.completed is True
    assert task.created_at == "2023-01-01T00:00:00"

def test_task_from_dict_missing_created_at():
    data = {"title": "Test Task", "completed": False}
    task = Task.from_dict(data)
    assert task.created_at is not None  # default value

def test_task_from_dict_missing_title():
    data = {"completed": False, "created_at": "2023-01-01T00:00:00"}
    with pytest.raises(KeyError):
        Task.from_dict(data)

def test_add_task_with_valid_title_button():
    with patch.object(TodoApp, 'task_entry', new_callable=MagicMock) as mock_task_entry:
        mock_task_entry.get.return_value = "New Task"
        mock_task_entry.delete.return_value = None
        app = TodoApp()
        app.tasks = []
        app.save_tasks = MagicMock()
        app.refresh_task_list = MagicMock()
        
        app.add_task()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "New Task"
        mock_task_entry.delete.assert_called_once_with(0, "end")
        app.save_tasks.assert_called_once()
        app.refresh_task_list.assert_called_once()

def test_add_task_with_empty_title():
    with patch.object(TodoApp, 'task_entry', new_callable=MagicMock) as mock_task_entry:
        mock_task_entry.get.return_value = ""
        app = TodoApp()
        app.tasks = []
        app.save_tasks = MagicMock()
        app.refresh_task_list = MagicMock()
        
        app.add_task()
        
        assert len(app.tasks) == 0
        app.save_tasks.assert_not_called()
        app.refresh_task_list.assert_not_called()

def test_save_tasks():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    app.data_file = "test_tasks.json"
    
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.write = MagicMock()
        
        app.save_tasks()
        
        mock_open.assert_called_once_with("test_tasks.json", "w")
        mock_file.write.assert_called_once()

def test_load_tasks():
    app = TodoApp()
    app.data_file = "test_tasks.json"
    
    with patch('builtins.open', new_callable=MagicMock) as mock_open:
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = '{"tasks": [{"title": "Test Task", "completed": false, "created_at": "2023-01-01T00:00:00"}], "theme": "dark"}'
        
        app.load_tasks()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "Test Task"

def test_toggle_theme():
    app = TodoApp()
    
    with patch('customtkinter.get_appearance_mode', return_value="dark"):
        with patch('customtkinter.set_appearance_mode') as mock_set_appearance_mode:
            app.toggle_theme()
            mock_set_appearance_mode.assert_called_once_with("light")

def test_update_stats():
    app = TodoApp()
    app.tasks = [Task("Test Task", completed=True), Task("Test Task 2")]
    
    app.update_stats()
    
    assert app.stats_label.cget("text") == "2 tasks • 1 active • 1 completed"

def test_refresh_task_list():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    
    with patch.object(app, 'get_filtered_tasks', return_value=[app.tasks[0]]):
        with patch.object(TaskWidget, '__init__') as mock_task_widget:
            app.refresh_task_list()
            mock_task_widget.assert_called_once()

def test_get_filtered_tasks_all():
    app = TodoApp()
    app.tasks = [Task("Test Task"), Task("Test Task 2", completed=True)]
    app.filter_mode = "all"
    
    filtered_tasks = app.get_filtered_tasks()
    
    assert len(filtered_tasks) == 2

def test_get_filtered_tasks_active():
    app = TodoApp()
    app.tasks = [Task("Test Task"), Task("Test Task 2", completed=True)]
    app.filter_mode = "active"
    
    filtered_tasks = app.get_filtered_tasks()
    
    assert len(filtered_tasks) == 1

def test_get_filtered_tasks_completed():
    app = TodoApp()
    app.tasks = [Task("Test Task"), Task("Test Task 2", completed=True)]
    app.filter_mode = "completed"
    
    filtered_tasks = app.get_filtered_tasks()
    
    assert len(filtered_tasks) == 1

def test_clear_completed():
    app = TodoApp()
    app.tasks = [Task("Test Task"), Task("Test Task 2", completed=True)]
    
    app.clear_completed()
    
    assert len(app.tasks) == 1

def test_edit_task():
    app = TodoApp()
    task = Task("Test Task")
    app.tasks = [task]
    
    with patch('customtkinter.CTkInputDialog', new_callable=MagicMock) as mock_input_dialog:
        mock_input_dialog.return_value.get_input.return_value = "New Task"
        
        app.edit_task(task)
        
        assert task.title == "New Task"

def test_delete_task():
    app = TodoApp()
    task = Task("Test Task")
    app.tasks = [task]
    
    app.delete_task(task)
    
    assert len(app.tasks) == 0

def test_toggle_task():
    app = TodoApp()
    task = Task("Test Task")
    app.tasks = [task]
    
    app.toggle_task()
    
    assert task.completed

def test_set_filter():
    app = TodoApp()
    
    app.set_filter("active")
    
    assert app.filter_mode == "active"

def test_on_closing():
    app = TodoApp()
    
    with patch.object(app, 'save_tasks') as mock_save_tasks:
        with patch.object(app, 'destroy') as mock_destroy:
            app.on_closing()
            mock_save_tasks.assert_called_once()
            mock_destroy.assert_called_once()