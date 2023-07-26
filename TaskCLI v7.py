from os import kill
from signal import SIGTERM
from time import sleep
import psutil
from pymem import Pymem
from cutie import select
import msvcrt
from prettytable import PrettyTable

def close_process(pid):
    try:
        kill(pid, SIGTERM)
    except ProcessLookupError:
        pass

def list_processes():
    procnum = 0
    # Iterate over all running processes
    for proc in psutil.process_iter(attrs=['name', 'pid']):
        procnum += 1
        process_name = proc.info['name']
        process_id = proc.info['pid']
        print(f'[{procnum}] | Name: {process_name} | PID: {process_id}')
    print(f'\n{procnum} Process Running.\n')

def print_system_resources():
    cpu_percent = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    disk_usage = psutil.disk_usage('/')
    network_info = psutil.net_io_counters()
    print('\n' * 100)
    print(f"{COLOR_BOLD}{COLOR_HEADER}System Resource Usage:{COLOR_END}")
    print(f"{COLOR_OKGREEN}CPU Usage: {cpu_percent}%")
    print(f"Memory Usage: {convert_bytes(memory_info.used)} / {convert_bytes(memory_info.total)}")
    print(f"Disk Usage: {convert_bytes(disk_usage.used)} / {convert_bytes(disk_usage.total)}")
    print(f"Network Usage: Sent - {convert_bytes(network_info.bytes_sent)}, Received - {convert_bytes(network_info.bytes_recv)}")

def convert_bytes(size, precision=2):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
    suffix_index = 0
    while size > 1024 and suffix_index < len(suffixes) - 1:
        size /= 1024
        suffix_index += 1
    return f"{size:.{precision}f} {suffixes[suffix_index]}"

process_name = 'Not Selected'
pid = 'Not Selected'
executable = 'Not Selected'

def monitor_processes():
    procnum = 0
    while True:
        procnum += 1
        # Fetch all running processes (excluding System Idle Process) and their information
        process_table = PrettyTable(['PID', 'PNAME', 'STATUS', 'CPU', 'NUM THREADS', 'MEMORY(MB)'])
        for p in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'num_threads', 'memory_info']):
            try:
                with p.oneshot():
                    # Check if the process name is not "System Idle Process" before adding it to the table
                    if p.info['name'] != 'System Idle Process':
                        process_table.add_row([
                            str(p.info['pid']),
                            p.info['name'],
                            p.info['status'],
                            f'{p.info["cpu_percent"]:.2f}' + "%",
                            p.info['num_threads'],
                            f'{p.info["memory_info"].rss / 1e6:.3f} MB'
                        ])
                    
            except psutil.NoSuchProcess:
                pass
            except KeyboardInterrupt:
                print('Monitoring Stopped by User.')
        # Create a 1 second delay
        sleep(1)
        print(process_table)
        print('''+-------+-------------------------------+---------+-------+-------------+------------+
|  PID  |         PROCESS NAME          |  STATUS |  CPU  | NUM THREADS | MEMORY(MB) |
+-------+-------------------------------+---------+-------+-------------+------------+''')
        print(f'[According to Update {procnum}]')

def get_process_name_from_pid(pid):
    try:
        process = psutil.Process(pid)
        return process.name()
    except psutil.NoSuchProcess:
        return "Process not found"
    except psutil.AccessDenied:
        return "Access denied"

def print_process_tree(process, indent='', last=True, is_child=False):
    # Skip the "System Idle Process"
    if process.name() == "System Idle Process":
        return False

    # Set Unicode symbols for tree structure
    symbols = {
        "branch": "├─ ",
        "tee": "├─ ",
        "last": "└─ ",
        "space": "   ",
    }

    # Print process information with indentation
    print(f"{indent}{symbols['branch'] if is_child else ''}{symbols['branch'] if not last else symbols['last']}Name: {process.name()}   :   PID: {process.pid}")

    # Get child processes
    children = process.children()
    child_count = len(children)

    for index, child in enumerate(children):
        is_last = index == child_count - 1
        child_indent = indent + (symbols['space'] if not last else symbols['branch'])
        print_process_tree(child, child_indent, is_last, True)

    return child_count > 0

def find_executable(process_name):
    for proc in psutil.process_iter(['name', 'exe']):
        if proc.info['name'] == process_name:
            return proc.info['exe']
    return executable

# ANSI escape codes for color
COLOR_HEADER = '\033[95m'
COLOR_BOLD = '\033[1m'
COLOR_OKGREEN = '\033[92m'
COLOR_FAIL = '\033[91m'
COLOR_END = '\033[0m'

def get_process_name_or_pid():
    global process_name, pid
    user_input = input("PID/Process Name: ")
    if user_input == "":
        return
    try:
        pid = int(user_input)
        process_name = get_process_name_from_pid(pid)
        print(f"{process_name} ({pid}) Selected")
    except ValueError:
        process_name = user_input
        processes_with_name = [p for p in psutil.process_iter(['name', 'pid']) if p.info['name'] == process_name]
        if not processes_with_name:
            print(f"No process with the name '{process_name}' found.")
        elif len(processes_with_name) == 1:
            pid = processes_with_name[0].info['pid']
            print(f"PID {pid} is associated with the process '{process_name}'.")
        else:
            print(f"Multiple processes found with the name '{process_name}':")
            for index, proc in enumerate(processes_with_name):
                print(f"{index + 1}. PID: {proc.info['pid']}")
            chosen_idx = None
            while chosen_idx is None:
                user_choice = input("Choose the Number to the Left of the PID: ")
                try:
                    chosen_idx = int(user_choice)
                    if chosen_idx < 1 or chosen_idx > len(processes_with_name):
                        print("Invalid choice. Please enter a valid number.")
                        chosen_idx = None
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
                    chosen_idx = None

            chosen_proc = processes_with_name[chosen_idx - 1]
            pid = chosen_proc.info['pid']
            print(f"PID {pid} is associated with the process '{process_name}'.")

