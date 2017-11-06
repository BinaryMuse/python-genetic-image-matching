import sys

import tkinter as Tk
from genetic import App

target_image = sys.argv[1]
root_window = Tk.Tk()
app = App(root_window, target_image, mutation_chance=0.1)
app.focus()
app.run()
