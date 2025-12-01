import customtkinter as ctk
import json
import os
from datetime import datetime
from typing import List, Dict

# Application Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class Task:
    """Represents a single task"""

    def __init__(self, title: str, completed: bool = False, created_at: str = None):
        self.title = title
        self.completed = completed
        self.created_at = created_at or datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "title": self.title,
            "completed": self.completed,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict):
        return cls(data["title"], data["completed"], data.get("created_at"))


class TaskWidget(ctk.CTkFrame):
    """Custom widget for displaying a task"""

    def __init__(self, master, task: Task, on_toggle, on_delete, on_edit, **kwargs):
        super().__init__(master, **kwargs)

        self.task = task
        self.on_toggle = on_toggle
        self.on_delete = on_delete
        self.on_edit = on_edit

        self.configure(fg_color=("gray85", "gray20"), corner_radius=10)

        # Checkbox
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            width=30,
            command=self._toggle_task,
            checkbox_width=22,
            checkbox_height=22,
        )
        self.checkbox.grid(row=0, column=0, padx=(15, 10), pady=15, sticky="w")

        # Task label
        self.label = ctk.CTkLabel(
            self, text=task.title, font=ctk.CTkFont(size=14), anchor="w"
        )
        self.label.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
        self.label.bind("<Double-Button-1>", lambda e: self._edit_task())

        # Delete button
        self.delete_btn = ctk.CTkButton(
            self,
            text="✕",
            width=35,
            height=35,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color="transparent",
            hover_color=("gray75", "gray30"),
            text_color=("gray40", "gray60"),
            command=self._delete_task,
        )
        self.delete_btn.grid(row=0, column=2, padx=(5, 15), pady=15)

        # Configure grid
        self.grid_columnconfigure(1, weight=1)

        self._update_appearance()

    def _update_appearance(self):
        """Update the appearance based on completion status"""
        if self.task.completed:
            self.checkbox.select()
            self.label.configure(
                text_color=("gray50", "gray55"),
                font=ctk.CTkFont(size=14, overstrike=True),
            )
        else:
            self.checkbox.deselect()
            self.label.configure(
                text_color=("gray10", "gray90"),
                font=ctk.CTkFont(size=14, overstrike=False),
            )

    def _toggle_task(self):
        self.task.completed = not self.task.completed
        self._update_appearance()
        self.on_toggle()

    def _delete_task(self):
        self.on_delete(self.task)

    def _edit_task(self):
        self.on_edit(self.task)

    def update_task(self, task: Task):
        """Update the widget with new task data"""
        self.task = task
        self.label.configure(text=task.title)
        self._update_appearance()