def main_menu():
    while True:
        executable_path = find_executable(process_name)

        if executable_path:
            executable = executable_path
        print(f'''{COLOR_OKGREEN}  _______        _____ _  _______ _      _____  __      ________ 
 |__   __|/\    / ____| |/ / ____| |    |_   _| \ \    / /____  |
    | |  /  \  | (___ | ' / |    | |      | |    \ \  / /    / / 
    | | / /\ \  \___ \|  <| |    | |      | |     \ \/ /    / /  
    | |/ ____ \ ____) | . \ |____| |____ _| |_     \  /    / /   
    |_/_/    \_\_____/|_|\_\_____|______|_____|     \/    /_/ 
{COLOR_END}         
Selected Process: {process_name}
Selected PID: {pid}
Executable: {executable}
''')
        try:
            options = ['Select Process', 'List Processes', 'Close Process', 'Inject Python Code', 'Monitor Resource Usage', 'Monitor Processes', 'Get Process Tree']
            chosen_idx = select(options)
            chosen = options[chosen_idx]

            if chosen == 'Select Process':
                get_process_name_or_pid()
            elif chosen == 'Close Process':
                if pid != 'Not Selected':
                    close_process(pid)
                else:
                    print("No process is selected. Please select a process first.")
            elif chosen == 'Monitor Processes':
                try:                         monitor_processes()
                except KeyboardInterrupt: print('Monitoring Canceled.')
            elif chosen == 'List Processes':
                list_processes()
            elif chosen == 'Inject Python Code':
                def insert_new_line(lines, current_line, current_column):
                    lines.insert(current_line + 1, lines[current_line][current_column:])
                    lines[current_line] = lines[current_line][:current_column]
                    return current_line + 1, 0

                def delete_character(lines, current_line, current_column):
                    if current_column > 0:
                        lines[current_line] = lines[current_line][:current_column - 1] + lines[current_line][current_column:]
                        return current_line, current_column - 1
                    elif current_line > 0:
                        current_column = len(lines[current_line - 1])
                        lines[current_line - 1] += lines[current_line]
                        del lines[current_line]
                        return current_line - 1, current_column
                    return current_line, current_column

                def main():
                    process = Pymem(process_name)
                    process.inject_python_interpreter()
                    lines = [""]
                    current_line = 0
                    current_column = 0

                    try:
                        while True:
                            # Clear the screen
                            print("\033[H\033[J")

                            # Print all the lines
                            for line in lines:
                                print(line)

                            # Print the current cursor position
                            print("\033[{};{}H".format(current_line + 1, current_column + 1))

                            # Get the keyboard input
                            key = msvcrt.getch()

                            # Process the input
                            if key == b'\r':  # Enter key
                                current_line, current_column = insert_new_line(lines, current_line, current_column)
                            elif key == b'\x08':  # Backspace key
                                current_line, current_column = delete_character(lines, current_line, current_column)
                            elif key == b'\x7f':  # Delete key
                                if current_column < len(lines[current_line]):
                                    lines[current_line] = lines[current_line][:current_column] + lines[current_line][current_column + 1:]
                            elif key == b'\x1a':  # Ctrl+Z (EOF)
                                break
                            elif key == b'\x03':  # Ctrl+C (KeyboardInterrupt)
                                raise KeyboardInterrupt
                            elif key == b'\xe0':  # Special keys (e.g., arrow keys)
                                next_key = msvcrt.getch()
                                if next_key == b'H':  # Up arrow key
                                    if current_line > 0:
                                        current_line -= 1
                                        current_column = min(current_column, len(lines[current_line]))
                                elif next_key == b'P':  # Down arrow key
                                    if current_line < len(lines) - 1:
                                        current_line += 1
                                        current_column = min(current_column, len(lines[current_line]))
                                elif next_key == b'K':  # Left arrow key
                                    current_column = max(current_column - 1, 0)
                                elif next_key == b'M':  # Right arrow key
                                    if current_column < len(lines[current_line]):
                                        current_column += 1
                            else:
                                # Insert the typed character at the current cursor position
                                lines[current_line] = lines[current_line][:current_column] + key.decode() + lines[current_line][current_column:]
                                current_column += 1

                        user_input = '\n'.join(lines)
                        process.inject_python_shellcode(user_input)

                    except KeyboardInterrupt:
                        print("\nPython Code Injection Canceled.")

            if __name__ == "__main__":
                main()
            elif chosen == 'Monitor Processes':
                monitor_processes()
            elif chosen == 'Monitor Resource Usage':
                while True:
                    try:
                        print_system_resources()
                    except Exception as e:
                        print(f'An error occurred: {e}')
            elif chosen == 'Get Process Tree':
                print_process_tree(process='firefox.exe')
        except Exception as e:
            pass

if __name__ == "__main__":
    main_menu()
