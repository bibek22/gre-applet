#!/usr/bin/env python
import PySimpleGUI as sg
import subprocess
import time
from multiprocessing import Process

sg.theme('DarkGreen2')
record = []
answers = []
prev = time.time()
font = 'Monospace 20'
font_small = 'Monospace 10'
ht = 1
w = 6
i = 1
all_text = ""


def sec2time(secs):
    time = str(secs // 60) + ":" + "{:02d}".format(secs % 60)
    return (time)


def timer():
    # Timer
    field_timer = sg.Text(f"0:00",
                          size=(w, 2),
                          font=font,
                          justification='center')
    layout_timer = [[field_timer]]
    window_timer = sg.Window('timer', layout_timer, finalize=True)

    duration = 0
    while True:
        print(duration)
        time.sleep(1)
        duration += 1
        label = sec2time(duration)
        print(label)
        field_timer.Update(label)


#  timerp = Process(target=timer)
#  timerp.start()


def printm(text, **kwargs):
    global all_text
    print(text, **kwargs)
    all_text += "\n" + text


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
        return (time)

    def update_time(self, time):
        if self.time:
            self.time += time
        else:
            self.time = time


class Section(object):
    """collection of Responses"""
    def __init__(self):
        self.questions = []
        self.critical_time = 102
        self.keys = None

    def add_question(self, qn):
        new = Response(qn)
        self.questions.append(new)
        return (new)

    def read_answers(self):
        # get rid of the last question right away
        del self.questions[-1]
        print(f"total responses: {len(self.questions)}")
        self.keys = input("Answers: ").strip().replace(" ", "").upper()
        total_keys = len(self.keys)
        for i, q in enumerate(self.questions):
            #  if not q.answer: del self.questions[i]
            if q.qn > total_keys:
                printm("\n!!! Not all answerkeys read")
                break
            q.key = self.keys[q.qn - 1]

    def prepare_result(self):
        for q in self.questions:
            if not q.answer: continue
            if q.answer == q.key:
                q.result = 1
            else:
                q.result = 0

    def _print_banner(self, headers):
        banner = "\t".join(headers)
        length = len(banner) + 1
        printm("\n" + "=" * length)
        printm(banner)
        printm("-" * length)

    def show_response(self):
        self._print_banner(["Qn.", "Ans.", "Time"])
        for q in self.questions:
            printm("%s\t%s\t%s" % (q.qn, q.answer, q.get_duration()))

    def show_result(self):
        self._print_banner(["Qn.", "Answer", "Time"])
        for q in self.questions:
            if q.result:
                printm("%s\t%s \t\t%s" % (q.qn, q.answer, q.get_duration()))
            else:
                printm("%s\t%s(%s)\t%s" %
                       (q.qn, q.answer, q.key, q.get_duration()))

    def report_time(self):
        ct = input(f"\nTime threshold ({section.critical_time}s): ").strip()
        if ct:
            try:
                self.critical_time = int(ct)
            except:
                print("Default understood.")
        else:
            printm("Default understood.")
        critical = []
        for q in self.questions:
            if q.time > self.critical_time:
                critical.append(self.questions.index(q))
        if not critical:
            printm("Congratutions, All on time!")
        else:
            printm("Following questions took too long:")
            self._print_banner(["Qn.", "Result", "Time"])
            for i in critical:
                q = self.questions[i]
                #    לּ ﬽✘
                #  result = ":)" if q.result else ":("
                result = "" if q.result else "✘"
                printm(f"{q.qn}\t{result}\t\t{q.get_duration()}")

    def finalize(self):
        self.read_answers()
        self.prepare_result()
        self.show_result()
        self.report_time()

    def get_qn(self, num):
        for q in self.questions:
            if q.qn == num:
                return(q)
        return(None)


    def qexists(self, num):
        for q in self.questions:
            if q.qn == num:
                return(True)
        return(False)


field = sg.Text(f"Q: {i}".center(8), size=(w+1, 2), font=font, justification='center')
options = ["A", "B", "C", "D", "E", "F", "G"]
nav_options = ["Prev", "Next"]
option_buttons = [
    sg.Button(label, size=(w, ht), font=font) for label in options
]
layout = [
    [field], [option_buttons[0]], [option_buttons[1]], [option_buttons[2]],
    [option_buttons[3]], [option_buttons[4]], [option_buttons[5]],
    [option_buttons[6]],
    [sg.Button(label, size=(w//2+1, ht), font=font_small) for label in nav_options]
]

# create a section object
section = Section()
# Create the Window
window = sg.Window('record', layout, finalize=True)

# Event Loop to process "events" and get the "values" of the inputs

question = section.add_question(i)
while True:
    if question.answer:
        field.Update(f"Q:{i}[{question.answer}]".center(7))
    else:
        field.Update(f"Q:{i} ".center(7))
    event, values = window.read()
    now = time.time()
    if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
        break
    if event in options:
        question.answer = event
        continue # so as to not reset the time counter
    if event in nav_options[0]:
        question.update_time(int(now - prev))
        if ( i != 1 ):
            i -= 1
            question = section.get_qn(i)
    elif event in nav_options[1]:
        question.update_time(int(now - prev))
        i += 1
        if section.qexists(i):
            question = section.get_qn(i)
        else:
            question = section.add_question(i)

    prev = now

window.close()
section.finalize()
name = input("filename: ")
if not name: exit()
with open(f"./{name}", "w+") as f:
    f.writelines(all_text)
print("saved.")
