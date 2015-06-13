#! /usr/bin/env python

# Jenkins monitor in terminal based on the curses library
# Author: Marius Herring

import curses
import urllib2
import base64
import sys
import time
import traceback

def createHeader():

	header = "Curses Jenkins"
	headerPos = (x/2) - 7

	myscreen.addstr(0, headerPos, header,curses.color_pair(1))

def noticeInteractiveMode(focusRow):

	if focusRow == -1:
		myscreen.addstr(1, 1, " " * (x-2), curses.color_pair(1))
	else:
		headerPos = (x/2) - 8
		myscreen.addstr(1, 1, " " * (x-2), curses.color_pair(7))
		myscreen.addstr(1, headerPos, "Interactive mode",curses.color_pair(7))


def init():

	global myscreen, x, y, links

	myscreen = curses.initscr()
	myscreen.border(0)
	curses.curs_set(0);
	curses.noecho()

	links = {}

	y,x = myscreen.getmaxyx();

	defineColors();

def defineColors():

	curses.start_color()
	curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
	curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
	curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
	curses.init_pair(4, curses.COLOR_CYAN, curses.COLOR_BLACK)
	curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
	curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
	curses.init_pair(7, curses.COLOR_BLACK, curses.COLOR_RED)
	curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)

	curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_CYAN)
	curses.init_pair(12, curses.COLOR_BLACK, curses.COLOR_CYAN)
	curses.init_pair(13, curses.COLOR_BLACK, curses.COLOR_CYAN)
	curses.init_pair(14, curses.COLOR_BLACK, curses.COLOR_CYAN)
	curses.init_pair(15, curses.COLOR_BLACK, curses.COLOR_CYAN)
	curses.init_pair(16, curses.COLOR_BLACK, curses.COLOR_CYAN)

def displayGui():

	count = 1

	try:
		while 1:

			drawScreen(count, -1)

			if count < 6:
				count += 1
			else:
				count = 1

			time.sleep(1)

	except (SystemExit, Exception):
		curses.endwin()
		print traceback.format_exc()
		sys.exit(0)
	except (KeyboardInterrupt):
		interactiveLoop()

def interactiveLoop():
	focusRow = 4
	try:
		myscreen.nodelay(1)
		drawScreen(1,focusRow)
		while 1:
			c = myscreen.getch()
			q = c
			if c == ord('w'):
				if focusRow > 4:
					focusRow = focusRow - 1
					drawScreen(1,focusRow)
			if c == ord('s'):
				if focusRow < y-1:
					focusRow = focusRow + 1
					drawScreen(1,focusRow)
			if c == ord('m'):
				displayGui()
				curses.endwin()
				sys.exit(0)
			if c == ord('b'):
				build(focusRow)
				displayGui()
				curses.endwin()
				sys.exit(0)
			time.sleep(0.1)

	except (SystemExit, Exception):
		curses.endwin()
		print traceback.format_exc()
		sys.exit(0)
	except (KeyboardInterrupt):
		curses.endwin()
		sys.exit(0)

def drawScreen(count, focusRow):
	row = 1

	createHeader()
	noticeInteractiveMode(focusRow)

	argumentNr = 3

	while argumentNr < len(sys.argv):

		row = readData(count, argumentNr, row, focusRow)

		if argumentNr < (len(sys.argv)-1):
			myscreen.addstr(row, 1, "-" * (x-2))
			row += 1

		argumentNr += 1

	myscreen.refresh()

def readData(count, argumentNr, row, focusRow):

	data = eval(urllib2.urlopen(str(sys.argv[argumentNr]) + "/api/python?depth=1&pretty=true").read());

	row += 1

	if windowToSmallToWriteIn(row):
		return row;

	addDescription(data["description"], row);
	row += 2

	for current in data["jobs"]:

		if windowToSmallToWriteIn(row):
			break;

		nameToDisplay = current["name"].strip()
		color = current["color"].strip()
		colorCode = getColorCode(color)
		colorCode = adjustColor(colorCode, row, focusRow)

		links[row] = current["url"]

		cleanLine(row, focusRow)

		addHealthReport(current, row, focusRow)

		myscreen.addstr(row, 16, nameToDisplay, curses.color_pair(colorCode))

		addStructure(row, focusRow)

		addProgressBar(count, row, nameToDisplay, color, focusRow)

		createStatus(row, color, row, focusRow)

		addQuitInstructions(y, focusRow)

		row += 1

	row += 1;
	return row

