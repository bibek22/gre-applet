#!/usr/bin/env python
import PySimpleGUI as sg
import subprocess
import time
from multiprocessing import Process

record = []
answers = []
prev = time.time()
ht = 6
w = 16
i = 1

def show(answers):
    banner = "Qn.\tAns\tTime"
    print("\n" + "="*len(banner))
    print(banner)
    print("-"*len(banner))
    for item in answers:
        print("%s\t%s\t%s" % item)

sg.theme('DarkGreen3')	# Add a touch of color
# All the stuff inside your window.
the_only_button = sg.Button("QN: {}".format(i), size=(2*w+5, 2*ht+4))
field = sg.Text("0:00", size=(w, ht))
options = ["A", "B", "C", "D", "E", "F", "G"]
option_buttons = [sg.Button(label, size=(w, ht)) for label in options]
layout = [ 
        [option_buttons[0]],
        [option_buttons[1]],
        [option_buttons[2]],
        [option_buttons[3]],
        [option_buttons[4]],
        [option_buttons[5]],
        [option_buttons[6]]
        ]

def sec2time(secs):
    time = str(secs // 60) + ":" + "{:02d}".format(secs % 60)
    return(time)

def timer(field):
    duration = 0
    while True:
        print(duration)
        time.sleep(1)
        duration += 1
        label = sec2time(duration)
        field.Update()

# Create the Window
window = sg.Window('record', layout, finalize=True)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':# if user closes window or clicks cancel
        break
    if event in options:
        now = time.time() 
        duration = sec2time(int(now - prev))
        answers.append((i, event, duration))
        i+=1
        prev = now
window.close()
show(answers)
