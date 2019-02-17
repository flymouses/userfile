#! python3
import pyautogui, sys
while True:
    title = input('please type tile:')
    try:
        win = pyautogui.getWindow(title)
    except Exception:
        print('wrong title {}'.format(title))
    else:
        break
print('Press Ctrl-C to quit.')
try:
    while True:
        x, y = pyautogui.position()
        positionStr = 'X: ' + str(x).rjust(4) + ' Y: ' + str(y).rjust(4)
        pos = win.get_position()
        left, top, _, _ = pos
        positionStr += ' <Win {} {}> REL ({}, {})'.format(title, pos, x-left, y-top)
        print(positionStr, end='')
        print('\b' * len(positionStr), end='', flush=True)
except KeyboardInterrupt:
    print('\n')