import os
import time

from main import read_file, logging, save_file

file_numbers = read_file('remaining_file_numbers.txt', list(range(2420000, 2603491 + 1)))
if isinstance(file_numbers, str):
    file_numbers = [f for f in file_numbers.split('\n') if f != '']

file_numbers = sorted(file_numbers)
total_files = len(file_numbers)
for _ in range(int(file_numbers[0]), int(file_numbers[-1]), 1000):
    p = os.system('python3 impi.py')
    # os.system('killall chrome')
    # os.system('killall chromedriver')
    if p == 0:
        total_files -= 1000
        logging.info(f"{total_files} file numbers remaining")
        time.sleep(10)
    else:
        logging.error('Error called in the last run of impi.py')
        print('break')
        save_file('-1', 'impi_status.txt')
        break
