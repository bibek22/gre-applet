#!/usr/bin/env python3
## Author : Bibek Gautam
## Date	  : Sat Aug 29 2020

import PySimpleGUI as sg
import subprocess
import time
import re
import sys

sg.theme('DarkGreen2')
sg.SetOptions(element_padding=(2, 2))
sg.SetOptions(margins=(0, 4))
if sys.platform == 'darwin':
    font = "Courier"
else:
    font = "Monospace"

fs_big = 20
fs_mid = 15
fs_small = 10
fs_tiny = 10
ht = i = 1
w = 5
all_text = ""


def sec2time(secs):
    time = str(secs // 60) + ":" + "{:02d}".format(secs % 60)
    return (time)

def printm(text, nonewline=0):
    # used to be a wrapper around print. But it just saves
    # texts on a variable now.
    global all_text
    if nonewline:
        all_text += text
    else:
        all_text += "\n" + text

def timer(time, element):
    time = sec2time(int(time))
    element.Update(time)


class Question(object):
    """
    response object ie. answer from test taker

    Attributes:
    qn : int
        Question number
    answer: str
        Answer choosen from 7 options(buttons)
    input: str
        Any input given in the input field.
        answer and input overwrite each other.
    time: float
        Time spent on this question
    key: str
        correct answer for this question from the answer key
        read from the user.
    result: bool
        whether user got this question right.
    flag: bool
        flag the question
    """
    def __init__(self, qn):
        self.qn = qn
        self.answer = None
        self.input = ""
        self.time = 0
        self.key = None
        self.result = None
        self.flag = 0

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
    """
    collection of Responses

    Attributes
    questions: list
        of Question objects
    critical_time: int
        Target time to spend on each question
        spend beyond this and will be reported in the result screen.
        can be changed at the end.
    keys: str
        entirety of answer keys for all questions
        read from user
    leaked_time: float
        this just keeps track of time not accounted for in any questions
        not sure if this is necessary anymore.
    total_time: float
        total time spent on this session
        It's printed on the result screen
    furthest: int
        The furthest one went into the section.
        the greatest `qn` of the question attempted
    _pat : regex compiled object
        pattern to look for as a single answer. 
    """
    def __init__(self):
        self.questions = []
        self.critical_time = 90
        self.keys = None
        # Time spent on unanswered questions, which is otherwise unaccounted
        self.leaked_time = 0
        self.total_time = 0
        self.furthest = 0  # the highest question number with a response
        self._pat = re.compile(r"\(.*?\)")
        self.raw_score = 0

    def add_question(self, qn):
        if self.furthest < qn:
            self.furthest = qn
        new = Question(qn)
        self.questions.append(new)
        return (new)

    def read_answers_gui(self):
        prompt = sg.Text(f"Answer keys: (0/{self.furthest})",
                         font=(font, fs_mid),
                         size=(50, 1))
        time_field = sg.Input(key='time_threshold', font=(font, fs_mid), size=(5, 10))
        answers_field = sg.Input(key='answers', font=(font, fs_mid), enable_events=True)
        layout = [
            [prompt],
            [answers_field],
            [sg.Text('Time Threshold: ', font=(font, fs_mid))],
            [time_field],
            [sg.Button("Submit", font=(font, fs_mid))],
        ]
        window = sg.Window('GRE', layout, finalize=True)
        time_field.Update(self.critical_time)
        while True:
            event, value = window.read()
            if event == sg.WIN_CLOSED or event == 'Submit':
                break
            else:
                answers_field.Update(value['answers'].upper())
                # Inefficient but gets the job done
                self.keys = value['answers'].strip().replace(" ", "").upper()
                ct = value['time_threshold']
                keys = re.sub(r"\(.*?\)", "_", self.keys)
                n = len(keys)
                prompt.Update(f"Answer keys: ({n}/{self.furthest})")
        window.close()

        if ct:
            try:
                self.critical_time = int(ct)
            except:
                print("Proceeding with default time threshold.")
        else:
            print("Proceeding with default time threshold.")

    def show_result_gui(self):
        mline = sg.MLine(key="report", font=(font, fs_mid), size=(40, 20))
        layout = [
            [
                sg.Text('Results are in!',
                        justification='center',
                        font=(font, fs_mid),
                        size=(30, 1))
            ],
            [mline],
            [sg.Text('save: ', font=(font, fs_mid))],
            [sg.Input(key='name', font=(font, fs_mid), size=(40, 1))],
            [sg.Button("Save and Exit", font=(font, fs_mid))],
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
                self.raw_score += 1
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
        printm(f"Total time: {sec2time(self.total_time)}")
        printm(f"Raw score: {self.raw_score}/{self.furthest}")
        header = ["Qn.", "Answer(Correct)", "Time"]
        rows = []
        for q in self.questions:
            answer = q.answer if q.answer else "-"
            if q.result:
                rows.append([str(q.qn), "✓ " + q.answer , q.get_duration()])
            else:
                rows.append(
                    [str(q.qn), "✘ " + answer + "(" + q.key + ")",
                     q.get_duration()])
        self.tabulate(rows, header)

    def report_time(self):
        critical = []
        for q in self.questions:
            if q.time > self.critical_time:
                critical.append(self.questions.index(q))
        if not critical:
            printm("\nCongratutions on the time!")
        else:
            header = ["Qn.", "Result", "Time"]
            rows = []
            printm("\nFollowing questions took too long:")
            for i in critical:
                q = self.questions[i]
                result = "✓" if q.result else "✘"
                rows.append([str(q.qn), result, q.get_duration()])
            self.tabulate(rows, header)

    def finalize(self):
        try:
            self.purge_questions()
            self.read_answers_gui()
            self.prepare_result()
            self.show_result()
            self.report_time()
            self.show_result_gui()
        except Exception as e:
            print(e)
            user_response = []
            for q in self.questions:
                answer = q.answer if q.answer else q.input
                user_response.append(answer)
            logfile = f"./gre-applet-autosave-" + str(time.time())[3:9]
            with open(logfile, "w+") as file:
                file.write("Answers: " + ",".join(user_response))
                if self.keys: file.write("\nKeys: " + self.keys + "\n")
            print(f"Error Occurred.\nLog saved at {logfile}")
            exit()

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


field = sg.Text(f"{i}".center(w),
                size=(w+1, 1),
                font=(font, fs_big),
                justification='center')
timer_field = sg.Text(f"",
                size=(w+1, 1),
                font=(font, fs_tiny),
                justification='center')
answer_input = sg.Input(key='answer',
                        size=(w + 1, ht),
                        justification='c',
                        font=(font, fs_mid),
                        enable_events=True)
options = ["A", "B", "C", "D", "E", "F", "G"]
close = sg.Button("Done", size=(w, ht), font=(font, fs_mid))
timer_check = sg.Checkbox("⏰", default=True, key='timer', font=(font, fs_tiny))
flag_check = sg.Checkbox("🚩", default=True, key="flag", font=(font, fs_tiny))
nav_options = ["<<", ">>"]
option_buttons = [
    sg.Button(label, size=(w, ht), font=(font, fs_mid)) for label in options
]

layout = [
    [field],
    [sg.Text("_"*20, font=(font, 5))],
    [timer_field],
    [timer_check, flag_check],
    [answer_input],
    [sg.Button(label, font=(font, fs_small)) for label in nav_options],
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
    element_justification='center',
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
        field.Update(f"{i}")
    else:
        field.Update(f"{i}")
    event, values = window.Read(timeout=100)
    # Closing window
    if event == sg.WIN_CLOSED or event == 'Done':  # if user closes window or clicks cancel
        question.update_time(now - prev)
        section.purge_questions()
        section.total_time = int(now - start_time)
        break
    if values['timer']:
        if values['flag']:
            timer(question.time + time.time() - prev , timer_field)
        else:
            timer(time.time() - start_time , timer_field)
    else:
        timer_field.Update("")
    if "Return" in event:
        event = ">>"
    now = time.time()
    if event == "answer":
        question.answer = None
        question.input = values['answer'].upper().strip()
    # For buttons
    if event in options:
        question.answer = event
        question.input = event
        continue  # so as to not reset the time counter
    # For navigation
    if event in nav_options[0]:
        question.flag = values['flag']
        question.update_time(now - prev)
        if (i != 1):
            i -= 1
            question = section.get_qn(i)
        prev = now
    elif event in nav_options[1]:
        question.flag = values['flag']
        question.update_time(now - prev)
        i += 1
        if section.qexists(i):
            question = section.get_qn(i)
        else:
            question = section.add_question(i)
        prev = now

window.close()
section.finalize()
