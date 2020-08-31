#!/usr/bin/env python
## Author : Bibek Gautam
## Date	  : Sat Aug 29 2020
## LICENSE: GPL-3

import PySimpleGUI as sg
import subprocess
import time
import re
#  from multiprocessing import Process

sg.theme('DarkGreen2')
font = 'Monospace 20'
font_small = 'Monospace 15'
ht = i = 1
w = 5
all_text = ""


def sec2time(secs):
    time = str(secs // 60) + ":" + "{:02d}".format(secs % 60)
    return (time)


def timer():
    field_timer = sg.Text(f"0:00",
                          size=(w, 2),
                          font=font,
                          justification='center')
    layout_timer = [[field_timer]]
    window_timer = sg.Window('timer',
                             layout_timer,
                             finalize=True,
                             grab_anywhere=True,
                             no_titlebar=True)
    duration = 0
    while True:
        print(duration)
        time.sleep(1)
        duration += 1
        label = sec2time(duration)
        print(label)
        field_timer.Update(label)


def printm(text, nonewline=0):
    global all_text
    if nonewline:
        all_text += text
    else:
        all_text += "\n" + text


class Question(object):
    """response object ie. answer from test taker"""
    def __init__(self, qn):
        self.qn = qn
        self.answer = None
        self.input = ""
        self.time = None
        self.key = None
        self.result = None

    def get_duration(self):
        secs = round(self.time)
        time = str(secs // 60) + ":" + "{:02d}".format(secs % 60)
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
        # Time spent on unanswered questions, which is otherwise unaccounted
        self.leaked_time = 0
        self.total_time = 0
        self.furthest = 0  # the highest question number with a response
        self._pat = re.compile(r"\(.*?\)")

    def add_question(self, qn):
        if self.furthest < qn:
            self.furthest = qn
        new = Question(qn)
        self.questions.append(new)
        return (new)

    def read_answers_cli(self, answer=""):
        # get rid of the last question right away
        #  del self.questions[-1]
        if not answer:
            print(f"total responses: {len(self.questions)}")
            answer = input("Answers: ")
        self.keys = answer.strip().replace(" ", "").upper()

    def read_answers_gui(self):
        prompt = sg.Text(f'Answer keys: (0/{self.furthest})',
                         font=font,
                         size=(50, 1))
        time_field = sg.Input(key='time_threshold', font=font, size=(5, 10))
        answers_field = sg.Input(key='answers', font=font, enable_events=True)
        layout = [
            [prompt],
            [answers_field],
            [sg.Text('Time Threshold: ', font=font)],
            [time_field],
            [sg.Button("Submit", font=font)],
        ]
        window = sg.Window('GRE', layout, finalize=True)
        time_field.Update(self.critical_time)
        while True:
            event, value = window.read()
            if event in ['Submit', 'Close']:
                break
            else:
                answers_field.Update(value['answers'].upper())
                keys = re.sub(r"\(.*?\)", "_",
                              value['answers'].replace(" ", "").strip())
                n = len(keys)
                prompt.Update(f"Answer keys: ({n}/{self.furthest})")

        window.close()
        self.keys = value['answers'].strip().replace(" ", "").upper()
        ct = value['time_threshold']
        if ct:
            try:
                self.critical_time = int(ct)
            except:
                print("Default understood.")
        else:
            print("Default understood.")

    def show_result_gui(self):
        mline = sg.MLine(key="report", font=font_small, size=(40, 20))
        layout = [
            [
                sg.Text('Results are in!',
                        justification='center',
                        font=font,
                        size=(30, 1))
            ],
            [mline],
            [sg.Text('save: ', font=font)],
            [sg.Input(key='name', font=font_small, size=(40, 1))],
            [sg.Button("Save and Exit", font=font)],
        ]
        window = sg.Window('GRE', layout, finalize=True)
        mline.print(all_text)
        event, value = window.read()
        if not value['name']: exit()
        with open(f"./{value['name']}", "w+") as f:
            f.writelines(value['report'])
        window.close()

    def prepare_result(self):
        # put in place (key)
        shift = 0
        match = self._pat.finditer(self.keys)
        for m in match:
            index = m.start() - shift
            self.questions[index].key = m.group(0)[1:-1]
            shift += m.end() - m.start() - 1
        self.keys = re.sub(r"\(.*?\)", "_", self.keys)
        total_keys = len(self.keys)

        # put in place (answer)
        for i, q in enumerate(self.questions):
            if not q.answer:
                q.answer = q.input
            if q.qn > total_keys:
                print("\n!!! Not all answerkeys read")
                break
            if self.keys[q.qn - 1] == "_":
                pass
            else:
                q.key = self.keys[q.qn - 1]

            # RESULT
            if not q.answer: continue
            if q.answer == q.key:
                q.result = 1
            else:
                q.result = 0

    def tabulate(self, rows, headers):
        delim = "    "
        banner = delim.join(headers)
        length = len(banner)
        printm("\n" + "=" * length)
        printm(banner)
        printm("-" * length)
        for row in rows:
            printm(row[0].center(len(headers[0])) + delim, nonewline=0)
            printm(row[1].ljust(len(headers[1])) + delim, nonewline=1)
            printm(row[2].rjust(len(headers[2])), nonewline=1)

    def purge_questions(self):
        #  print(f"purge\n{len(self.questions)}")
        while True:
            if (not self.questions[-1].answer) and (
                    not self.questions[-1].input):
                self.furthest -= 1
                self.leaked_time += self.questions[-1].time
                del self.questions[-1]
            else:
                break

    def show_response(self):
        self._print_banner(["Qn.", "Ans.", "Time"])
        for q in self.questions:
            printm("%s\t%s\t%s" % (q.qn, q.answer, q.get_duration()))

    def show_result(self):
        printm(f"total time: {sec2time(self.total_time)}")
        header = ["Qn.", "Answer(Correct)", "Time"]
        rows = []
        for q in self.questions:
            answer = q.answer if q.answer else "-"
            if q.result:
                rows.append([str(q.qn), q.answer + " ", q.get_duration()])
            else:
                rows.append(
                    [str(q.qn), answer + "(" + q.key + ")",
                     q.get_duration()])
        self.tabulate(rows, header)

    def report_time(self):
        critical = []
        for q in self.questions:
            if q.time > self.critical_time:
                critical.append(self.questions.index(q))
        if not critical:
            printm("\nCongratutions, All on time!")
        else:
            header = ["Qn.", "Result", "Time"]
            rows = []
            printm("\nFollowing questions took too long:\n")
            for i in critical:
                q = self.questions[i]
                #    לּ ﬽✘
                result = "" if q.result else "✘"
                rows.append([str(q.qn), result, q.get_duration()])
            self.tabulate(rows, header)

    def finalize(self):
        self.purge_questions()
        self.read_answers_gui()
        self.prepare_result()
        self.show_result()
        self.report_time()
        self.show_result_gui()

    def get_qn(self, num):
        for q in self.questions:
            if q.qn == num:
                return (q)
        return (None)

    def qexists(self, num):
        for q in self.questions:
            if q.qn == num:
                return (True)
        return (False)


field = sg.Text(f" Q: {i}".center(w),
                size=(w + 1, 2),
                font=font,
                justification='center')
answer_input = sg.Input(key='answer',
                        size=(w + 1, ht),
                        justification='c',
                        font=font,
                        enable_events=True)
options = ["A", "B", "C", "D", "E", "F", "G"]
close = sg.Button("Done", size=(w, ht), font=font)
nav_options = ["<<", ">>"]
#  flag_checkbox = sg.Checkbox('⚑', font=font_small)
option_buttons = [
    sg.Button(label, size=(w, ht), font=font) for label in options
]

layout = [
    [field],
    #  [flag_checkbox],
    [answer_input],
    [sg.Button(label, font=font_small) for label in nav_options],
    [option_buttons[0]],
    [option_buttons[1]],
    [option_buttons[2]],
    [option_buttons[3]],
    [option_buttons[4]],
    [option_buttons[5]],
    [option_buttons[6]],
    [close]
]

# create a section object
section = Section()
# Create the Window
window = sg.Window(
    'GRE',
    layout,
    finalize=True,
    location=(1366 - 50, 760 // 2 - 120),
    #  no_titlebar=True,
    alpha_channel=0.95,
    #  grab_anywhere=True,
    return_keyboard_events=True)

# preparation for the main loop
start_time = prev = time.time()
question = section.add_question(i)
# Event Loop to process "events" and get the "values" of the inputs
while True:
    # don't update answer_input anywhere below
    # update question.input instead
    answer_input.Update(question.input)
    if question.answer:
        field.Update(f"Q:{i}")
    else:
        field.Update(f"Q:{i}")
    win, event, values = sg.read_all_windows()
    if "Return" in event:
        event = ">>"
    now = time.time()
    if event == "answer":
        question.answer = None
        question.input = values['answer'].upper().strip()
    # Closing window
    if event == sg.WIN_CLOSED or event == 'Done':  # if user closes window or clicks cancel
        question.update_time(now - prev)
        section.purge_questions()
        section.total_time = int(now - start_time)
        break
    # For buttons
    if event in options:
        question.answer = event
        question.input = event
        continue  # so as to not reset the time counter
    # For navigation
    if event in nav_options[0]:
        question.update_time(now - prev)
        if (i != 1):
            i -= 1
            question = section.get_qn(i)
        prev = now
    elif event in nav_options[1]:
        question.update_time(now - prev)
        i += 1
        if section.qexists(i):
            question = section.get_qn(i)
        else:
            question = section.add_question(i)
        prev = now

window.close()
section.finalize()
