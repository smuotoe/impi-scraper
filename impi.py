from multiprocessing.pool import ThreadPool

import pandas as pd

from main import logging, get_data, read_file, save_file

file_numbers = read_file('remaining_file_numbers.txt', list(range(2420000, 2603491 + 1)))
if isinstance(file_numbers, str):
    file_numbers = [f for f in file_numbers.split('\n') if f != '']
file_numbers = sorted(file_numbers)
data_index = int(read_file('data_index.txt', 0))

file_data = []
remaining_file_numbers = file_numbers
for index, file in enumerate(ThreadPool(10).imap_unordered(get_data, file_numbers), start=1):
    remaining_file_numbers = list(set(remaining_file_numbers) - set([str(int(f)) for f in file.iloc[:, 0] if f != '' if not pd.isna(f)]))
    logging.info('{} done'.format(index + 1))
    file_data.append(file)
    if index % 10 == 0 or index == len(file_numbers):
        data_index += 1
        file_data = [df for df in file_data if df.shape[1] == 57]
        file_df = pd.concat(file_data).dropna(how='all').reset_index(drop=True)
        file_df.to_excel(f'file_data_{data_index}.xlsx', index=False)
        save_file(data_index, 'data_index.txt')
        save_file(remaining_file_numbers, 'remaining_file_numbers.txt')
        break

# df = pd.read_excel('data/file_data_1.xlsx').dropna(how='all')
# remaining_file_numbers = list(set(file_numbers) - set([str(int(f)) for f in df.iloc[:, 0]]))
