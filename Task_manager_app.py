import tkinter as tk
from tkinter import messagebox, simpledialog
import sqlite3
import hashlib

# Initialize database connection and create tables if they don't exist
def initialize_db():
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        completed BOOLEAN NOT NULL DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    ''')
    conn.commit()
    return conn, cursor

class TaskAppGUI:
    def __init__(self, root, conn, cursor):
        self.root = root
        self.conn = conn
        self.cursor = cursor
        self.root.title('Task Management App')
        self.current_user_id = None  # To keep track of the logged-in user
        self.setup_login_frame()

    # Define other methods as previously described...

    def setup_login_frame(self):
        self.clear_frames()
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack()

        tk.Label(self.login_frame, text='Username:').pack()
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.pack()

        tk.Label(self.login_frame, text='Password:').pack()
        self.password_entry = tk.Entry(self.login_frame, show='*')
        self.password_entry.pack()

        tk.Button(self.login_frame, text='Login', command=self.login).pack()
        tk.Button(self.login_frame, text='Register', command=self.register).pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()

        cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hashed_password))
        user = cursor.fetchone()
        if user:
            self.current_user_id = user[0]  # Store the user's ID
            messagebox.showinfo("Login Successful", "You are now logged in.")
            self.show_main_menu()
        else:
            messagebox.showerror("Login Failed", "Incorrect username or password.")

    def register(self):

    # The registration function remains the same as previously defined

        username = simpledialog.askstring("Username", "Choose a username:")
        password = simpledialog.askstring("Password", "Choose a password:", show='*')
        if username and password:
            hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
                conn.commit()
                messagebox.showinfo("Registration Successful", "You can now log in with your credentials.")
            except sqlite3.IntegrityError:
                messagebox.showerror("Registration Failed", "Username already exists.")
    def show_main_menu(self):
        self.clear_frames()
        self.main_menu_frame = tk.Frame(self.root)
        self.main_menu_frame.pack()

        tk.Button(self.main_menu_frame, text='Add a Task', command=self.add_task).pack()
        tk.Button(self.main_menu_frame, text='View Tasks', command=self.view_tasks).pack()
        tk.Button(self.main_menu_frame, text='Logout', command=self.logout).pack()

    def add_task(self):
        self.clear_frames()
        add_task_frame = tk.Frame(self.root)
        add_task_frame.pack()

        tk.Label(add_task_frame, text='Title:').pack()
        title_entry = tk.Entry(add_task_frame)
        title_entry.pack()

        tk.Label(add_task_frame, text='Description:').pack()
        description_entry = tk.Entry(add_task_frame)
        description_entry.pack()

        def submit_task():
            title = title_entry.get()
            description = description_entry.get()
            if title:
                self.cursor.execute("INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
                                    (self.current_user_id, title, description))
                self.conn.commit()
                messagebox.showinfo("Success", "Task added successfully.")
                self.show_main_menu()
            else:
                messagebox.showerror("Error", "Title cannot be empty.")

        tk.Button(add_task_frame, text='Submit', command=submit_task).pack()

    def view_tasks(self):
        self.clear_frames()
        view_tasks_frame = tk.Frame(self.root)
        view_tasks_frame.pack()

        tk.Label(view_tasks_frame, text="Select a task:").pack()
        tasks_listbox = tk.Listbox(view_tasks_frame)
        tasks_listbox.pack()

        self.cursor.execute("SELECT id, title, description, completed FROM tasks WHERE user_id = ?",
                            (self.current_user_id,))
        for task in self.cursor.fetchall():
            status = "Completed" if task[3] else "Not Completed"
            tasks_listbox.insert(tk.END, f"{task[0]}: {task[1]} - {task[2]} [{status}]")

        def complete_task():
            selection = tasks_listbox.curselection()
            if selection:
                task_id = tasks_listbox.get(selection[0]).split(":")[0]
                self.cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
                self.conn.commit()
                messagebox.showinfo("Success", "Task marked as completed.")
                self.view_tasks()

        def edit_task():
            selection = tasks_listbox.curselection()
            if selection:
                task_id = tasks_listbox.get(selection[0]).split(":")[0]
                self.edit_task_details(task_id)

        tk.Button(view_tasks_frame, text='Complete Selected Task', command=complete_task).pack()
        tk.Button(view_tasks_frame, text='Edit Selected Task', command=edit_task).pack()


        # Inside the view_tasks method
        tk.Button(view_tasks_frame, text='Delete Selected Task', command=lambda: self.delete_task(tasks_listbox)).pack()

        tk.Button(view_tasks_frame, text='Back to Main Menu', command=self.show_main_menu).pack()

    def edit_task_details(self, task_id):
        # Fetch the current details of the task to populate the fields.
        self.cursor.execute("SELECT title, description FROM tasks WHERE id = ?", (task_id,))
        task = self.cursor.fetchone()

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Task")

        tk.Label(edit_window, text="Title:").pack()
        title_entry = tk.Entry(edit_window)
        title_entry.insert(0, task[0])
        title_entry.pack()

        tk.Label(edit_window, text="Description:").pack()
        description_entry = tk.Entry(edit_window)
        description_entry.insert(0, task[1])
        description_entry.pack()

        def submit_changes():
            new_title = title_entry.get()
            new_description = description_entry.get()
            self.cursor.execute("UPDATE tasks SET title = ?, description = ? WHERE id = ?",
                                (new_title, new_description, task_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Task updated successfully.")
            edit_window.destroy()
            self.view_tasks()

        tk.Button(edit_window, text="Submit", command=submit_changes).pack()


    def delete_task(self,tasks_listbox):
            selection = tasks_listbox.curselection()
            if selection:
                task_id = tasks_listbox.get(selection[0]).split(":")[0]
                if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this task?"):
                    self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
                    self.conn.commit()
                    messagebox.showinfo("Success", "Task deleted successfully.")
                    self.view_tasks()




    def logout(self):
        self.current_user_id = None
        self.setup_login_frame()

    def clear_frames(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # Add task, view tasks, and other functionalities as previously described...

if __name__ == "__main__":
    # Database initialization
    conn, cursor = initialize_db()

    # Create the main application window
    root = tk.Tk()
    app = TaskAppGUI(root, conn, cursor)

    # Start the main event loop
    root.mainloop()

    # Close database connection upon exiting the application
    conn.close()
