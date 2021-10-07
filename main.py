import logging
import pickle
import threading
import time
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options

threadLocal = threading.local()
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

t1_names = ['Número de expediente', 'Número de registro', 'Fecha de presentación', 'Fecha de inicio de uso',
            'Fecha de concesión', 'Fecha de vigencia', 'Fecha de publicación de la solicitud', 'Denominación',
            'Descripción de la marca', 'Tipo de solicitud', 'Tipo de marca',
            'Elementos sobre los cuales no se solicita protección', 'Número de registro internacional',
            'Traducción', 'Transliteración']

t2_names = ['Nombre', 'Dirección', 'Población', 'Código postal', 'País', 'Nacionalidad', 'RFC', 'Teléfono', 'Fax',
            'E-mail']
t3_names = ['Dirección', 'Población', 'Código postal', 'País']
t4_names = ['Clase', 'Descripción']
t5_names = ['Nombre', 'Dirección', 'Población', 'Código postal', 'País', 'Nacionalidad', 'RFC', 'Teléfono', 'Fax',
            'E-mail']
t6_names = ['Folio de entrada del trámite', 'Año de recepción', 'Descripción', 'Fecha de inicio', 'Fecha de conclusión']
t7_names = ['Descripción del oficio', 'Número del oficio', 'Fecha del oficio', 'Estado de la notificación']
t8_names = ['Folio de entrada de la promoción', 'Año de recepción de la promoción', 'Fecha de presentación',
            'Número del oficio que guarda relación con la promoción', 'Descripción de la promoción']


def extract_table(selector, soup, n=None):
    table = soup.select(selector)[0]
    table_rows = table.find_all('tr')  # find all rows
    if n == 4:
        table_data = table_rows[0].find_all('td')[0].find_all('td')
        table_header = table_rows[0].find_all('th')
        names = [th.text.strip() for th in table_header]
        data = [td.text.strip() for td in table_data]
    else:
        names = []
        data = []
        for tr in table_rows:
            table_data = tr.find_all('td')
            names.append([td.text.strip() for td in table_data][0])
            data.append([td.text.strip() for td in table_data][1])
    table = pd.DataFrame(dict(zip(names, data)), index=[0])
    # table = pd.DataFrame([data], columns=names)

    return table


def extract_table_with_index(selector, th_index, td_index, soup, n):
    table = soup.select(selector)[0]
    table_rows = table.find_all('tr')  # find all rows
    table_header = table_rows[th_index].find_all('th')
    names = [th.text.strip() for th in table_header]
    if n == 6:
        table_data = table_rows[1].find_all('td')
        data = [td.text.strip() for td in table_data]
        # df = pd.DataFrame(dict(zip(names, data)), index=[1])
        df = pd.DataFrame([data], columns=names)
    else:
        data = []
        i = 0
        while True:
            try:
                table_data = table_rows[td_index + i].find_all('td')
            except IndexError:
                break
            data.append([td.text.strip() for td in table_data])
            if (data[i] == ['Promociones']) | (data[i] == ['']):
                data = data[:-1]
                break
            i += 1
        df = pd.DataFrame(data, columns=names)

    return df


def empty_table(names, file_number=None):
    data = ["" for _ in range(len(names))]
    if file_number:
        data[0] = file_number
    # df = pd.DataFrame(dict(zip(names, data)), index=[1])
    df = pd.DataFrame([data], columns=names)
    return df


def cut_and_add_dots(string):
    max_length = 20000
    if len(string) >= max_length:
        reduced_string = string[:max_length] + '...'
        return reduced_string
    else:
        return string


