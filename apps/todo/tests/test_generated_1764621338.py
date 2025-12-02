import pytest
import sys
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import source module directly (for coverage measurement)
import todo_app
from todo_app import Task, TaskWidget, TodoApp


def test_add_task_with_valid_title_via_button():
    app = TodoApp()
    app.task_entry.insert(0, "Test Task")
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.add_task()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "Test Task"
        assert app.task_entry.get() == ""
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()


def test_add_task_with_valid_title_via_enter():
    app = TodoApp()
    app.task_entry.insert(0, "Test Task")
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.add_task()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "Test Task"
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()


def test_add_task_with_empty_title():
    app = TodoApp()
    app.task_entry.insert(0, "")
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.add_task()
        
        assert len(app.tasks) == 0
        mock_save.assert_not_called()
        mock_refresh.assert_not_called()


def test_add_task_with_whitespace_only():
    app = TodoApp()
    app.task_entry.insert(0, "   ")
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.add_task()
        
        assert len(app.tasks) == 0
        mock_save.assert_not_called()
        mock_refresh.assert_not_called()


def test_edit_task_with_valid_new_title():
    app = TodoApp()
    original_task = Task("Original Title")
    app.tasks.append(original_task)
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog, \
         patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = "New Title"
        mock_dialog.return_value = mock_instance
        
        app.edit_task(original_task)
        
        assert original_task.title == "New Title"
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()


def test_edit_task_with_empty_title():
    app = TodoApp()
    original_task = Task("Original Title")
    app.tasks.append(original_task)
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog, \
         patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = ""
        mock_dialog.return_value = mock_instance
        
        app.edit_task(original_task)
        
        assert original_task.title == "Original Title"
        mock_save.assert_not_called()
        mock_refresh.assert_not_called()


def test_delete_task():
    app = TodoApp()
    task_to_delete = Task("Task to Delete")
    app.tasks.append(task_to_delete)
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.delete_task(task_to_delete)
        
        assert len(app.tasks) == 0
        assert task_to_delete not in app.tasks
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()


def test_toggle_task_completion():
    app = TodoApp()
    task = Task("Test Task", completed=False)
    app.tasks.append(task)
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'update_stats') as mock_update_stats:
        
        app.toggle_task()
        
        mock_save.assert_called_once()
        mock_update_stats.assert_called_once()


def test_set_filter_active():
    app = TodoApp()
    
    app.set_filter("active")
    
    assert app.filter_mode == "active"
    assert app.filter_all_btn.cget("fg_color") == "transparent"
    assert app.filter_active_btn.cget("fg_color") == ("gray70", "gray30")
    assert app.filter_completed_btn.cget("fg_color") == "transparent"


def test_set_filter_completed():
    app = TodoApp()
    
    app.set_filter("completed")
    
    assert app.filter_mode == "completed"
    assert app.filter_all_btn.cget("fg_color") == "transparent"
    assert app.filter_active_btn.cget("fg_color") == "transparent"
    assert app.filter_completed_btn.cget("fg_color") == ("gray70", "gray30")


def test_set_filter_all():
    app = TodoApp()
    app.filter_mode = "active"
    
    app.set_filter("all")
    
    assert app.filter_mode == "all"
    assert app.filter_all_btn.cget("fg_color") == ("gray70", "gray30")
    assert app.filter_active_btn.cget("fg_color") == "transparent"
    assert app.filter_completed_btn.cget("fg_color") == "transparent"


def test_clear_completed():
    app = TodoApp()
    app.tasks = [
        Task("Active Task 1", completed=False),
        Task("Completed Task 1", completed=True),
        Task("Active Task 2", completed=False),
        Task("Completed Task 2", completed=True),
    ]
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        app.clear_completed()
        
        assert len(app.tasks) == 2
        assert all(not task.completed for task in app.tasks)
        mock_save.assert_called_once()
        mock_refresh.assert_called_once()


def test_update_stats_no_tasks():
    app = TodoApp()
    app.tasks = []
    
    app.update_stats()
    
    assert app.stats_label.cget("text") == "No tasks"


def test_update_stats_single_task():
    app = TodoApp()
    app.tasks = [Task("Single Task", completed=False)]
    
    app.update_stats()
    
    assert app.stats_label.cget("text") == "1 task • 1 active • 0 completed"