def addStructure(row, focusRow):
	myscreen.addstr(row, 49, "[", curses.color_pair(adjustColor(1, row, focusRow)))
	myscreen.addstr(row, 56, "]", curses.color_pair(adjustColor(1, row, focusRow)))

def cleanLine(row, focusRow):
	myscreen.addstr(row, 1, " " * (x-2), curses.color_pair(adjustColor(1, row, focusRow)))

def addHealthReport(current, row, focusRow):

	if x > 119:
		myscreen.addstr(row, 58, " " * (x-59), curses.color_pair(adjustColor(4, row, focusRow)))
		myscreen.addstr(row, 58, current["healthReport"][0]["description"], curses.color_pair(adjustColor(4, row, focusRow)))

def addDescription(description, row):

	# Set standard description if jenkins doesn't have any
	if description is None:
		description = "Jenkins"

	# We just allow 1 line of description
	description = description.split('\n')[0]

	# If description is to long, cut of parts of the end
	if (x-2) < len(description):
		description = description[:(x-10)]
		description += " (...)"

	myscreen.addstr(row, 2, description, curses.color_pair(1))

def addProgressBar(count, row, nameToDisplay, color, focusRow):

	if "anime" in color:
		progressBar = createProgressBar(count);
		myscreen.addstr(row, 50, progressBar, curses.color_pair(adjustColor(3, row, focusRow)))
	else:
		myscreen.addstr(row, 50, " " * 6, curses.color_pair(adjustColor(3, row, focusRow)))

def createProgressBar(count):

	result = "|" * count
	space = " " * (6-count)
	result = result+space
	return result

def addQuitInstructions(y, focusRow):
	if focusRow == -1:
		myscreen.addstr(y-2, 1, " " * (x-2), curses.color_pair(1))
		myscreen.addstr(y-2, 2, "Press ctrl+C to interact!")
	else:
		myscreen.addstr(y-2, 1, " " * (x-2), curses.color_pair(8))
		myscreen.addstr(y-2, 2, "ctrl+C: quit | w: up | s: down | b: build | m: monitor",curses.color_pair(8))

def windowToSmallToWriteIn(row):

	if row >= (y-3):
		if x > 50:
			myscreen.addstr(y-2, 23, " (Can't show all data. To small window)", curses.color_pair(6))
		else:
			myscreen.addstr(y-3, 2, "(Can't show all data. To small window)", curses.color_pair(6))
		return 1

	return 0

def createStatus(y, color, row, focusRow):

	if "blue" in color:
		myscreen.addstr(y, 2, "      [ OK ]", curses.color_pair(adjustColor(2, row, focusRow)))
	elif "disabled" in color:
		myscreen.addstr(y, 2, "[ DISABLED ]", curses.color_pair(adjustColor(4, row, focusRow)))
	elif "yellow" in color:
		myscreen.addstr(y, 2, "[ UNSTABLE ]", curses.color_pair(adjustColor(5, row, focusRow)))
	elif "red":
		myscreen.addstr(y, 2, "  [ FAILED ]", curses.color_pair(adjustColor(6, row, focusRow)))

def getColorCode(color):

	if "blue" in color:
		return 2
	elif "disabled" in color:
		return 4
	elif "yellow" in color:
		return 5
	elif "red":
		return 6

def build(focusRow):
	if focusRow in links.keys():
		request = urllib2.Request(links[focusRow] + "/build/")
		base64string = base64.encodestring('%s:%s' % (sys.argv[1], sys.argv[2])).replace('\n', '')
		request.add_header("Authorization", "Basic %s" % base64string)
		urllib2.urlopen(request, data="");

def adjustColor(colorCode, row, focusRow):

	if focusRow == row:
		return colorCode + 10
	else:
		return colorCode

if len(sys.argv) < 4:
	print("ERROR: Wrong nr of parameter")
	print("  Usage: ./cjenkins.py <username> <password> <pathToJenkins>")
	exit(1)

init();

displayGui()
