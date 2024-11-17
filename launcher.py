import tkinter as tk
from PIL import Image, ImageTk
import subprocess
import os
import sys

def launch_maze():
    script_path = os.path.join(os.getcwd(), "MAZE.py")
    subprocess.run([sys.executable, script_path])

def launch_snake_wars():
    script_path = os.path.join(os.getcwd(), "snake_wars.py")
    subprocess.run([sys.executable, script_path])

def on_enter_button(button):
    button.config(bg="#1e8449", font=("Helvetica", 16, "bold"))

def on_leave_button(button):
    button.config(bg="#27ae60", font=("Helvetica", 14))

window = tk.Tk()
window.title("Game Launcher")
window.geometry("800x400")
window.config(bg="#34495e")

maze_image = Image.open("assets/maze_bg.png")
maze_image = maze_image.resize(
    (int(maze_image.width * 0.4), int(maze_image.height * 0.4)),
    Image.ANTIALIAS
)
maze_bg = ImageTk.PhotoImage(maze_image)

snake_image = Image.open("assets/snake_bg.png")
snake_image = snake_image.resize(
    (int(snake_image.width * 0.4), int(snake_image.height * 0.4)),
    Image.ANTIALIAS
)
snake_bg = ImageTk.PhotoImage(snake_image)

frame_maze = tk.Frame(window, width=400, height=400)
frame_maze.pack(side="left", fill="both", expand=True)
frame_maze_bg = tk.Label(frame_maze, image=maze_bg)
frame_maze_bg.place(relwidth=1, relheight=1)

frame_snake = tk.Frame(window, width=400, height=400)
frame_snake.pack(side="right", fill="both", expand=True)
frame_snake_bg = tk.Label(frame_snake, image=snake_bg)
frame_snake_bg.place(relwidth=1, relheight=1)

separator = tk.Frame(window, width=2, bg="#ecf0f1")
separator.place(relx=0.5, rely=0, relheight=1)

button_maze = tk.Button(
    frame_maze,
    text="Launch Maze",
    font=("Helvetica", 14),
    bg="#27ae60",
    fg="#ecf0f1",
    activebackground="#1e8449",
    activeforeground="#ecf0f1",
    relief="flat",
    command=launch_maze
)
button_maze.place(relx=0.5, rely=0.5, anchor="center")

button_maze.bind("<Enter>", lambda e: on_enter_button(button_maze))
button_maze.bind("<Leave>", lambda e: on_leave_button(button_maze))

# Bouton pour lancer Snake Wars
button_snake_wars = tk.Button(
    frame_snake,
    text="Launch Snake Wars",
    font=("Helvetica", 14),
    bg="#27ae60",
    fg="#ecf0f1",
    activebackground="#1e8449",
    activeforeground="#ecf0f1",
    relief="flat",
    command=launch_snake_wars
)
button_snake_wars.place(relx=0.5, rely=0.5, anchor="center")

button_snake_wars.bind("<Enter>", lambda e: on_enter_button(button_snake_wars))
button_snake_wars.bind("<Leave>", lambda e: on_leave_button(button_snake_wars))

window.mainloop()
