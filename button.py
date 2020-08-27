#!/usr/bin/env python
import PySimpleGUI as sg
import subprocess
import time
from multiprocessing import Process

record = []
answers = []
prev = time.time()
font='Monospace 20'
ht = 1
w = 6
i = 1

class Response(object):

    """response object ie. answer from test taker"""

    def __init__(self, qn):
        self.qn = qn
        self.answer = None
        self.time = None
        self.key = None
        self.result = None

    def get_duration(self):
        time = str(self.time // 60) + ":" + "{:02d}".format(self.time % 60)
        return(time)


class Section(object):

    """collection of responses"""

    def __init__(self):
        self.questions = []
        self.critical_time = 142
        self.keys = None

    def add_question(self, qn):
        new = Response(qn)
        self.questions.append(new)
        return(new)

    def read_answers(self):
        # get rid of the last question right away
        del self.questions[-1]
        print(f"total responses: {len(self.questions)}")
        self.keys = input("Answers: ").strip().replace(" ", "").upper()
        total_keys = len(self.keys)
        for i, q in enumerate(self.questions):
            #  if not q.answer: del self.questions[i]
            if q.qn > total_keys: print("not all answerkeys read..."); break
            q.key = self.keys[q.qn-1]
        
    def prepare_result(self):
        for q in self.questions:
            if not q.answer: continue
            if q.answer == q.key:
                q.result = 1
            else:
                q.result = 0

    def show_response(self):
        banner = "Qn.\tAns.\tTime"
        print("\n" + "="*len(banner))
        print(banner)
        print("-"*len(banner))
        for q in self.questions:
            print("%s\t%s\t%s" % (q.qn, q.answer, q.get_duration()))


    def show_result(self):
        banner = "Qn.\tAnswer\tTime"
        print("\n" + "="*len(banner))
        print(banner)
        print("-"*len(banner))
        for q in self.questions:
            if q.result:
                print("%s\t%s\t\t%s" % (q.qn, q.answer, q.get_duration()))
            else:
                print("%s\t%s(%s)\t%s" % (q.qn, q.answer, q.key, q.get_duration()))


def show(responses):
    banner = "Qn.\tAns\tTime"
    print("\n" + "="*len(banner))
    print(banner)
    print("-"*len(banner))
    for item in responses:
        print("%s\t%s\t%s" % item)

def read_answers():
    answers = input("Answers: ").strip().replace(" ", "")
    return answers
    

sg.theme('DarkGreen2')	# Add a touch of color
# All the stuff inside your window.
field = sg.Text(f" Qn: {i}", size=(w, 2), font=font, justification='center')
options = ["A", "B", "C", "D", "E", "F", "G"]
option_buttons = [sg.Button(label, size=(w, ht), font=font) for label in options]
layout = [ 
        [field],
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

# create a section object
section = Section()
# Create the Window
window = sg.Window('record', layout, finalize=True)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    question = section.add_question(i)
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == 'Cancel':# if user closes window or clicks cancel
        break
    if event in options:
        now = time.time() 
        question.time = int(now - prev)
        question.answer = event
        i+=1
        field.Update(f" Qn: {i}")
        prev = now

window.close()
section.read_answers()
section.prepare_result()
section.show_result()
#  section.show_response()
