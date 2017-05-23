#!/bin/bash
""":"
PY_VERSIONS="2.6 2.7"
PY_BINS="python python26 python27"

for p in $PY_BINS; do
  if ! which $p >/dev/null 2>&1; then continue; fi

  VER=$($p --version 2>&1)

  for v in $PY_VERSIONS; do
    if echo $VER | grep -i "python $v" >/dev/null 2>&1 ; then
      exec $p $0; exit
    fi
  done
done
echo "No supported python interpreter found.  Requires one of version $PY_VERSION"
exit
":"""


import curses
import signal
import re
import os
import time

CLEAR = 0
try:
    TMUX = os.environ['TMUX']
except:
    TMUX = 'no'
try:
    SCREEN = os.environ['STY']
except:
    SCREEN = 'no'

def signal_handler(signal, frame):
    global CLEAR
    CLEAR = 1
    #curses.nocbreak(); curses.echo ()
    #curses.endwin()

def launch_ssh(hostname):
    title = hostname[:hostname.find(' ')]
    if TMUX != 'no':
        os.system("tmux new-window -n %s 'ssh -q %s'" % (title,hostname))
    elif SCREEN != 'no':
        os.system("/usr/bin/screen -x %s -X screen -t %s ssh %s" % (SCREEN,hostname,hostname))

def delete_key(hostname):
    PATH = os.environ['HOME'] + '/.ssh/known_hosts'
    if os.path.exists(PATH):
        f = open(PATH)
        lines = f.readlines()
        f.close()
        loc = -1
        for i in range(0,len(lines) -1):
            if lines[i].find(hostname) > -1:
                loc = i
        if loc > -1:
            lines.remove(lines[loc])
            f = open(PATH,'w')
            for i in lines:
                f.write(i)
            f.close()


def load_hosts():
    hosts = []
    if os.path.exists(os.environ['HOME']+ '/.ssh/known_hosts'):
        f = open(os.environ['HOME']+ '/.ssh/known_hosts')
        lines = f.readlines()
        f.close()
        for i in lines:
            hosts.append(i.split(' ')[0].split(',')[0])
    return hosts

def list_matches(match_string,hosts_array):
    matches_array = []
    commands = ['exit','quit','reload']
    for i in hosts_array + commands:
        if i.find(match_string[match_string.find('@') + 1:]) >= 0:
            matches_array.append(i)
    return matches_array

def print_autocomplete(curses_window,print_array):
    height, width = curses_window.getmaxyx()
    curses_window.erase()
    curses_window.refresh()
    xlocation = 3
    ylocation = 0
    for i in print_array:
        curses_window.addstr(ylocation,xlocation, "   | " + i)
        ylocation += 1
        if ylocation >= height - 2:
            curses_window.refresh()
            return print_array
    curses_window.refresh()
    return print_array

def autocomplete_select(curses_window,length_hosts,stdscr):
    select_mode = 1
    yloc = 0
    xloc = 4
    key  = 'None'
    curses_window.addstr(yloc,xloc,'>')
    curses_window.refresh()
    height, width = curses_window.getmaxyx()
    while select_mode:
        c = stdscr.getch()
        if c > 30 and c < 256 and c != 127:
            res = re.match('^[a-z0-9-\.@]',chr(c))
            if res != None:
                key = 'alpha'
                select_mode = 0
                curses_window.addstr(yloc,xloc,' ')
                return [key,c]
        elif c == curses.KEY_ENTER or c == 10:
            select_mode = 0
            key = 'enter'
        elif c == curses.KEY_UP and yloc > 0:
            curses_window.addstr(yloc,xloc,' ')
            yloc -= 1
            curses_window.addstr(yloc,xloc,'>')
            curses_window.refresh()
        elif c == curses.KEY_DOWN and yloc < (length_hosts -1) and yloc < (height-1):
            curses_window.addstr(yloc,xloc,' ')
            yloc += 1
            curses_window.addstr(yloc,xloc,'>')
            curses_window.refresh()
        elif c == 9:
            key = 'tab'
            select_mode = 0
        elif (c == curses.KEY_UP and yloc == 0) or  c == 27:
            key = 'escape'
            select_mode = 0
        elif c == 330:
            key = 'del'
            select_mode = 0
        elif c == curses.KEY_BACKSPACE or c == 127:
            key = 'backspace'
            select_mode = 0
        elif c == curses.KEY_RESIZE:
            key = 'resize'
            select_mode = 0
    curses_window.addstr(yloc,xloc,' ')
    return [key,yloc]

