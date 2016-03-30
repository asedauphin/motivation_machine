# -*- coding: utf-8 -*-

"""
Tkinter UI definition
"""

__author__ = 'joscha'
__date__ = '3/15/16'

from tkinter import *
from tkinter import ttk, filedialog, messagebox
from configuration import Settings
import math

import time

import simulation as simulation



from helper_widgets import MainMenu, SimFrame, ConfigDialog

class GuiApp(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)
        #self.geometry("500x500")
        self.minsize(500, 250)

        # menus
        self.option_add('*tearOff', FALSE)
        menubar = MainMenu(self)
        for diagram in simulation.diagrams:
            key = diagram.key
            menubar.menu_plot.add_command(label= "Plot " + key, command=lambda key=key : self.open_diagram(key))
        self.config(menu=menubar)

        # diagram
        self.open_diagrams = {}

        # frames
        content_frame = ttk.Frame(self)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        content_frame.grid(column=0, row=0, sticky=(N, W, E, S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)

        self.simulator = SimFrame(content_frame)
        self.simulator.grid(row=0, column=0, sticky=(W, E))


        spacer = ttk.Frame(content_frame)
        spacer.grid(row=98, column=0, sticky=(W, E, N, S))
        spacer.rowconfigure(0, weight=1)

        self.spacer = spacer

        self.status = StringVar()
        self.status_bar = ttk.Frame(content_frame, padding = (6, 6, 6, 6), relief="sunken")
        self.status_bar.grid(row=99, column=0, sticky=(W, E, N, S))
        self.status_label = ttk.Label(self.status_bar, textvariable = self.status)
        self.status_label.grid(row=0, column=0, sticky=(W, E, N, S))

        # simulation thread
        self.running = False

        self.reset_simulation()


    def open_diagram(self, key):
        """open a diagram window for the given type"""
        if not key in self.open_diagrams:
            for Diagram in simulation.diagrams:
                if Diagram.key == key:
                    self.open_diagrams[key] = Diagram(self, self.simulation)


    def calculate_need_coordinates(self, needs):
        """Arrange the needs in a circle on the canvas"""
        self.need_coordinates = []
        origin = (350, 350)
        r = 300
        k = len(needs)
        for n in range(0, k):
            self.need_coordinates.append(
                (r * math.cos(2 * math.pi * n / k) + origin[0],
                 r * math.sin(2 * math.pi * n / k) + origin[1])
            )


    def configure_simulation(self):
        """Configure simulation settings and initialize values"""
        ConfigDialog(self)  # will call reset simulation for us

    def run_simulation(self):
        """Starts a runner that will trigger simulation steps"""
        self.status.set("running")
        self.running = True
        while self.running:
            self.simulation.step()
            self.update_display_after_simstep()
            self.update()
            time.sleep(Settings.update_milliseconds/1000)

    def stop_simulation(self):
        """Pauses the runner that triggers simulation steps"""
        self.running = False
        self.update_display_after_simstep()
        self.status.set("paused")

    def reset_simulation(self):
        """Initializes all values to original settings and sets up the canvas"""

        self.running = False

        self.simulation = simulation.Simulation()  # the self parameter tells the sim where to find the gui

        diagrams = list(self.open_diagrams.values())
        for plot in diagrams:
            plot.destroy()  # close diagrams because they are bound to old data sets

        self.setup_need_drawings(self.simulation.needs)

        self.update_display_after_simstep()
        self.status.set("ready to start")


    def step_simulation(self):
        """Advances the simulation by a single step"""
        self.running = False
        self.status.set("step")
        self.simulation.step()
        self.update_display_after_simstep()
        self.status.set("paused")


    def export_simulation_data(self):
        filename = filedialog.asksaveasfilename()
        print("export simulation "+filename)

    def export_plot(self):
        print("export diagram")

    def show_contact(self):
        messagebox.showinfo(title="Contact", message="Joscha Bach, 2016\njoscha@mit.edu")

    def setup_need_drawings(self, needs):
        """Draw needs and their respective values"""
        c = self.simulator.canvas
        self.calculate_need_coordinates(needs)
        self.simulator.canvas.delete(ALL)
        radius = 10
        offset = 18
        self.need_drawings = []
        self.need_value_labels = []


        for i, (x, y) in enumerate(self.need_coordinates):
            self.need_drawings.append(c.create_oval(x-radius, y-radius, x+radius, y+radius,
                                                                         outline="black", fill="lightblue", width=2))
            self.need_value_labels.append([
                c.create_text(x, y + offset, text="", fill="blue"),
                c.create_text(x, y + 2 * offset, text="", fill="orange"),
                c.create_text(x, y - offset, text="", fill="green"),
                c.create_text(x, y - 2 * offset, text="", fill="red"),
                c.create_text(x, y, text=needs[i].name, fill="black"),
            ])

    def update_need_value_labels(self, need_index, need):
        """paints the updated values on the canvas"""
        values = [need.urge_strength, need.urgency, need.pleasure, need.pain]
        for index, value in enumerate(values):
            self.simulator.canvas.itemconfig(self.need_value_labels[need_index][index], text= str(round(value, 3)))


    def update_display_after_simstep(self):
        """Update gui display after every individual simulationstep"""
        self.simulator.simstep.set(self.simulation.current_simstep)
        for i, need in enumerate(self.simulation.needs):
            self.update_need_value_labels(i, need)
        self.update_plots()


    def update_plots(self):
        try:
            for plot in self.open_diagrams.values():
                plot.update_diagram()
        except RuntimeError:  # thread hates it when we add new diagrams while running
            pass
