from pynput.keyboard import Key, Listener
from pynput import keyboard
import socket
import sys

print("""
    .___.______________________  
  __| _/|   \______   \_   ___ \ 
 / __ | |   ||       _/    \  \/ 
/ /_/ | |   ||    |   \     \____
\____ | |___||____|_  /\______  /
     \/             \/        \/ 
      
Doom Input Relay Client
""")

print("Connecting to Unix socket server...")

session_id = sys.argv[1] if len(sys.argv) > 1 else "1"
unix_socket_path = f"/tmp/doom-inputrelay-{session_id}"

client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
client.connect(unix_socket_path)

print("Connected to Unix socket server.")

current_keys = []

def update_sock(is_up: bool, key: int):
    client.send(bytes([is_up, key]))

def get_event_from_key(key) -> int:
    if type(key) is Key:
        if key == Key.alt:
            print("Quitting.")
            exit(0)
        if key == Key.left:
            return 0xac
        elif key == Key.right:
            return 0xae
        elif key == Key.up:
            return 0xad
        elif key == Key.down:
            return 0xaf
        elif key == Key.ctrl_l:
            return 0xa3
        elif key == Key.space:
            return 0xa2
        elif key == Key.shift_r:
            return 0x80+0x36
        elif key == Key.enter:
            return 13
        elif key == Key.esc:
            return 27
        else:
            raise Exception("unknown key")
    else:
        if key.char == "a":
            return 0xac
        elif key.char == "d":
            return 0xae
        elif key.char == "w":
            return 0xad
        elif key.char == "s":
            return 0xaf
        elif key.char == ",":
            return 0xa0
        elif key.char == ".":
            return 0xa1
        else:
            raise Exception("unknown key")

def on_press(key):
    processed_key = 0

    try:
        processed_key = get_event_from_key(key)
    except Exception:
        print("[x] Unknown key recieved.")
        return
    
    if processed_key not in current_keys:
        current_keys.append(processed_key)
        update_sock(True, processed_key)

def on_release(key):
    processed_key = 0

    try:
        processed_key = get_event_from_key(key)
    except Exception:
        print("[x] Unknown key recieved.")
        return
    
    current_keys.pop(current_keys.index(processed_key))
    update_sock(False, processed_key)
        
with keyboard.Listener(
    on_press=on_press,
    on_release=on_release,
    suppress=True
) as listener:
    print("Listening for keyboard events.")
    listener.join()