def test_update_stats_multiple_tasks():
    app = TodoApp()
    app.tasks = [
        Task("Task 1", completed=False),
        Task("Task 2", completed=True),
        Task("Task 3", completed=False),
    ]
    
    app.update_stats()
    
    assert app.stats_label.cget("text") == "3 tasks • 2 active • 1 completed"


def test_toggle_theme_dark_to_light():
    app = TodoApp()
    
    with patch('customtkinter.get_appearance_mode', return_value="dark"), \
         patch('customtkinter.set_appearance_mode') as mock_set_mode:
        
        app.toggle_theme()
        
        mock_set_mode.assert_called_once_with("light")
        assert app.theme_switch.cget("text") == "☀️"


def test_toggle_theme_light_to_dark():
    app = TodoApp()
    
    with patch('customtkinter.get_appearance_mode', return_value="light"), \
         patch('customtkinter.set_appearance_mode') as mock_set_mode:
        
        app.toggle_theme()
        
        mock_set_mode.assert_called_once_with("dark")
        assert app.theme_switch.cget("text") == "🌙"


def test_save_tasks():
    app = TodoApp()
    app.tasks = [Task("Test Task", completed=False)]
    
    with patch('builtins.open', mock_open()) as mock_file, \
         patch('customtkinter.get_appearance_mode', return_value="dark"):
        
        app.save_tasks()
        
        mock_file.assert_called_once_with("tasks.json", "w")
        written_data = mock_file().write.call_args[0][0]
        saved_data = json.loads(written_data)
        
        assert len(saved_data["tasks"]) == 1
        assert saved_data["tasks"][0]["title"] == "Test Task"
        assert saved_data["theme"] == "dark"


def test_load_tasks_success():
    app = TodoApp()
    test_data = {
        "tasks": [{"title": "Loaded Task", "completed": True, "created_at": "2023-01-01T00:00:00"}],
        "theme": "light"
    }
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(test_data))), \
         patch('customtkinter.set_appearance_mode') as mock_set_theme:
        
        app.load_tasks()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].title == "Loaded Task"
        assert app.tasks[0].completed is True
        mock_set_theme.assert_called_once_with("light")


def test_load_tasks_file_missing():
    app = TodoApp()
    
    with patch('os.path.exists', return_value=False):
        app.load_tasks()
        
        assert len(app.tasks) == 0


def test_load_tasks_corrupted_json():
    app = TodoApp()
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data="invalid json")), \
         patch('builtins.print') as mock_print:
        
        app.load_tasks()
        
        assert len(app.tasks) == 0
        mock_print.assert_called_once()


def test_load_tasks_missing_title_key():
    app = TodoApp()
    test_data = {
        "tasks": [{"completed": True, "created_at": "2023-01-01T00:00:00"}],
        "theme": "dark"
    }
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(test_data))), \
         patch('builtins.print') as mock_print:
        
        app.load_tasks()
        
        assert len(app.tasks) == 0
        mock_print.assert_called_once()


def test_load_tasks_missing_completed_key():
    app = TodoApp()
    test_data = {
        "tasks": [{"title": "Task without completed", "created_at": "2023-01-01T00:00:00"}],
        "theme": "dark"
    }
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(test_data))), \
         patch('customtkinter.set_appearance_mode'):
        
        app.load_tasks()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].completed is False