def draw_background(stdscr):
    message = "== SSH Launcher =="
    #stdscr.border(0)
    height, width = stdscr.getmaxyx()
    i = 1
    while i < width - 1:
        stdscr.addstr(height - 3,i,'-')
        i += 1
    message_start_location = int(width/2) - int((len(message)/2))
    stdscr.addstr(height - 2,message_start_location,message)
    i = 1
    while i < width - 1:
        stdscr.addstr(3,i,'-')
        i += 1
    time_date = time.localtime()
    time_string = "%s:%s:%s %s/%s/%s" % (time_date[3]if time_date[3] > 9 else "0" + str(time_date[3]) ,time_date[4]if time_date[4] > 9 else "0" + str(time_date[4]) , time_date[5] if time_date[5] > 9 else "0" + str(time_date[5]) ,time_date[1] if time_date[1] > 9 else "0" + str(time_date[1]) ,time_date[2]if time_date[2] > 9 else "0" + str(time_date[2]) ,time_date[0])
    stdscr.addstr(height - 2, width - 2 - len(time_string),time_string )
    #stdscr.refresh()

def display_lastssh(stdscr, hostname):
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.border(0)
    stdscr.refresh()
    stdscr.addstr(height - 2, 2,"Last ssh: " + hostname)

    draw_background(stdscr)


def history_selection(window,history_list,location):
    hostname = ''
    PREFIX = "Connect to: "
    if len(history_list) < 0:
        return
    else:
        window.keypad(1)
        #running = 1
        hostname_location = location
        window.move(1, len(history_list[hostname_location]) + 1)
        hostname = history_list[hostname_location]
        window.addstr(1,len(PREFIX) + 1,hostname)
        window.refresh()

    return hostname

def resize(window1,window2,stdscr,auto_hosts):
    height, width = stdscr.getmaxyx()
    stdscr.erase()
    stdscr.border(0)
    stdscr.refresh()
    draw_background(stdscr)
    window1.resize(3, width -2)
    window1.erase()
    window2.resize(height - 6,width - 2)
    window2.erase()
    window2.refresh()
    print_autocomplete(window2,auto_hosts)
    window2.refresh()

