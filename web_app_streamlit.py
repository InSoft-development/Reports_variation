import argparse
import datetime
import errno
import json
import os
from dateutil import parser as pars

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st
from loguru import logger
from streamlit_option_menu import option_menu

import get_interval_streamlit
import get_pdf_report_streamlit
import get_view_streamlit


def fill_zeros_with_last_value(df, count_next=288):
    count = 0
    for index, row in df.iterrows():
        if row['target_value'] == 0:
            if count == 0:
                start_index = index
                last_value = df.iloc[index-1]['target_value']
            count += 1
        if row['target_value'] != 0 and count != 0:
            if count < count_next:
                df.loc[start_index:index-1, 'target_value'] = last_value
            count = 0

# Конфиг страницы веб-приложения streamlit
st.set_page_config(
    page_title="Web app",
    layout="wide"
)

# Убирает логотип streamlit

hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_st_style, unsafe_allow_html=True)


# вычисление средних для составления списка датчиков, внесших max вклад
def mean_index(data, sensors, top_count=3):
    # отбрасываем лишние датчики, перечисленные в config_plot_SOCHI
    data_temp = data.copy(deep=True)
    for sensor in DROP_LIST:
        if sensor in data_temp.columns:
            data_temp.drop(columns=sensor, inplace=True)
            sensors.remove(sensor)
            logger.info(f"drop bad sensor: {sensor} from {CSV_LOSS_NAME} dataframe")
    mean_loss = data_temp[sensors].mean().sort_values(ascending=False).index[:top_count].to_list()
    mean_measurement = list(data_temp[sensors].mean().sort_values(ascending=False).values[:top_count])
    return mean_loss, mean_measurement


# сортировка добавленных периодов
def sort_correction_json(added):
    if len(added) > 1:
        for i in range(0, len(added) - 1):
            begin = i
            j = i
            while added[j]["index"][0] == added[j + 1]["index"][0]:
                j += 1
                if j + 1 == len(added):
                    break
            swap_dict = added[begin:j + 1]
            swap_dict.sort(key=lambda swap_dict: swap_dict["index"][-1] - swap_dict["index"][0], reverse=False)
            added[begin:j + 1] = swap_dict
            logger.info("json intervals has been sorted")


# загрузка KKS и описания датчиков группы
@st.cache_data
def load_kks():
    df_kks = pd.read_csv(DICT_KKS, delimiter=';', header=None)
    df_kks = df_kks.loc[~df_kks[0].isin(config_plot_json['DROP_LIST'])]
    kks_dict = dict(zip(df_kks[0].to_list(), df_kks[1].to_list()))
    return kks_dict


# выбранный период
if "selection_interval" not in st.session_state:
    st.session_state.selection_interval = 0
    st.session_state.selection_interval_tab_list = 0

# флаг выбора нового периода
if "selection_flag" not in st.session_state:
    st.session_state.selection_flag = 0

# флаг начала редактирования периода
if "edit_flag" not in st.session_state:
    st.session_state.edit_flag = 0
    st.session_state.edit_index = 0

# флаг открытия вкладки
if "navigation_tab_flag" not in st.session_state:
    st.session_state.navigation_tab_flag = False

# ориентация страниц отчетов
if "PDF_check_radio_button" not in st.session_state:
    st.session_state.PDF_check_radio_button = "Книжная"
    st.session_state.PDF_check_radio_index = 0
    st.session_state.PDF_id_flag_radio = False

# выбранная группа
if "selected_group" not in st.session_state:
    st.session_state.selected_group = 0
    st.session_state.selected_name = "None"
    st.session_state.flag_group = False

# Выбранный метод
if "checked_method" not in st.session_state:
    st.session_state.checked_method = "Potentials"

# Интервалы датчиков
if ("LEFT_SPACE" not in st.session_state) or ("RIGHT_SPACE" not in st.session_state):
    st.session_state.LEFT_SPACE = 1000
    st.session_state.RIGHT_SPACE = 1000

# Сглаживагие
if "roll" not in st.session_state:
    st.session_state.roll = 4

if "top" not in st.session_state:
    st.session_state.top = 3

parser = argparse.ArgumentParser()
parser.add_argument('--station', type=str, default='')
opt = parser.parse_args()

DATA_DIR = f'Data/'
UTILS_DIR = f'utils/'
WEB_APP_DIR = f'web_app/'
WEB_APP_REPORTS_DIR = f'{WEB_APP_DIR}/Reports/'
WEB_APP_REPORTS = f'{WEB_APP_REPORTS_DIR}{st.session_state.checked_method}/'
METHODS = ["Potentials", "LSTM"]
METHODS_DIR = f'{DATA_DIR}{st.session_state.checked_method}/'

JSON_DIR = f'{METHODS_DIR}json_interval/'

CSV_DATA = f'{DATA_DIR}/csv_data/'
CSV_PREDICT = f'{METHODS_DIR}csv_predict/'
CSV_ROLLED = f'{METHODS_DIR}csv_rolled/'
CSV_LOSS = f'{METHODS_DIR}csv_loss/'

LEFT_SPACE = st.session_state.LEFT_SPACE
RIGHT_SPACE = st.session_state.RIGHT_SPACE