class TodoApp(ctk.CTk):
    """Main To-Do Application"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("To-Do App")
        self.geometry("600x750")
        self.minsize(500, 600)

        # Data
        self.tasks: List[Task] = []
        self.filter_mode = "all"  # all, active, completed
        self.data_file = "tasks.json"

        # Load saved tasks
        self.load_tasks()

        # Build UI
        self.create_widgets()
        self.refresh_task_list()

        # Protocol for closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """Create all UI widgets"""

        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ===== HEADER =====
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            header_frame, text="📝 My Tasks", font=ctk.CTkFont(size=32, weight="bold")
        )
        title_label.grid(row=0, column=0, sticky="w")

        # Theme toggle
        self.theme_switch = ctk.CTkSwitch(
            header_frame,
            text="🌙",
            font=ctk.CTkFont(size=20),
            command=self.toggle_theme,
            width=60,
        )
        self.theme_switch.grid(row=0, column=1, padx=10)

        # Stats
        self.stats_label = ctk.CTkLabel(
            header_frame,
            text="0 tasks",
            font=ctk.CTkFont(size=13),
            text_color=("gray50", "gray60"),
        )
        self.stats_label.grid(row=1, column=0, sticky="w", pady=(5, 0))

        # ===== INPUT SECTION =====
        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        # Task entry
        self.task_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Add a new task...",
            height=45,
            font=ctk.CTkFont(size=14),
            border_width=2,
        )
        self.task_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.task_entry.bind("<Return>", lambda e: self.add_task())

        # Add button
        self.add_btn = ctk.CTkButton(
            input_frame,
            text="Add",
            width=80,
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self.add_task,
        )
        self.add_btn.grid(row=0, column=1)

        # ===== FILTER SECTION =====
        filter_frame = ctk.CTkFrame(self, fg_color="transparent")
        filter_frame.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Filter buttons
        self.filter_all_btn = ctk.CTkButton(
            filter_frame,
            text="All",
            width=80,
            height=32,
            command=lambda: self.set_filter("all"),
            fg_color=("gray70", "gray30"),
        )
        self.filter_all_btn.grid(row=0, column=0, padx=(0, 5))

        self.filter_active_btn = ctk.CTkButton(
            filter_frame,
            text="Active",
            width=80,
            height=32,
            command=lambda: self.set_filter("active"),
            fg_color="transparent",
            border_width=2,
        )
        self.filter_active_btn.grid(row=0, column=1, padx=5)

        self.filter_completed_btn = ctk.CTkButton(
            filter_frame,
            text="Completed",
            width=80,
            height=32,
            command=lambda: self.set_filter("completed"),
            fg_color="transparent",
            border_width=2,
        )
        self.filter_completed_btn.grid(row=0, column=2, padx=5)

        # Clear completed button
        self.clear_btn = ctk.CTkButton(
            filter_frame,
            text="Clear Completed",
            width=120,
            height=32,
            command=self.clear_completed,
            fg_color="transparent",
            border_width=2,
            text_color=("red", "lightcoral"),
        )
        self.clear_btn.grid(row=0, column=3, padx=(20, 0))

        # ===== TASK LIST =====
        self.scrollable_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray30"),
            scrollbar_button_hover_color=("gray60", "gray40"),
        )
        self.scrollable_frame.grid(
            row=3, column=0, padx=20, pady=(0, 20), sticky="nsew"
        )
        self.scrollable_frame.grid_columnconfigure(0, weight=1)

    def add_task(self):
        """Add a new task"""
        title = self.task_entry.get().strip()
        if not title:
            return

        task = Task(title)
        self.tasks.append(task)
        self.task_entry.delete(0, "end")
        self.save_tasks()
        self.refresh_task_list()

    def edit_task(self, task: Task):
        """Edit an existing task"""
        dialog = ctk.CTkInputDialog(text=f"Edit task:", title="Edit Task")
        dialog._entry.insert(0, task.title)
        new_title = dialog.get_input()

        if new_title and new_title.strip():
            task.title = new_title.strip()
            self.save_tasks()
            self.refresh_task_list()

    def delete_task(self, task: Task):
        """Delete a task"""
        self.tasks.remove(task)
        self.save_tasks()
        self.refresh_task_list()

    def toggle_task(self):
        """Task completion toggled"""
        self.save_tasks()
        self.update_stats()

    def set_filter(self, mode: str):
        """Set the filter mode and update UI"""
        self.filter_mode = mode

        # Update button appearance
        buttons = {
            "all": self.filter_all_btn,
            "active": self.filter_active_btn,
            "completed": self.filter_completed_btn,
        }

        for btn_mode, btn in buttons.items():
            if btn_mode == mode:
                btn.configure(fg_color=("gray70", "gray30"), border_width=0)
            else:
                btn.configure(fg_color="transparent", border_width=2)

        self.refresh_task_list()

    def clear_completed(self):
        """Remove all completed tasks"""
        self.tasks = [task for task in self.tasks if not task.completed]
        self.save_tasks()
        self.refresh_task_list()

    def refresh_task_list(self):
        """Refresh the displayed task list"""
        # Clear existing widgets
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Filter tasks
        filtered_tasks = self.get_filtered_tasks()

        # Create widgets for filtered tasks
        for i, task in enumerate(filtered_tasks):
            task_widget = TaskWidget(
                self.scrollable_frame,
                task,
                on_toggle=self.toggle_task,
                on_delete=self.delete_task,
                on_edit=self.edit_task,
            )
            task_widget.grid(row=i, column=0, padx=0, pady=5, sticky="ew")

        # Show empty state if no tasks
        if not filtered_tasks:
            empty_label = ctk.CTkLabel(
                self.scrollable_frame,
                text="No tasks to show"
                if self.tasks
                else "Add your first task to get started! ✨",
                font=ctk.CTkFont(size=14),
                text_color=("gray50", "gray60"),
            )
            empty_label.grid(row=0, column=0, pady=50)

        self.update_stats()

    def get_filtered_tasks(self) -> List[Task]:
        """Get tasks based on current filter"""
        if self.filter_mode == "active":
            return [task for task in self.tasks if not task.completed]
        elif self.filter_mode == "completed":
            return [task for task in self.tasks if task.completed]
        else:  # all
            return self.tasks

    def update_stats(self):
        """Update the statistics display"""
        total = len(self.tasks)
        completed = sum(1 for task in self.tasks if task.completed)
        active = total - completed

        if total == 0:
            stats_text = "No tasks"
        else:
            stats_text = f"{total} task{'s' if total != 1 else ''} • {active} active • {completed} completed"

        self.stats_label.configure(text=stats_text)

    def toggle_theme(self):
        """Toggle between dark and light mode"""
        current_mode = ctk.get_appearance_mode()
        new_mode = "light" if current_mode.lower() == "dark" else "dark"
        ctk.set_appearance_mode(new_mode)

        # Update switch emoji
        self.theme_switch.configure(text="☀️" if new_mode == "light" else "🌙")

    def save_tasks(self):
        """Save tasks to JSON file"""
        data = {
            "tasks": [task.to_dict() for task in self.tasks],
            "theme": ctk.get_appearance_mode(),
        }
        with open(self.data_file, "w") as f:
            json.dump(data, f, indent=2)

    def load_tasks(self):
        """Load tasks from JSON file"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    self.tasks = [
                        Task.from_dict(task_data) for task_data in data.get("tasks", [])
                    ]

                    # Restore theme
                    saved_theme = data.get("theme", "dark")
                    ctk.set_appearance_mode(saved_theme)
            except Exception as e:
                print(f"Error loading tasks: {e}")
                self.tasks = []

    def on_closing(self):
        """Handle application closing"""
        self.save_tasks()
        self.destroy()


def main():
    """Main entry point"""
    app = TodoApp()
    app.mainloop()


if __name__ == "__main__":
    main()