def get_data(file_number):
    driver = get_driver()
    primary_url = "https://acervomarcas.impi.gob.mx:8181/marcanet/vistas/common/datos/bsqExpedienteCompleto.pgi"

    def retry():
        i = 0
        while i < 5:
            try:
                driver.get(primary_url)
                driver.find_element_by_css_selector("#frmBsqExp\\:expedienteId").send_keys(str(file_number) + '\n')
                # time.sleep(5)
                # soup = BeautifulSoup(driver.page_source, 'lxml')
                # error_msg = soup.select_one('span.ui-messages-error-summary')
                # if error_msg:
                #     logging.info(f'File number {file_number} does not exist.')
                #     break
                break
            except NoSuchElementException:
                time.sleep(10)
            i += 1

    retry()

    logging.info('Scraping file number: {}'.format(file_number))

    # time.sleep(5)

    count = 0
    while count < 5:
        try:
            # ALWAYS check for the ID of the search button
            search_id = 407
            driver.find_element_by_css_selector(f'#dtTblTramitesId\\:0\\:j_idt{search_id}').click()
            break
        except NoSuchElementException:
            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, 'lxml')
            error_msg = soup.select_one('span.ui-messages-error-summary')
            if error_msg:
                logging.info(f'File number {file_number} does not exist.')
                break
            count += 1

    time.sleep(5)
    soup: BeautifulSoup = BeautifulSoup(driver.page_source, 'lxml')

    try:
        table_1 = extract_table('#pnlDetalleGral_content > table:nth-child(3)', soup)
        table_1 = table_1.drop(table_1.columns[0], axis=1)
    except IndexError:
        logging.warning('Table 1 (Datos generales) not found.')
        table_1 = empty_table(t1_names, file_number)

    try:
        image = soup.select('#imagenSeccion~ table')[0].find_all('td')[1].img.attrs['src']
        if image:
            image = 'https://marcanet.impi.gob.mx:8181' + image
            image = pd.DataFrame({'image': image}, index=[0])
    except IndexError:
        image = pd.DataFrame({'image': ''}, index=[0])

    try:
        vcc = soup.select('#imagenSeccion~ table')[1].find_all('td')[1].text.strip()
        vcc = pd.DataFrame({'vcc': vcc}, index=[0])
    except IndexError:
        vcc = pd.DataFrame({'vcc': ''}, index=[0])

    try:
        table_2 = extract_table("#titularSeccion~ table", soup)
    except IndexError:
        logging.warning('Table 2 (Datos del titular) not found.')
        table_2 = empty_table(t2_names)

    try:
        table_3 = extract_table("#estabSeccion~ table", soup)
    except IndexError:
        logging.warning('Table 3 (Establecimiento) not found.')
        table_3 = empty_table(t3_names)

    try:
        table_4 = extract_table("#dtGrdProductosId_content > table", soup, 4)
        try:
            table_4['Descripción'] = [cut_and_add_dots(d) for d in table_4['Descripción']]
        except KeyError as e:
            # raise KeyError(f'{e}\nFile number is {file_number}')
            logging.warning(e)
            raise IndexError
    except IndexError:
        logging.warning('Table 4 (Productos y servicios) not found.')
        table_4 = empty_table(t4_names)

    try:
        table_5 = extract_table("#dtGrdApoderadosId_content > table", soup)
        table_5 = table_5.drop(table_5.columns[0], axis=1)  # remove the first column
    except IndexError:
        logging.warning('Table 5 (Datos del apoderado) not found.')
        table_5 = empty_table(t5_names)

    try:
        table_6 = extract_table_with_index("#dtTblTramitesId > div.ui-datatable-tablewrapper > table",
                                           0, 1, soup, 6)
        table_6 = table_6.drop(table_6.columns[[0, 6, 7]], axis=1)

    except IndexError:
        logging.warning('Table 6 (Trámite) not found.')
        table_6 = empty_table(t6_names)

    try:
        table_7 = extract_table_with_index("#frmDlgDicProm > table", 1, 3, soup, 7)
        table_7 = table_7.drop(table_7.columns[4], axis=1)
    except IndexError:
        logging.warning('Table 7 (Oficios) not found.')
        table_7 = empty_table(t7_names)

    # To test 'promociones', use file_number 2195524
    # ALWAYS check for the latest table ID
    try:
        table_id = 435
        table_8 = extract_table_with_index(f"#frmDlgDicProm\\:j_idt{table_id} > div > table", 0, 1, soup, 8)
        table_8 = table_8.drop(table_8.columns[5], axis=1)
    except IndexError:
        logging.warning('Table 8 (Promociones) not found.')
        table_8 = empty_table(t8_names)

    df = pd.concat([table_1, image, vcc, table_2, table_3, table_4, table_5, table_6], axis=1)
    df['tmp'] = 1  # create dummy key column for `merge`
    df1 = pd.concat([table_7, table_8], axis=1)
    df1['tmp'] = 1
    df = pd.merge(df, df1, on='tmp')
    df = df.drop('tmp', axis=1)
    return df


def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output)


def save_file(obj, filename):
    with open(filename, 'w') as f:  # Overwrites any existing file.
        if isinstance(obj, list):
            for file_number in obj:
                f.write("{}\n".format(str(file_number)))
        else:
            f.write(str(obj))


def read_file(file, default):
    path = Path(file)
    if path.is_file():
        with open(path, 'r') as file:
            return file.read()
    else:
        return default


def get_driver():
    driver = getattr(threadLocal, 'driver', None)
    if driver is None or not get_driver_status(driver):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-browser-side-navigation")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-features=VizDisplayCompositor")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        driver = webdriver.Chrome(options=chrome_options)
        setattr(threadLocal, 'driver', driver)
    return driver


def get_driver_status(driver):
    from urllib3.exceptions import MaxRetryError
    try:
        _ = driver.title
        return True
    except MaxRetryError:
        return False