try:
    os.mkdir(f'{WEB_APP_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)
        st.write(f'Error has been occurred on create {WEB_APP_DIR}')
        st.stop()

try:
    os.mkdir(f'{WEB_APP_REPORTS_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)
        st.write(f'Error has been occurred on create {WEB_APP_REPORTS_DIR}')
        st.stop()

try:
    os.mkdir(f'{WEB_APP_REPORTS}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)
        st.write(f'Error has been occurred on create {WEB_APP_REPORTS}')
        st.stop()

try:
    os.mkdir(f'{DATA_DIR}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)
        st.write(f'Error has been occurred on create {DATA_DIR}')
        st.stop()

try:
    os.mkdir(f'{CSV_DATA}')
except OSError as e:
    if e.errno != errno.EEXIST:
        logger.error(e)
        st.write(f'Error has been occurred on create {CSV_DATA}')
        st.stop()

for method in METHODS:
    csv_predict = f'{DATA_DIR}{method}{os.sep}csv_predict{os.sep}'
    csv_loss = f'{DATA_DIR}{method}{os.sep}csv_loss{os.sep}'
    csv_rolled = f'{DATA_DIR}{method}{os.sep}csv_rolled{os.sep}'
    json_dir = f'{DATA_DIR}{method}{os.sep}json_interval{os.sep}'

    try:
        os.mkdir(f'{DATA_DIR}{method}')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {DATA_DIR}{method}')
            st.stop()
    try:
        os.mkdir(csv_predict)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {csv_predict}')
            st.stop()
    try:
        os.mkdir(csv_rolled)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {csv_rolled}')
            st.stop()
    try:
        os.mkdir(csv_loss)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {csv_loss}')
            st.stop()
    try:
        os.mkdir(json_dir)
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {json_dir}')
            st.stop()

try:
    with open(f'{WEB_APP_DIR}config_plot_{opt.station}.json', 'r', encoding='utf8') as j:
        config_plot_json = json.load(j)
except FileNotFoundError as e:
    msg = f'The file {WEB_APP_DIR}config_plot_{opt.station}.json hasn\'t found. Please add file ' \
          f'{WEB_APP_DIR}config_plot_{opt.station}.json'
    logger.error(e)
    st.error(msg)
    st.stop()

try:
    with open(f'{WEB_APP_DIR}config_{opt.station}.json', 'r', encoding='utf8') as j:
        config = json.load(j)
except FileNotFoundError as e:
    msg = f'The file {WEB_APP_DIR}config_{opt.station}.json hasn\'t found. Please add file ' \
          f'{WEB_APP_DIR}config_{opt.station}.json'
    logger.error(e)
    st.error(msg)
    st.stop()

try:
    with open(f'{UTILS_DIR}default_interval_config.json', 'r', encoding='utf8') as j:
        default_interval_config = json.load(j)
except FileNotFoundError as e:
    msg = f'The file {UTILS_DIR}default_interval_config.json hasn\'t found. Please add file ' \
          f'{UTILS_DIR}default_interval_config.json'
    logger.error(e)
    st.error(msg)
    st.stop()

try:
    with open(f'{DATA_DIR}/{config["paths"]["files"]["json_sensors"]}', 'r', encoding='utf8') as f:
        json_dict = json.load(f)
except FileNotFoundError as e:
    msg = f'The file {DATA_DIR}/{config["paths"]["files"]["json_sensors"]} hasn\'t found. Please add file ' \
          f'{DATA_DIR}/{config["paths"]["files"]["json_sensors"]}'
    logger.error(e)
    st.error(msg)
    st.stop()

PLOT_FEATURES = config_plot_json['PLOT_FEATURES']
DROP_LIST = config_plot_json['DROP_LIST']
DICT_KKS = f'{DATA_DIR}{config["paths"]["files"]["original_kks"]}'
NUMBER_OF_SAMPLES = config["number_of_samples"]

index_group = [list(x.keys())[0] for x in json_dict["groups"]]
if index_group[0] == '0':
    index_group.remove('0')
logger.info(f'finded groups: {index_group}')

selector_index_group = [x + " " + "(" + json_dict["groups"][int(x)][str(x)]['name'] + ")" for x in index_group]

for group in index_group:
    web_app_group = f'{WEB_APP_REPORTS}/group_{group}/'

    try:
        os.mkdir(f'{web_app_group}')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {web_app_group}')
            st.stop()

    web_app_period_reports = f'{web_app_group}/periods'
    try:
        os.mkdir(f'{web_app_period_reports}/')
    except OSError as e:
        if e.errno != errno.EEXIST:
            logger.error(e)
            st.write(f'Error has been occurred on create {web_app_period_reports}')
            st.stop()

if not st.session_state.flag_group:
    st.session_state.flag_group = True
    st.session_state.selected_group = index_group[0]

CSV_DATA_NAME = f'{CSV_DATA}/slices.csv'
CSV_PREDICT_NAME = f'{CSV_PREDICT}/predict_{st.session_state.selected_group}.csv'
CSV_ROLLED_NAME = f'{CSV_ROLLED}/rolled_{st.session_state.selected_group}.csv'
CSV_LOSS_NAME = f'{CSV_LOSS}/loss_{st.session_state.selected_group}.csv'

added_intervals = f'{JSON_DIR}/added_intervals_{st.session_state.selected_group}.json'
group_intervals = f'{JSON_DIR}/group_{st.session_state.selected_group}.json'
interval_list = []
top_list = []
interval_added_list = []
top_added_list = []

# получение исходных данных csv
try:
    logger.info(f'Read_file: {CSV_DATA_NAME}')
    data_df = pd.read_csv(f'{CSV_DATA_NAME}')
    time_df = pd.DataFrame()
    time_df['timestamp'] = data_df['timestamp']
    time_df.index = time_df['timestamp']
    data_df.index = data_df['timestamp']
    data_df = data_df.drop(columns=['timestamp'])
except Exception as e:
    logger.error(e)

# получение данных csv группы по вероятности аномалии
try:
    logger.info(f'Read_file: {CSV_PREDICT_NAME}')
    anomaly_time_df = pd.read_csv(f'{CSV_PREDICT_NAME}')
    anomaly_time_df.index = anomaly_time_df['timestamp']
    anomaly_time_df = anomaly_time_df.drop(columns=['timestamp'])
except Exception as e:
    logger.error(e)

# получение данных csv группы сглаженной вероятности
try:
    logger.info(f'Read_file: {CSV_ROLLED_NAME}')
    rolled_df = pd.read_csv(f'{CSV_ROLLED_NAME}')
    #rolled_df.fillna(method='ffill', inplace=True)
    #rolled_df.fillna(0, inplace=True)
    rolled_df.fillna(value={"target_value": 0}, inplace=True)
    fill_zeros_with_last_value(rolled_df)
    rolled_df.index = rolled_df['timestamp']
    rolled_df = rolled_df.drop(columns=['timestamp'])
except Exception as e:
    logger.error(e)

# получение данных csv по вкладам датчиков в аномалию
try:
    logger.info(f'Read_file: {CSV_LOSS_NAME}')
    loss_df = pd.read_csv(f'{CSV_LOSS_NAME}')
    loss_df.fillna(0, inplace=True)
    loss_df.index = loss_df['timestamp']
    loss_df = loss_df.drop(columns=['timestamp'])
except Exception as e:
    logger.error(e)

# считывание интервалов аномальности по каждой группе
top_sensors = []

try:
    f = open(group_intervals, 'r')
    j = json.load(f)
    for interval in j:
        interval_list.append(interval['index'])
        top_sensors.append(interval['top_sensors'])
    top_list.append(top_sensors)
    top_sensors = []
except Exception as e:
    logger.error(e)

try:
    f = open(added_intervals, 'r')
    f.close()
except FileNotFoundError as e:
    logger.info(f'{added_intervals} has been created')
    with open(added_intervals, "w+") as f:
        json.dump(dict(), f, ensure_ascii=False, indent=4)

dict_kks = load_kks()
logger.info(f'dict_kks has been loaded')

temp_idx = 0
while int(st.session_state.selected_group) != int(list(json_dict['groups'][temp_idx].keys())[0]):
    temp_idx += 1
union_sensors = json_dict['groups'][temp_idx][st.session_state.selected_group]['unions']
single_sensors = json_dict['groups'][temp_idx][st.session_state.selected_group]['single sensors']
if union_sensors == "null":
    group_sensors = single_sensors
elif single_sensors == "null":
    group_sensors = union_sensors
else:
    group_sensors = union_sensors + single_sensors

with st.sidebar:
    selected_menu = option_menu(
        menu_title=None,
        options=["---", "Интервалы", "---", "Дополнения", "---", "Настройки", "---"],
        icons=["", "chevron-right", "", "chevron-right", "", "chevron-right"],
        orientation='vertical',
        default_index=1
    )

if selected_menu == "Интервалы":
    st.markdown(f'<h4 style="text-align: left; color: #4562a1;">Метод {st.session_state.checked_method}: группа '
                f'{str(selector_index_group[int(st.session_state.selected_group) - 1])}</h5>',
                unsafe_allow_html=True)
    with st.sidebar:
        method_radio = st.radio("Метод", options=METHODS, index=0, key="method_radio")
        selected_group_sidebar = st.selectbox("Группа", options=selector_index_group,
                                              key="group_select_box_sidebar", label_visibility="visible", index=0)
        st.session_state.selected_name = selected_group_sidebar
        if st.session_state.checked_method != method_radio:
            st.session_state.checked_method = method_radio
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            st.session_state.selection_interval = 0
            st.experimental_rerun()
        if st.session_state.selected_group != selected_group_sidebar[:selected_group_sidebar.find(' ')]:
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            st.session_state.selection_interval = 0
            st.experimental_rerun()
    web_app_group = f'{WEB_APP_REPORTS}/group_{st.session_state.selected_group}/'
    web_app_period_reports = f'{web_app_group}/periods'
    tab_name_list = ["Главная"]

    if st.session_state.checked_method == "Potentials":
        home_line_text = "График вероятности наступления аномалии за весь период"
        tab_line_text = "График вероятности наступления аномалии"
    if st.session_state.checked_method == "LSTM":
        home_line_text = "График функции потерь за весь период"
        tab_line_text = "График функции потерь"
    try:
        with open(added_intervals, 'r', encoding='utf8') as f:
            added = json.load(f)
    except FileNotFoundError as e:
        msg = f'The file {added_intervals} hasn\'t found. ' \
              f'Please add file {added_intervals}'
        logger.error(e)

    if added:
        for interval in added:
            interval_added_list.append(interval['index'])
            top_added_list.append(interval['top_sensors'])
    merged_interval_list = [0] + interval_list + interval_added_list
    merged_interval_list[1:] = sorted(merged_interval_list[1:], key=lambda x: x[0], reverse=False)
    merged_top_list = [["0"]]
    for interval in merged_interval_list[1:]:
        for element in j:
            if interval == element["index"]:
                merged_top_list.append(element["top_sensors"])
        for element in added:
            if interval == element["index"]:
                merged_top_list.append(element["top_sensors"])
    for tab in merged_interval_list[1:]:
        tab_name_list.append("(" + datetime.datetime.strptime(data_df.index[tab[0]], "%Y-%m-%d %H:%M:%S")
                             .strftime("%d/%m/%y %H:%M:%S") + ";" +
                             datetime.datetime.strptime(data_df.index[tab[-1]], "%Y-%m-%d %H:%M:%S")
                             .strftime("%d/%m/%y %H:%M:%S") + ")")
    interval_added_list = []
    tab_bar_list = []
    tab_sidebar_list = []
    count = 0

    # st.session_state.opened_tab = tab_name_list
    for tab in tab_name_list:
        tab_bar_item = stx.TabBarItemData(id=tab_name_list.index(tab), title=tab, description="")
        tab_bar_list.append(tab_bar_item)
        tab_sidebar_list.append(tab)
        count += 1
    with st.sidebar:
        selected_interval_sidebar = st.selectbox("Выберите период", tab_sidebar_list,
                                                 index=int(st.session_state.selection_interval),
                                                 key="intervals_select_box_sidebar", label_visibility="visible")

        top_count = st.number_input(label="Количество датчиков, внесших максимальный вклад", min_value=1,
                                    max_value=len(dict_kks), value=st.session_state.top, key="top_count")

        st.session_state.top = top_count

        if selected_interval_sidebar == "Главная":
            with st.form("interval detection"):
                st.write("Выделение интервалов")

                roll_probability = st.number_input(label="Сглаживание в часах", min_value=0,
                                                   value=config["model"]["rolling"], key="roll_probability")

                st.session_state.roll = roll_probability

                short_col, long_col = st.columns(2)
                with short_col:
                    short_threshold = st.number_input(label="SHORT_THRESHOLD", min_value=1, max_value=100, value=default_interval_config["SHORT_THRESHOLD"],
                                                      key="SHORT_THRESHOLD")
                    len_short_anomaly = st.number_input(label="LEN_SHORT_ANOMALY", min_value=0, value=default_interval_config["LEN_SHORT_ANOMALY"],
                                                        key="LEN_SHORT_ANOMALY")
                    count_continue_short = st.number_input(label="COUNT_CONTINUE_SHORT", min_value=0, value=default_interval_config["COUNT_CONTINUE_SHORT"],
                                                           key="COUNT_CONTINUE_SHORT")
                with long_col:
                    long_threshold = st.number_input(label="LONG_THRESHOLD", min_value=1, max_value=100, value=default_interval_config["LONG_THRESHOLD"],
                                                     key="LONG_THRESHOLD")
                    len_long_anomaly = st.number_input(label="LEN_LONG_ANOMALY", min_value=0, value=default_interval_config["LEN_LONG_ANOMALY"],
                                                       key="LEN_LONG_ANOMALY")
                    count_continue_long = st.number_input(label="COUNT_CONTINUE_LONG", min_value=0, value=default_interval_config["COUNT_CONTINUE_LONG"],
                                                          key="COUNT_CONTINUE_LONG")
                submitted_interval_detection = st.form_submit_button("Запустить выделение интервалов")
                if submitted_interval_detection:
                    st.write("Выделение интервалов")
                    get_interval_streamlit.rebuilt_anomaly_interval_streamlit(st.session_state.checked_method,
                                                                              CSV_PREDICT, CSV_ROLLED, CSV_DATA_NAME,
                                                                              JSON_DIR, CSV_LOSS,
                                                                              roll_probability,
                                                                              NUMBER_OF_SAMPLES,
                                                                              DROP_LIST,
                                                                              short_threshold,
                                                                              len_short_anomaly,
                                                                              count_continue_short,
                                                                              long_threshold,
                                                                              len_long_anomaly,
                                                                              count_continue_long,
                                                                              config,
                                                                              top_count)
                    st.experimental_rerun()
        report_sidebar_button = st.button("PDF", key="report_siderbar_button")

    st.session_state.selection_interval = tab_name_list.index(selected_interval_sidebar)
    if st.session_state.edit_flag:
        st.session_state.selection_flag = False

    if st.session_state.selection_flag:
        tab_list = stx.tab_bar(data=tab_bar_list, default=st.session_state.selection_interval)
    else:
        tab_list = stx.tab_bar(data=tab_bar_list, default=st.session_state.selection_interval)
        st.session_state.selection_flag = False

    if st.session_state.navigation_tab_flag:
        st.session_state.selection_interval = 0
        st.session_state.navigation_tab_flag = False
        idx = 0
    else:
        idx = int(tab_list)
    logger.info(f'idx = {idx}')
    logger.info(f'tab_list = {tab_list}')
    if idx == 0:
        st.markdown(f'<h5 style="text-align: left; color: #4562a1;">{home_line_text}</h5>',
                    unsafe_allow_html=True)
        df_common = rolled_df
        col_list = ['target_value']
        anomaly_interval = [0, len(df_common)]
        fig_home = get_view_streamlit.home_plot(df_common, anomaly_interval, col_list, interval_list)
        st.markdown("<h5 style='text-align: left; color: #4562a1;'>Найденные периоды</h5>",
                    unsafe_allow_html=True)

        found_interval, empty_interval_col = st.columns([5, 5])
        with found_interval:
            if st.session_state.selection_flag:
                st.session_state.selection_flag = False
                st.session_state.selection_interval = tab_list
            selected_interval = st.selectbox("Выберите период", tab_sidebar_list,
                                             key="intervals_select_box", label_visibility="visible")
            if (selected_interval != tab_name_list[0]) \
                    and (selected_interval != tab_name_list.index(selected_interval)) \
                    and (not st.session_state.selection_flag):
                st.session_state.selection_interval = tab_name_list.index(selected_interval)
                st.session_state.selection_flag = True
                selected_interval_sidebar = st.session_state.selection_interval
                logger.info(f'selected_interval_sidebar = {selected_interval_sidebar}')
                st.experimental_rerun()
        st.markdown("<h5 style='text-align: left; color: #4562a1;'>Добавить период</h5>",
                    unsafe_allow_html=True)

        with st.form(key="create_period"):
            flag_down_time = False
            flag_up_time = False
            down_border, up_border, create_border = st.columns([7, 7, 6])
            with down_border:
                down_time = st.text_input("Начало периода", max_chars=17, key='down_time',
                                          type="default", placeholder="ДД/ММ/ГГ ЧЧ:ММ:СС")
                try:
                    if down_time != "":
                        # datetime_down_time = datetime.datetime.strptime(down_time, '%d/%m/%y %H:%M:%S')
                        datetime_down_time = pars.parse(down_time, dayfirst=True, default=datetime.datetime(1978, 1, 1, 0, 0))
                        flag_down_time = True
                    else:
                        st.error("Введите начало периода")
                except ValueError as e:
                    st.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")
            with up_border:
                up_time = st.text_input("Конец периода", max_chars=17, key='up_time',
                                        type="default", placeholder="ДД/ММ/ГГ ЧЧ:ММ:СС")
                try:
                    if up_time != "":
                        # datetime_up_time = datetime.datetime.strptime(up_time, '%d/%m/%y %H:%M:%S')
                        datetime_up_time = pars.parse(up_time, dayfirst=True, default=datetime.datetime(1978, 1, 1, 0, 0))
                        flag_up_time = True
                    else:
                        st.error("Введите конец периода")
                except ValueError as e:
                    st.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")
            with create_border:
                st.write("\n")
                st.write("\n")
                create_button = st.form_submit_button(label='Создать')
                if create_button and flag_down_time and flag_up_time:
                    st.session_state.selection_flag = False
                    st.session_state.selection_interval = 0
                    try:
                        if datetime_down_time not in df_common.index.tolist():
                            logger.info(datetime_down_time)
                            timestamp_down_time = datetime_down_time.timestamp()
                            datetime_down_time = pars.parse(
                                min(df_common.index, key=lambda x: abs(pars.parse(x).timestamp() - timestamp_down_time)))
                            logger.info(datetime_down_time)
                            with down_border:
                                st.info(f"Начало периода было округлено до "
                                        f"{datetime_down_time.strftime('%d/%m/%y %H:%M:%S')}")

                        if datetime_up_time not in df_common.index.tolist():
                            logger.info(datetime_up_time)
                            timestamp_up_time = datetime_up_time.timestamp()
                            datetime_up_time = pars.parse(
                                min(df_common.index, key=lambda x: abs(pars.parse(x).timestamp() - timestamp_up_time)))
                            logger.info(datetime_up_time)
                            with up_border:
                                st.info(f"Конец периода был округлен до "
                                        f"{datetime_up_time.strftime('%d/%m/%y %H:%M:%S')}")

                        datetime_down_time_index = df_common.index.tolist().index(
                            datetime_down_time.strftime("%Y-%m-%d %H:%M:%S"))
                        datetime_up_time_index = df_common.index.tolist().index(
                            datetime_up_time.strftime("%Y-%m-%d %H:%M:%S"))

                        flag_between_time = (datetime_up_time_index <= len(df_common)) and \
                                            (datetime_down_time_index >= 0)
                        if (datetime_up_time > datetime_down_time) and flag_between_time:
                            interval_begin_index = datetime_down_time_index
                            interval_end_index = datetime_up_time_index
                            top_T, measurement = mean_index(loss_df[interval_begin_index:interval_end_index], group_sensors, top_count=st.session_state.top)
                            logger.info(loss_df[interval_begin_index:interval_end_index])
                            dictionary = {
                                "time": [str(datetime.datetime.strftime(datetime_down_time,
                                                                        "%Y-%m-%d %H:%M:%S")),
                                         str(datetime.datetime.strftime(datetime_up_time,
                                                                        "%Y-%m-%d %H:%M:%S"))],
                                "len": interval_end_index - interval_begin_index,
                                "index": [interval_begin_index, interval_end_index],
                                "top_sensors": top_T,
                                "measurement": measurement
                            }
                            try:
                                with open(added_intervals, 'r', encoding='utf8') as f:
                                    added = json.load(f)
                            except FileNotFoundError as e:
                                msg = f'The file {added_intervals} hasn\'t found. ' \
                                      f'Please add file {added_intervals}'
                                logger.error(e)
                                st.error(msg)
                                st.stop()

                            try:
                                with open(group_intervals, 'r', encoding='utf8') as f:
                                    group_sensors = json.load(f)
                            except FileNotFoundError as e:
                                msg = f'The file {group_intervals} hasn\'t found. ' \
                                      f'Please add file {group_intervals}'
                                logger.error(e)
                                st.error(msg)
                                st.stop()

                            if (not added) and (dictionary not in group_sensors):
                                added = []
                                added.append(dictionary)
                                try:
                                    with open(added_intervals, 'w', encoding='utf8') as f:
                                        json.dump(added, f, ensure_ascii=False, indent=4)
                                except FileNotFoundError as e:
                                    msg = f'The file {added_intervals} hasn\'t found. ' \
                                          f'Please add file {added_intervals}'
                                    logger.error(e)
                                    st.error(msg)
                                    st.stop()
                                st.session_state.navigation_tab_flag = True
                                st.experimental_rerun()
                            elif (dictionary not in added) and (dictionary not in group_sensors):
                                added.append(dictionary)
                                added.sort(key=lambda added: added["index"][0], reverse=False)
                                sort_correction_json(added)
                                try:
                                    with open(added_intervals, 'w', encoding='utf8') as f:
                                        json.dump(added, f, ensure_ascii=False, indent=4)
                                except FileNotFoundError as e:
                                    msg = f'The file {added_intervals} hasn\'t found. ' \
                                          f'Please add file {added_intervals}'
                                    logger.error(e)
                                    st.error(msg)
                                    st.stop()
                                st.session_state.navigation_tab_flag = True
                                st.experimental_rerun()
                            else:
                                st.error("Введенный период уже добавлен или найден")
                        else:
                            st.error("Конец периода должен быть после начала периода!")

                    except ValueError as e:
                        st.error("Задано время не из \"пятиминутки\". Добавление не произошло")

        st.markdown("""---""")
        columns_table = st.columns((8, 4, 4, 2, 2))
        fields = ["Добавленный период", 'Начало периода', 'Конец периода', ""]
        for col, field_name in zip(columns_table, fields):
            col.markdown("<b style='text-align: left; color: #4562a1;'>" + field_name + "</b>",
                         unsafe_allow_html=True)
        st.markdown("""---""")
        try:
            with open(added_intervals, 'r', encoding='utf8') as f:
                added = json.load(f)
        except FileNotFoundError as e:
            msg = f'The file {added_intervals} hasn\'t found. ' \
                  f'Please add file {added_intervals}'
            logger.error(e)
            st.error(msg)
            st.stop()
        for interval in added:
            interval_added_list.append(interval['index'])
        flag_down_edit = False
        flag_up_edit = False
        for x, interval in enumerate(interval_added_list):
            col1, col2, col3, col4, col5 = st.columns((8, 4, 4, 2, 2))
            col1.markdown("<b style='text-align: left; color: #4562a1;'>Период " + str(x + 1) + "</b>",
                          unsafe_allow_html=True)

            col_down_datetime = datetime.datetime.strptime(df_common.index[interval[0]],
                                                           "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y %H:%M:%S")
            col_up_datetime = datetime.datetime.strptime(df_common.index[interval[-1]],
                                                         "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%y %H:%M:%S")

            button_edit_container = col4.empty()
            button_remove_container = col5.empty()
            edit_button = button_edit_container.button("✏️", key="edit_button_" + str(x))
            remove_button = button_remove_container.button("🗑️", key="remove_button_" + str(x))

            if remove_button:
                st.session_state.selection_flag = False
                st.session_state.selection_interval = 0
                st.session_state.edit_flag = False
                logger.info(f'del\n: {added[x]}')
                del added[x]
                del interval_added_list[x]
                try:
                    with open(added_intervals, 'w', encoding='utf8') as f:
                        json.dump(added, f, ensure_ascii=False, indent=4)
                except FileNotFoundError as e:
                    msg = f'The file {added_intervals} hasn\'t found. ' \
                          f'Please add file {added_intervals}'
                    logger.error(e)
                    st.error(msg)
                    st.stop()
                st.session_state.navigation_tab_flag = True
                st.experimental_rerun()
            st.markdown("""---""")

            if st.session_state.edit_flag and (x == st.session_state.edit_index):
                st.session_state.selection_flag = False
                st.session_state.selection_interval = 0
                logger.info("edit mode")
                down_edit = col2.text_input("Начало периода", value=col_down_datetime, max_chars=17,
                                            key="col2_" + str(x),
                                            type="default", placeholder="ДД/ММ/ГГ ЧЧ:ММ:СС",
                                            label_visibility="collapsed", disabled=False)
                up_edit = col3.text_input("Конец периода", value=col_up_datetime, max_chars=17,
                                          key="col3_" + str(x),
                                          type="default", placeholder="ДД/ММ/ГГ ЧЧ:ММ:СС",
                                          label_visibility="collapsed", disabled=False)
                try:
                    if down_edit != "":
                        # datetime_down_edit = datetime.datetime.strptime(down_edit, '%d/%m/%y %H:%M:%S')
                        datetime_down_edit = pars.parse(down_edit, dayfirst=True,
                                                        default=datetime.datetime(1978, 1, 1, 0, 0))
                        flag_down_edit = True
                    else:
                        col2.error("Введите начало периода")
                except ValueError as e:
                    col2.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")

                try:
                    if up_edit != "":
                        # datetime_up_edit = datetime.datetime.strptime(up_edit, '%d/%m/%y %H:%M:%S')
                        datetime_up_edit = pars.parse(up_edit, dayfirst=True,
                                                      default=datetime.datetime(1978, 1, 1, 0, 0))
                        flag_up_edit = True
                    else:
                        col3.error("Введите начало периода")
                except ValueError as e:
                    col3.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")

                if flag_down_edit and flag_up_edit:
                    try:
                        if datetime_down_edit not in df_common.index.tolist():
                            logger.info(datetime_down_edit)
                            timestamp_down_edit = datetime_down_edit.timestamp()
                            datetime_down_edit = pars.parse(
                                min(df_common.index, key=lambda x: abs(pars.parse(x).timestamp() - timestamp_down_edit)))
                            logger.info(datetime_down_edit)
                            with col2:
                                st.info(f"Начало периода было округлено до "
                                        f"{datetime_down_edit.strftime('%d/%m/%y %H:%M:%S')}")

                        if datetime_up_edit not in df_common.index.tolist():
                            logger.info(datetime_up_edit)
                            timestamp_up_edit = datetime_up_edit.timestamp()
                            datetime_up_edit = pars.parse(
                                min(df_common.index, key=lambda x: abs(pars.parse(x).timestamp() - timestamp_up_edit)))
                            logger.info(datetime_up_edit)
                            with col3:
                                st.info(f"Конец периода был округлен до "
                                        f"{datetime_up_edit.strftime('%d/%m/%y %H:%M:%S')}")

                        datetime_down_edit_index = df_common.index.tolist().index(
                            datetime_down_edit.strftime("%Y-%m-%d %H:%M:%S"))
                        datetime_up_edit_index = df_common.index.tolist().index(
                            datetime_up_edit.strftime("%Y-%m-%d %H:%M:%S"))

                        flag_between_edit = (datetime_up_edit_index <= len(df_common)) and \
                                            (datetime_down_edit_index >= 0)
                        if (datetime_up_edit > datetime_down_edit) and flag_between_edit:
                            interval_begin_edit_index = datetime_down_edit_index
                            interval_end_edit_index = datetime_up_edit_index
                            top_edit_T, measurement = mean_index(loss_df[interval_begin_edit_index:interval_end_edit_index],
                                                                 group_sensors, top_count=st.session_state.top)
                            dictionary_edit = {
                                "time": [str(datetime.datetime.strftime(datetime_down_edit,
                                                                        "%Y-%m-%d %H:%M:%S")),
                                         str(datetime.datetime.strftime(datetime_up_edit,
                                                                        "%Y-%m-%d %H:%M:%S"))],
                                "len": interval_end_edit_index - interval_begin_edit_index,
                                "index": [interval_begin_edit_index, interval_end_edit_index],
                                "top_sensors": top_edit_T,
                                "measurement": measurement
                            }

                            try:
                                with open(added_intervals, 'r', encoding='utf8') as f:
                                    added = json.load(f)
                            except FileNotFoundError as e:
                                msg = f'The file {added_intervals} hasn\'t found. ' \
                                      f'Please add file {added_intervals}'
                                logger.error(e)
                                col1.error(msg)
                                st.stop()

                            try:
                                with open(group_intervals, 'r', encoding='utf8') as f:
                                    group_sensors = json.load(f)
                            except FileNotFoundError as e:
                                msg = f'The file {group_intervals} hasn\'t found. ' \
                                      f'Please add file {group_intervals}'
                                logger.error(e)
                                col1.error(msg)
                                st.stop()

                            if (dictionary_edit not in added) and (dictionary_edit not in group_sensors):
                                del added[x]
                                added.append(dictionary_edit)
                                added.sort(key=lambda added: added["index"][0], reverse=False)
                                sort_correction_json(added)
                                try:
                                    with open(added_intervals, 'w', encoding='utf8') as f:
                                        json.dump(added, f, ensure_ascii=False, indent=4)
                                    st.session_state.edit_flag = False
                                    st.session_state.navigation_tab_flag = True
                                    st.experimental_rerun()
                                except FileNotFoundError as e:
                                    msg = f'The file {added_intervals} hasn\'t found. ' \
                                          f'Please add file {added_intervals}'
                                    logger.error(e)
                                    col1.error(msg)
                                    st.stop()
                            else:
                                logger.error("Введенный период уже добавлен или найден")
                                col1.error("Введенный период уже добавлен или найден")
                        else:
                            logger.error("Конец периода должен быть после начала периода!")
                            col1.error("Конец периода должен быть после начала периода!")

                    except ValueError as e:
                        logger.error("Задано время не из \"пятиминутки\". Добавление не произошло")
                        col1.error("Задано время не из \"пятиминутки\". Добавление не произошло")
            else:
                col2.write(col_down_datetime)
                col3.write(col_up_datetime)

            if edit_button:
                st.session_state.edit_flag = True
                st.session_state.edit_index = x
                st.session_state.navigation_tab_flag = True
                st.experimental_rerun()
        report_button = st.button("Новый отчет", key="report_button")
        if report_button:
            get_pdf_report_streamlit.get_common_report(fig_home, df_common, data_df,
                                                       merged_interval_list, interval_list, tab_name_list,
                                                       WEB_APP_REPORTS, web_app_group, web_app_period_reports,
                                                       merged_top_list, LEFT_SPACE, RIGHT_SPACE,
                                                       PLOT_FEATURES, DROP_LIST, dict_kks,
                                                       home_line_text, tab_line_text)
        try:
            with open(f'{web_app_group}/common_report.pdf', "rb") as pdf_file:
                PDFbyte = pdf_file.read()
            report_common_button = st.download_button("Загрузить отчет", data=PDFbyte,
                                                      file_name=f'common_report.pdf',
                                                      key="download_report_button_",
                                                      mime="application/octet-stream")
        except FileNotFoundError as e:
            logger.info(f'{web_app_group}/common_report.pdf has been created')
    else:
        logger.info(f'tab else {st.session_state.selection_flag}')
        st.session_state.edit_flag = False
        if st.session_state.selection_flag:
            st.session_state.selection_flag = False
            st.session_state.selection_interval = tab_list
            st.experimental_rerun()
        col_label_date, col_pdf_report, col_close_tab = st.columns((10, 5, 5))
        with col_label_date:
            st.markdown("<h5 style='text-align: left; color: #4562a1;'>" +
                        tab_name_list[idx][1:tab_name_list[idx].index(";") - 3] +
                        "  &nbsp&nbsp÷&nbsp&nbsp" + tab_name_list[idx][tab_name_list[idx].index(";") + 1:-4] + "</h5>",
                        unsafe_allow_html=True)
        st.markdown(f'<h6 style="text-align: left; color: #4562a1;">{tab_line_text}</h6>',
                    unsafe_allow_html=True)
        df_common = rolled_df
        col_list = ['target_value']
        fig_tab = get_view_streamlit.tab_plot(idx, df_common, merged_interval_list, col_list, interval_list,
                                              LEFT_SPACE, RIGHT_SPACE)
        st.markdown("<h6 style='text-align: left; color: #4562a1;'>Сигналы, внесшие наибольший вклад</h6>",
                    unsafe_allow_html=True)

        signal_checkbox_list = []
        signal_checked_name_list = []
        for signal in merged_top_list[idx]:
            if signal not in DROP_LIST:
                signal_checkbox = st.checkbox(signal + " (" + dict_kks[signal] + ")", value=True,
                                              key="signal_checkbox" + str(idx) + "_" + signal)
                signal_checkbox_list.append(signal_checkbox)
                signal_checked_name_list.append(signal)
        st.markdown("<h6 style='text-align: left; color: #4562a1;'>Остальные сигналы группы</h6>",
                    unsafe_allow_html=True)
        array = [x[list(x.keys())[0]]['single sensors'] for x in json_dict['groups'] if
                 list(x.keys())[0] == st.session_state.selected_group]
        dict_array = [k for k, v in dict_kks.items() if k in array[0]]
        sensor_other_dict = {}
        for k in dict_kks:
            if k in dict_array:
                sensor_other_dict[k] = dict_kks[k]
        for other_signal in sensor_other_dict:
            if (other_signal not in merged_top_list[idx]) and (other_signal not in PLOT_FEATURES) \
                    and (other_signal not in DROP_LIST):
                signal_checkbox = st.checkbox(other_signal + " (" + dict_kks[other_signal] + ")",
                                              key="signal_checkbox" + str(idx) + "_" + other_signal)
                st.write("\n")
                signal_checkbox_list.append(signal_checkbox)
                signal_checked_name_list.append(other_signal)
        jdx = 0
        tab_dir_name = tab_name_list[idx][1:-1].replace(':', '-').replace('/', '-')
        legend_of_sensors = []
        palette_of_sensors = []
        for signal in signal_checkbox_list:
            if signal:
                st.write("\n")
                st.write("\n")
                st.markdown(
                    "<h6 style='text-align: left; color: #4562a1;'>" + signal_checked_name_list[jdx] + " (" +
                    dict_kks[signal_checked_name_list[jdx]] + ")</h6>", unsafe_allow_html=True)
                df_sensors = data_df
                fig_sensor, legend_of_sensor, palette_of_sensor = get_view_streamlit.sensor_plot(idx, jdx, df_common,
                                                                                                 df_sensors,
                                                                                                 merged_interval_list,
                                                                                                 interval_list,
                                                                                                 signal_checked_name_list,
                                                                                                 PLOT_FEATURES,
                                                                                                 LEFT_SPACE,
                                                                                                 RIGHT_SPACE,
                                                                                                 dict_kks)
                legend_of_sensors.append(legend_of_sensor)
                palette_of_sensors.append(palette_of_sensor)
                try:
                    os.mkdir(f'{web_app_period_reports}/{tab_dir_name}')
                except OSError as e:
                    if e.errno != errno.EEXIST:
                        logger.error(e)
                        st.write(f'Error has been occurred on create {web_app_period_reports}/{tab_dir_name}')
                        st.stop()
                fig_sensor.write_image(f'{web_app_period_reports}/{tab_dir_name}/'
                                       f'sensor_img_{str(idx)}_{str(jdx)}.png', engine="kaleido",
                                       width=1200, height=1000)
            jdx += 1
        with col_pdf_report:
            fig_tab.write_image(f'{web_app_period_reports}/{tab_dir_name}/tab_img.png', engine="kaleido")
            get_pdf_report_streamlit.get_period_report(idx, tab_name_list, tab_dir_name, web_app_period_reports,
                                                       signal_checked_name_list, signal_checkbox_list,
                                                       legend_of_sensors, palette_of_sensors,
                                                       merged_top_list, dict_kks, tab_line_text)
            with open(f'{web_app_period_reports}/report_{tab_dir_name}.pdf', "rb") as pdf_file:
                PDFbyte = pdf_file.read()
            report_tab_button = st.download_button("PDF отчет", data=PDFbyte,
                                                   file_name="report_" + tab_dir_name + ".pdf",
                                                   key="download_button_" + str(idx),
                                                   mime="application/octet-stream")
            if report_tab_button:
                st.write("Новый отчет по периоду создан")

    if report_sidebar_button:
        with st.sidebar:
            progress_bar = st.progress(0)
        get_pdf_report_streamlit.get_common_from_sidebar_report(rolled_df, data_df, group_intervals,
                                                                added_intervals, interval_list, progress_bar,
                                                                web_app_group, web_app_period_reports,
                                                                LEFT_SPACE, RIGHT_SPACE,
                                                                PLOT_FEATURES, DROP_LIST, dict_kks,
                                                                home_line_text, tab_line_text)
        with open(f'{web_app_group}/common_report.pdf', "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        with st.sidebar:
            progress_bar.progress(value=100)
            progress_bar.empty()
            report_download_side_button = st.download_button("Загрузить отчет", data=PDFbyte,
                                                             file_name=f'common_report.pdf',
                                                             key="download_report_button_sidebar",
                                                             mime="application/octet-stream")

if selected_menu == "Дополнения":
    with st.sidebar:
        if st.session_state.checked_method != METHODS[0]:
            st.session_state.checked_method = METHODS[0]
            st.experimental_rerun()
        selected_group_sidebar = st.selectbox("Группа", options=selector_index_group,
                                              key="group_select_box_sidebar", label_visibility="visible", index=0)
        if st.session_state.selected_group != selected_group_sidebar[:selected_group_sidebar.find(' ')]:
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            st.session_state.selection_interval = 0
            st.experimental_rerun()
        logger.info(st.session_state.selected_group)
    st.markdown("<h5 style='text-align: left; color: #4562a1;'>"
                "Гистограмма распределения ошибки восстановления значений датчиков</h5>",
                unsafe_allow_html=True)
    fig_hist = get_view_streamlit.hist_plot(rolled_df, config)

flag_radio = False

if selected_menu == "Настройки":
    st.write(selected_menu)
    left_col, right_col = st.columns(2)
    with left_col:
        left_number_input = st.number_input(label="Ширина отступа в 5-ти минутках слева", min_value=1,
                                            max_value=50000, step=1,
                                            value=st.session_state.LEFT_SPACE, key="left_number_input")
    with right_col:
        right_number_input = st.number_input(label="Ширина отступа в 5-ти минутках справа", min_value=1,
                                             max_value=50000, step=1,
                                             value=st.session_state.RIGHT_SPACE, key="right_number_input")
    st.session_state.LEFT_SPACE = left_number_input
    st.session_state.RIGHT_SPACE = right_number_input

    if st.session_state.PDF_id_flag_radio:
        st.session_state.PDF_id_flag_radio = False
        pdf_orientation_radio = st.radio("Выберите ориентацию страниц при построении PDF-отчетов",
                                         ('Книжная', 'Альбомная'), index=st.session_state.PDF_check_radio_index)
    else:
        pdf_orientation_radio = st.radio("Выберите ориентацию страниц при построении PDF-отчетов",
                                         ('Книжная', 'Альбомная'), index=st.session_state.PDF_check_radio_index)
        st.session_state.PDF_id_flag_radio = True
    if pdf_orientation_radio == "Книжная":
        st.session_state.PDF_check_radio_index = 0
    if pdf_orientation_radio == "Альбомная":
        st.session_state.PDF_check_radio_index = 1
    st.session_state.PDF_check_radio_button = pdf_orientation_radio
    if not st.session_state.PDF_id_flag_radio:
        st.experimental_rerun()
