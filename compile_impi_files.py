import os
import pandas as pd
from tqdm import tqdm

folders = ['file_data_linux', 'file_data_wsl']
df_list = []
for folder in folders:
    files = os.listdir(folder)
    for file in tqdm(files, 'File'):
        df_list.append(pd.read_excel(f'{folder}/{file}'))

impi_df_dup = pd.concat(df_list).reset_index(drop=True)
impi_df = impi_df_dup.drop_duplicates().sort_values('Número de expediente').reset_index(drop=True)
impi_df_na = impi_df[pd.isna(impi_df['Número de expediente'])]
impi_df.dropna(axis=0, subset=['Número de expediente'], inplace=True)

with pd.ExcelWriter('impi_data.xlsx', engine='xlsxwriter', options={'strings_to_urls': False}) as writer:
    impi_df.to_excel(writer, index=False)

num_df_list = []
for num in tqdm(impi_df['Número de expediente'].unique().tolist(), 'File number'):
    df = impi_df.query(f"`Número de expediente` == {str(num)}")
    df.loc[:, 'Número del oficio'] = df['Número del oficio'].map(lambda x: '' if pd.isna(x) else x)
    if len(df) > 1:
        if any(df['Número del oficio'].tolist()):
            # print('Here')
            df.drop_duplicates(['Número del oficio'], inplace=True)
            df.dropna(axis=0, subset=['Número del oficio'], inplace=True)
        else:
            df.drop_duplicates(['Número del oficio'], inplace=True)
    num_df_list.append(df)


impi_final = pd.concat(num_df_list).reset_index(drop=True)
with pd.ExcelWriter('impi_data_1.xlsx', engine='xlsxwriter', options={'strings_to_urls': False}) as writer:
    impi_final.to_excel(writer, index=False)
