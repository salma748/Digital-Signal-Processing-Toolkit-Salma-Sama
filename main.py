import tkinter as tk

from gui.task_menu import TaskMenu


def main():
    root = tk.Tk()
    app = TaskMenu(root)
    root.mainloop()


if __name__ == "__main__":
    main()