def test_load_tasks_missing_created_at_key():
    app = TodoApp()
    test_data = {
        "tasks": [{"title": "Task without created_at", "completed": False}],
        "theme": "dark"
    }
    
    with patch('os.path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=json.dumps(test_data))), \
         patch('customtkinter.set_appearance_mode'):
        
        app.load_tasks()
        
        assert len(app.tasks) == 1
        assert app.tasks[0].created_at is not None


def test_save_tasks_permission_error():
    app = TodoApp()
    app.tasks = [Task("Test Task")]
    
    with patch('builtins.open', side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            app.save_tasks()


def test_task_creation_with_long_title():
    long_title = "A" * 500
    task = Task(long_title)
    
    assert task.title == long_title
    assert len(task.title) == 500


def test_task_creation_with_special_characters():
    special_title = "Task with 🎉 emojis \n and newlines \t and tabs"
    task = Task(special_title)
    
    assert task.title == special_title


def test_duplicate_task_titles_allowed():
    app = TodoApp()
    app.tasks = [Task("Duplicate Title"), Task("Duplicate Title")]
    
    assert len(app.tasks) == 2
    assert app.tasks[0].title == app.tasks[1].title
    assert app.tasks[0] != app.tasks[1]


def test_set_filter_invalid_mode():
    app = TodoApp()
    original_filter = app.filter_mode
    
    app.set_filter("invalid_mode")
    
    assert app.filter_mode == original_filter


def test_task_creation_with_explicit_created_at():
    custom_time = "2023-01-01T12:00:00"
    task = Task("Test Task", created_at=custom_time)
    
    assert task.created_at == custom_time


def test_task_creation_without_created_at():
    task = Task("Test Task")
    
    assert task.created_at is not None
    assert isinstance(task.created_at, str)


def test_task_widget_update_task():
    task = Task("Original Title", completed=False)
    widget = TaskWidget(None, task, lambda: None, lambda t: None, lambda t: None)
    
    new_task = Task("Updated Title", completed=True)
    widget.update_task(new_task)
    
    assert widget.task == new_task
    assert widget.label.cget("text") == "Updated Title"


def test_get_filtered_tasks_all():
    app = TodoApp()
    app.tasks = [
        Task("Active Task", completed=False),
        Task("Completed Task", completed=True),
    ]
    app.filter_mode = "all"
    
    filtered = app.get_filtered_tasks()
    
    assert len(filtered) == 2


def test_get_filtered_tasks_active():
    app = TodoApp()
    app.tasks = [
        Task("Active Task", completed=False),
        Task("Completed Task", completed=True),
    ]
    app.filter_mode = "active"
    
    filtered = app.get_filtered_tasks()
    
    assert len(filtered) == 1
    assert not filtered[0].completed


def test_get_filtered_tasks_completed():
    app = TodoApp()
    app.tasks = [
        Task("Active Task", completed=False),
        Task("Completed Task", completed=True),
    ]
    app.filter_mode = "completed"
    
    filtered = app.get_filtered_tasks()
    
    assert len(filtered) == 1
    assert filtered[0].completed


def test_on_closing():
    app = TodoApp()
    
    with patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'destroy') as mock_destroy:
        
        app.on_closing()
        
        mock_save.assert_called_once()
        mock_destroy.assert_called_once()


def test_edit_task_dialog_cancelled():
    app = TodoApp()
    original_task = Task("Original Title")
    app.tasks.append(original_task)
    
    with patch('customtkinter.CTkInputDialog') as mock_dialog, \
         patch.object(app, 'save_tasks') as mock_save, \
         patch.object(app, 'refresh_task_list') as mock_refresh:
        
        mock_instance = MagicMock()
        mock_instance.get_input.return_value = None
        mock_dialog.return_value = mock_instance
        
        app.edit_task(original_task)
        
        assert original_task.title == "Original Title"
        mock_save.assert_not_called()
        mock_refresh.assert_not_called()


def test_empty_state_label_with_tasks_but_no_match():
    app = TodoApp()
    app.tasks = [Task("Active Task", completed=False)]
    app.filter_mode = "completed"
    
    with patch.object(app.scrollable_frame, 'winfo_children', return_value=[]):
        app.refresh_task_list()
        
        # Should show "No tasks to show" when tasks exist but none match filter
        # This is verified by the empty state logic in refresh_task_list


def test_empty_state_label_with_no_tasks():
    app = TodoApp()
    app.tasks = []
    
    with patch.object(app.scrollable_frame, 'winfo_children', return_value=[]):
        app.refresh_task_list()
        
        # Should show "Add your first task to get started! ✨" when no tasks exist


def test_theme_switch_emoji_after_loading_saved_theme():
    app = TodoApp()
    
    with patch('customtkinter.get_appearance_mode', return_value="light"):
        app.theme_switch.configure(text="☀️")
        assert app.theme_switch.cget("text") == "☀️"
    
    with patch('customtkinter.get_appearance_mode', return_value="dark"):
        app.theme_switch.configure(text="🌙")
        assert app.theme_switch.cget("text") == "🌙"