def main():
    global CLEAR
    PREFIX = "Connect to: "
    history = []
    history_location = 0
    auto_hosts = []
    hosts = load_hosts()
    stdscr = curses.initscr()
    #curses.start_color()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(1)
    #set the the getch to nonblocking with a .1 sec wait
    curses.halfdelay(1)
    stdscr.border(0)
    height, width = stdscr.getmaxyx()
    window1 = curses.newwin(3,width - 2,1,1)
    window2 = curses.newwin(height - 6,width - 2, 4,1)
    xloc = len(PREFIX) + 1
    buff = ""
    draw_background(stdscr)
    while 1:
        signal.signal(signal.SIGINT, signal_handler)
        ##### Window managemnt and key capture #####
        height, width = stdscr.getmaxyx()

        window1.addstr(1,1,PREFIX)
        #window1.box()
        #if len(buff) > 0:
        #	print_autocomplete(window2,auto_hosts)
        draw_background(stdscr)
        window1.addstr(1,len(PREFIX) + 1,buff)
        #window2.refresh()
        window1.refresh()
        stdscr.refresh()
        stdscr.move(2,xloc + 1)
        c = stdscr.getch()
        #Character Recognization
        if CLEAR == 1:
            CLEAR = 0
            c = 27
        if (c == curses.KEY_DOWN and len(auto_hosts) > 0 and len(buff)) or (c == 8 and len(history) > 0):
            array = []
            if c == 8 and len(history) > 0:
                window2.erase()
                window2.refresh()
                array = history[::-1]
                print_autocomplete(window2,history[::-1])
                complete_loc = autocomplete_select(window2,len(array),stdscr)
            else:
                array = auto_hosts
                complete_loc = autocomplete_select(window2,len(array),stdscr)
            if complete_loc[1] >= 0 and complete_loc[0] == 'tab':
                window1.erase()
                buff = buff[:buff.find('@') + 1] + array[complete_loc[1]]
                window1.addstr(1,len(PREFIX) + 1,buff)
                window1.refresh()
                xloc = len(buff) + len(PREFIX) + 1
                window2.erase()
                window2.refresh()
                array = list_matches(buff,hosts)
                print_autocomplete(window2,array)
                auto_hosts = array
            elif complete_loc[0] == 'enter':
                buff = buff[:buff.find('@') + 1] + array[complete_loc[1]]
                # os.system("tmux new-window -n %s 'ssh %s'" % (buff,buff))
                if buff.lower() == "exit" or buff.lower() == "quit":
                    break
                elif buff.lower() == "reload":
                    hosts = load_hosts()
                    buff = ""
                    xloc = len(PREFIX) + 1
                    window1.erase()
                    window1.refresh()
                    window2.erase()
                    window2.refresh()
                    draw_background(stdscr)
                else:
                    history.append(buff)
                    display_lastssh(stdscr,buff)
                    launch_ssh(buff)
                    buff = ""
                    xloc = len(PREFIX) + 1
                    window1.erase()
                    window1.refresh()
                    auto_hosts = []
                    window2.erase()
                    window2.refresh()
                    draw_background(stdscr)
            elif complete_loc[0] == 'alpha':
                c = complete_loc[1]
                window1.addstr(1,xloc,chr(complete_loc[1]))
                xloc += 1
                buff = buff + chr(complete_loc[1])
                window1.refresh()
                array = list_matches(buff,hosts)
                print_autocomplete(window2,array)
            elif complete_loc[0] == 'del':
                buff = array[complete_loc[1]]
                delete_key(buff)
                window1.erase()
                window1.refresh()
                window2.erase()
                window2.refresh()
                theight, twidth = stdscr.getmaxyx()
                stdscr.addstr(theight - 2, 1, 'Deleted key for ' + buff)
                buff = ""
                xloc = len(PREFIX) + 1
                draw_background(stdscr)
            elif complete_loc[0] == 'resize':
                c = curses.KEY_RESIZE
                resize(window1,window2,stdscr,auto_hosts)
            elif complete_loc[0] == 'backspace':
                if xloc == len(PREFIX) + 2:
                    xloc -= 1
                    buff = buff[0:-1]
                    window1.addstr(1,xloc," ")
                    window1.refresh()
                    auto_hosts = []
                    draw_background(stdscr)
                    window2.erase()
                    window2.refresh()
                elif xloc > len(PREFIX) + 2:
                    xloc -= 1
                    buff = buff[0:-1]
                    window1.addstr(1,xloc," ")
                    window1.refresh()
                    auto_hosts = list_matches(buff,hosts)
                    print_autocomplete(window2,auto_hosts)
                    draw_background(stdscr)
            CLEAR = 0
        elif c > 30 and c < 256 and c != 127:
            res = re.match('^[a-z0-9-\.@]',chr(c))
            if res != None or c == 32: # 32 is space
                window1.addstr(1,xloc,chr(c))
                xloc += 1
                buff = buff + chr(c)
                window1.refresh()
                auto_hosts = list_matches(buff,hosts)
                print_autocomplete(window2,auto_hosts)
                draw_background(stdscr)
        elif c == 27: #escape key
            buff = ""
            xloc = len(PREFIX) + 1
            window1.erase()
            window1.refresh()
            window2.erase()
            window2.refresh()
            draw_background(stdscr)
        #Special Key recognition
        # c == 8 is for ctrl-h (history)
        elif (c == curses.KEY_BACKSPACE or c == 127) and xloc > len(PREFIX) + 2:
            xloc -= 1
            buff = buff[0:-1]
            window1.addstr(1,xloc," ")
            window1.refresh()
            auto_hosts = list_matches(buff,hosts)
            print_autocomplete(window2,auto_hosts)
            draw_background(stdscr)
        elif (c == curses.KEY_BACKSPACE or c == 127) and xloc == len(PREFIX) + 2:
            xloc -= 1
            buff = buff[0:-1]
            window1.addstr(1,xloc," ")
            window1.refresh()
            auto_hosts = []
            #print_autocomplete(window2,auto_hosts)
            draw_background(stdscr)
            window2.erase()
            window2.refresh()
        elif c == curses.KEY_RESIZE:
            resize(window1,window2,stdscr,auto_hosts)
        elif c == curses.KEY_UP and len(history) > 0:
            h_hostname = history_selection(window1,history,len(history) - 1)
            if len(h_hostname) > 0:
                buff = h_hostname
                xloc = len(h_hostname) + len(PREFIX) + 1
                window1.addstr(1,len(PREFIX) + 1,buff)
                auto_hosts = list_matches(buff,hosts)
                print_autocomplete(window2,auto_hosts)
                draw_background(stdscr)
        elif (c == curses.KEY_ENTER or c == 10):# and len(buff) > 0:
            if len(buff) <= 0:
                if len(history) > 0:
                    launch_ssh(history[len(history) - 1])
                    window1.erase()
                    window2.erase()
                    display_lastssh(stdscr,history[len(history) - 1])
                    buff = ""
                    xloc = len(PREFIX) + 1
                    window1.refresh()
                    window2.refresh()
                    draw_background(stdscr)
            elif buff.lower() == "exit" or buff.lower() == "quit":
                break
            elif buff.lower() == "reload":
                hosts = load_hosts()
                buff = ""
                xloc = len(PREFIX) + 1
                window1.erase()
                window1.refresh()
                window2.erase()
                window2.refresh()
                draw_background(stdscr)
            else:
                launch_ssh(buff)
                window1.erase()
                window2.erase()
                display_lastssh(stdscr,buff)
                history.append(buff)
                buff = ""
                xloc = len(PREFIX) + 1
                window1.refresh()
                window2.refresh()
                draw_background(stdscr)
        elif c == 9: #9 is tab.. curses doesnt seem to have a key_tab
            if len(auto_hosts) > 0:
                window1.erase()
                buff = buff[:buff.find('@') + 1] + auto_hosts[0]
                window1.addstr(1,len(PREFIX) + 1,buff)
                window1.refresh()
                xloc = len(buff) + len(PREFIX) + 1
                auto_hosts = list_matches(buff,hosts)
                print_autocomplete(window2,auto_hosts)
                draw_background(stdscr)
        ##### End window managemnt and key capture #####

if __name__ == "__main__":
    exit_message = ""
    try:
        main()
    except Exception as e:
        exit_message = e.message
    #main()
    curses.nocbreak()
    curses.echo ()
    curses.endwin()
    if len(exit_message) > 0:
        print exit_message
