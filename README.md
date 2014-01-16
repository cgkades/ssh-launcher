ssh-launcher
============

SSH launcher to be used inside screen or tmux


This ssh launcher uses your known_hosts file to get it's list. launcher.py will launch new sessions in a new tmux or screen window.


Usage:

'reload' to reload keys
'exit' or 'quit' to.... do what it spells....

When typing it will auto-complete. You can then hit the down arrow at any time and select either tab to go back up and it will fill the line with the hostname, enter will ssh directly to the host. Hitting a letter will stop the selection and add that letter to the hostname above. backspace will exit the selection and backspace a char.

Ctrl-h will give you history
up will display your last history
enter with nothign entered will launch an ssh session with your most recient entry
Ctrl-c or escape will clear

