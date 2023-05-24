import argparse
import datetime
import json
import os

import extra_streamlit_components as stx
import pandas as pd
import streamlit as st
from loguru import logger
from streamlit_option_menu import option_menu

import get_view_streamlit
import get_pdf_report_streamlit
import get_interval_streamlit

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
    mean_loss = data[sensors].mean().sort_values(ascending=False).index[:top_count].to_list()
    return mean_loss


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
            logger.info(added)


# загрузка KKS и описания датчиков группы
@st.cache_data
def load_kks():
    df_kks = pd.read_csv(DICT_KKS, delimiter=';', header=None)
    df_kks = df_kks.loc[~df_kks[0].isin(config_plot_json['DROP_LIST'])]
    # idx = 0
    # while int(st.session_state.selected_group) != int(list(json_dict['groups'][idx].keys())[0]):
    #     idx += 1
    # union_sensors = json_dict['groups'][idx][st.session_state.selected_group]['unions']
    # single_sensors = json_dict['groups'][idx][st.session_state.selected_group]['single sensors']
    # if union_sensors == "null":
    #     group_sensors = single_sensors + PLOT_FEATURES
    # elif single_sensors == "null":
    #     group_sensors = union_sensors + PLOT_FEATURES
    # else:
    #     group_sensors = union_sensors + single_sensors + PLOT_FEATURES
    # print(df_kks)
    # print("***********************")
    # print(group_sensors)
    # df_kks = df_kks.loc[df_kks[0].isin(group_sensors)]
    # print("***********************")
    # print(df_kks)
    # st.stop()
    kks_dict = dict(zip(df_kks[0].to_list(), df_kks[1].to_list()))
    # print(kks_dict)
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

# массив открытых вкладок
# if "opened_tab" not in st.session_state:
#     st.session_state.opened_tab = ["Главная"]


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

parser = argparse.ArgumentParser()
parser.add_argument('--station', type=str, default='')
opt = parser.parse_args()

DATA_DIR = f'Data/'
WEB_APP_DIR = f'web_app/'
WEB_APP_REPORTS_DIR = f'{WEB_APP_DIR}/Reports/'
WEB_APP_REPORTS = f'{WEB_APP_REPORTS_DIR}{st.session_state.checked_method}/'
METHODS = ["Potentials", "LSTM"]
METHODS_DIR = f'{DATA_DIR}{st.session_state.checked_method}/'

# JSON_INTERVAL_DIR = f'{DATA_DIR}/json_interval/'
# JSON_DIR = f'{JSON_INTERVAL_DIR}{st.session_state.checked_method}'
JSON_DIR = f'{METHODS_DIR}json_interval/'

CSV_DATA = f'{DATA_DIR}/csv_data/'
CSV_PREDICT = f'{METHODS_DIR}csv_predict/'
CSV_LOSS = f'{METHODS_DIR}csv_loss/'
# CSV_PREDICT_DIR = f'{DATA_DIR}/csv_predict/'
# CSV_PREDICT = f'{CSV_PREDICT_DIR}{st.session_state.checked_method}'
# CSV_LOSS_DIR = f'{DATA_DIR}/csv_loss/'
# CSV_LOSS = f'{CSV_LOSS_DIR}{st.session_state.checked_method}'

LEFT_SPACE = st.session_state.LEFT_SPACE
RIGHT_SPACE = st.session_state.RIGHT_SPACE

try:
    os.mkdir(f'{WEB_APP_DIR}')
except Exception as e:
    print(e)
    logger.info(f'{WEB_APP_DIR} dir exist!')

try:
    os.mkdir(f'{WEB_APP_REPORTS_DIR}')
except Exception as e:
    print(e)
    logger.info(f'{WEB_APP_REPORTS_DIR} dir exist!')

try:
    os.mkdir(f'{WEB_APP_REPORTS}')
except Exception as e:
    print(e)
    logger.info(f'{WEB_APP_REPORTS} dir exist!')

try:
    os.mkdir(f'{DATA_DIR}')
except Exception as e:
    print(e)
    logger.info(f'{DATA_DIR} dir exist!')

try:
    os.mkdir(f'{CSV_DATA}')
except Exception as e:
    print(e)
    logger.info(f'{CSV_DATA} dir exist!')

for method in METHODS:
    try:
        csv_predict = f'{DATA_DIR}{method}{os.sep}csv_predict{os.sep}'
        csv_loss = f'{DATA_DIR}{method}{os.sep}csv_loss{os.sep}'
        json_dir = f'{DATA_DIR}{method}{os.sep}json_interval{os.sep}'

        os.mkdir(f'{DATA_DIR}{method}')
        os.mkdir(csv_predict)
        os.mkdir(csv_loss)
        os.mkdir(json_dir)

    except Exception as e:
        print(e)
        logger.info(f'{DATA_DIR}{method} dir exist!')

# try:
#     os.mkdir(f'{JSON_INTERVAL_DIR}')
# except Exception as e:
#     print(e)
#     logger.info(f'{JSON_INTERVAL_DIR} dir exist!')


# try:
#     os.mkdir(f'{CSV_PREDICT_DIR}')
# except Exception as e:
#     print(e)
#     logger.info(f'{CSV_PREDICT_DIR} dir exist!')

# try:
#     os.mkdir(f'{CSV_LOSS_DIR}')
# except Exception as e:
#     print(e)
#     logger.info(f'{CSV_LOSS_DIR} dir exist!')

# try:
#     os.mkdir(f'{JSON_DIR}')
# except Exception as e:
#     print(e)
#     logger.info(f'{JSON_DIR} dir exist!')

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

index_group = [list(x.keys())[0] for x in json_dict["groups"]]
if index_group[0] == '0':
    index_group.remove('0')
logger.info(f'groups: {index_group}')

# index_group = [x+" "+json_dict["groups"]["name"] for x in index_group]
selector_index_group = [x + " " + "(" + json_dict["groups"][int(x)][str(x)]['name'] + ")" for x in index_group]

for group in index_group:
    web_app_group = f'{WEB_APP_REPORTS}/group_{group}/'

    try:
        os.mkdir(f'{web_app_group}')
    except Exception as e:
        print(e)
        logger.info(f'{web_app_group} dir exist!')

    web_app_period_reports = f'{web_app_group}/periods'
    try:
        os.mkdir(f'{web_app_period_reports}/')
    except Exception as e:
        print(e)
        logger.info(f'{web_app_period_reports} dir exist!')

if not st.session_state.flag_group:
    st.session_state.flag_group = True
    st.session_state.selected_group = index_group[0]

CSV_DATA_NAME = f'{CSV_DATA}/slices.csv'
CSV_PREDICT_NAME = f'{CSV_PREDICT}/predict_{st.session_state.selected_group}.csv'
CSV_LOSS_NAME = f'{CSV_LOSS}/loss_{st.session_state.selected_group}.csv'

added_intervals = f'{JSON_DIR}/added_intervals_{st.session_state.selected_group}.json'
group_intervals = f'{JSON_DIR}/group_{st.session_state.selected_group}.json'
interval_list = []
top_list = []
interval_added_list = []
top_added_list = []

# получение данных csv группы по вероятности аномалии
try:
    logger.info(f'Read_file: {CSV_PREDICT_NAME}.csv')
    anomaly_time_df = pd.read_csv(f'{CSV_PREDICT_NAME}')
    anomaly_time_df.fillna(method='ffill', inplace=True)
    anomaly_time_df.fillna(value={"target_value": 0}, inplace=True)
    anomaly_time_df.index = anomaly_time_df['timestamp']
    anomaly_time_df = anomaly_time_df.drop(columns=['timestamp'])
except Exception as e:
    print(e)
    logger.error(e)

# получение данных csv по вкладам датчиков в аномалию
try:
    logger.info(f'Read_file: {CSV_LOSS_NAME}')
    loss_df = pd.read_csv(f'{CSV_LOSS_NAME}')
    loss_df.index = loss_df['timestamp']
    loss_df = loss_df.drop(columns=['timestamp'])
except Exception as e:
    print(e)
    logger.error(e)

# получение исходных данных csv
try:
    logger.info(f'Read_file: {CSV_DATA_NAME}')
    data_df = pd.read_csv(f'{CSV_DATA_NAME}')
    data_df.index = data_df['timestamp']
    data_df = data_df.drop(columns=['timestamp'])
    # data_df.fillna(data_df.mean(), inplace=True)
except Exception as e:
    print(e)
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
    print(e)
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

        # selected_group_sidebar = st.selectbox("Группа", options=index_group,
        #                                       key="group_select_box_sidebar", label_visibility="visible", index=0)
        selected_group_sidebar = st.selectbox("Группа", options=selector_index_group,
                                              key="group_select_box_sidebar", label_visibility="visible", index=0)
        st.session_state.selected_name = selected_group_sidebar
        if st.session_state.checked_method != method_radio:
            st.session_state.checked_method = method_radio
            # st.session_state.opened_tab = ["Главная"]
            # st.session_state.selected_group = selected_group_sidebar
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            st.session_state.selection_interval = 0
            st.experimental_rerun()
        # if st.session_state.selected_group != selected_group_sidebar:
        if st.session_state.selected_group != selected_group_sidebar[:selected_group_sidebar.find(' ')]:
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            # st.session_state.opened_tab = ["Главная"]
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
        # if tab in st.session_state.opened_tab:
        #     tab_bar_item = stx.TabBarItemData(id=tab_name_list.index(tab), title=tab, description="")
        #     tab_bar_list.append(tab_bar_item)
        #     tab_sidebar_list.append(tab)
        #     count += 1
    with st.sidebar:
        selected_interval_sidebar = st.selectbox("Выберите период", tab_sidebar_list,
                                                 index=int(st.session_state.selection_interval),
                                                 key="intervals_select_box_sidebar", label_visibility="visible")
        if selected_interval_sidebar == "Главная":
            with st.form("interval detection"):
                st.write("Выделение интервалов")
                short_col, long_col = st.columns(2)
                with short_col:
                    short_threshold = st.number_input(label="SHORT_THRESHOLD", min_value=1, max_value=100, value=96,
                                                      key="SHORT_THRESHOLD")
                    len_short_anomaly = st.number_input(label="LEN_SHORT_ANOMALY", min_value=0, value=72,
                                                        key="LEN_SHORT_ANOMALY")
                    count_continue_short = st.number_input(label="COUNT_CONTINUE_SHORT", min_value=0, value=5,
                                                           key="COUNT_CONTINUE_SHORT")
                with long_col:
                    long_threshold = st.number_input(label="LONG_THRESHOLD", min_value=1, max_value=100, value=86,
                                                     key="LONG_THRESHOLD")
                    len_long_anomaly = st.number_input(label="LEN_LONG_ANOMALY", min_value=0, value=288,
                                                       key="LEN_LONG_ANOMALY")
                    count_continue_long = st.number_input(label="COUNT_CONTINUE_LONG", min_value=0, value=5,
                                                          key="COUNT_CONTINUE_LONG")
                submitted_interval_detection = st.form_submit_button("Запустить выделение интервалов")
                if submitted_interval_detection:
                    st.write("Выделение интервалов")
                    get_interval_streamlit.rebuilt_anomaly_interval_streamlit(CSV_PREDICT, JSON_DIR, CSV_LOSS,
                                                                              short_threshold,
                                                                              len_short_anomaly,
                                                                              count_continue_short,
                                                                              long_threshold,
                                                                              len_long_anomaly,
                                                                              count_continue_long)
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
        df_common = anomaly_time_df
        # if st.session_state.checked_method == "LSTM":
        #     col_list = ['loss']
        # else:
        #     col_list = ['P']
        col_list = ['target_value']
        anomaly_interval = [0, len(df_common)]
        fig_home = get_view_streamlit.home_plot(df_common, anomaly_interval, col_list, interval_list, config)
        st.markdown("<h5 style='text-align: left; color: #4562a1;'>Найденные периоды</h5>",
                    unsafe_allow_html=True)

        found_interval, empty_interval_col = st.columns([5, 5])
        with found_interval:
            if st.session_state.selection_flag:
                st.session_state.selection_flag = False
                st.session_state.selection_interval = tab_list
            # tab_show_name = [i for i in tab_name_list if i not in st.session_state.opened_tab[1:]]
            # selected_interval = st.selectbox("Выберите период", tab_show_name,
            #                                  key="intervals_select_box", label_visibility="visible")
            selected_interval = st.selectbox("Выберите период", tab_sidebar_list,
                                             key="intervals_select_box", label_visibility="visible")
            if (selected_interval != tab_name_list[0]) \
                    and (selected_interval != tab_name_list.index(selected_interval)) \
                    and (not st.session_state.selection_flag):
                # if selected_interval not in st.session_state.opened_tab:
                # st.session_state.opened_tab.append(selected_interval)
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
                        datetime_down_time = datetime.datetime.strptime(down_time, '%d/%m/%y %H:%M:%S')
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
                        datetime_up_time = datetime.datetime.strptime(up_time, '%d/%m/%y %H:%M:%S')
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
                        datetime_down_time_index = df_common.index.tolist().index(
                            datetime_down_time.strftime("%Y-%m-%d %H:%M:%S"))
                        datetime_up_time_index = df_common.index.tolist().index(
                            datetime_up_time.strftime("%Y-%m-%d %H:%M:%S"))

                        flag_between_time = (datetime_up_time_index <= len(df_common)) and \
                                            (datetime_down_time_index >= 0)
                        if (datetime_up_time > datetime_down_time) and flag_between_time:
                            interval_begin_index = datetime_down_time_index
                            interval_end_index = datetime_up_time_index
                            top_T = mean_index(loss_df[interval_begin_index:interval_end_index], group_sensors)
                            dictionary = {
                                "time": [str(datetime.datetime.strftime(datetime_down_time,
                                                                        "%Y-%m-%d %H:%M:%S")),
                                         str(datetime.datetime.strftime(datetime_up_time,
                                                                        "%Y-%m-%d %H:%M:%S"))],
                                "len": interval_end_index - interval_begin_index,
                                "index": [interval_begin_index, interval_end_index],
                                "top_sensors": top_T
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

                            if not added:
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
                        datetime_down_edit = datetime.datetime.strptime(down_edit, '%d/%m/%y %H:%M:%S')
                        flag_down_edit = True
                    else:
                        col2.error("Введите начало периода")
                except ValueError as e:
                    col2.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")

                try:
                    if up_edit != "":
                        datetime_up_edit = datetime.datetime.strptime(up_edit, '%d/%m/%y %H:%M:%S')
                        flag_up_edit = True
                    else:
                        col3.error("Введите начало периода")
                except ValueError as e:
                    col3.error("Не соответствует формату ДД/ММ/ГГ ЧЧ:ММ:СС")

                if flag_down_edit and flag_up_edit:
                    try:
                        datetime_down_edit_index = df_common.index.tolist().index(
                            datetime_down_edit.strftime("%Y-%m-%d %H:%M:%S"))
                        datetime_up_edit_index = df_common.index.tolist().index(
                            datetime_up_edit.strftime("%Y-%m-%d %H:%M:%S"))

                        flag_between_edit = (datetime_up_edit_index <= len(df_common)) and \
                                            (datetime_down_edit_index >= 0)
                        if (datetime_up_edit > datetime_down_edit) and flag_between_edit:
                            interval_begin_edit_index = datetime_down_edit_index
                            interval_end_edit_index = datetime_up_edit_index
                            top_edit_T = mean_index(loss_df[interval_begin_edit_index:interval_end_edit_index],
                                                    group_sensors)
                            dictionary_edit = {
                                "time": [str(datetime.datetime.strftime(datetime_down_edit,
                                                                        "%Y-%m-%d %H:%M:%S")),
                                         str(datetime.datetime.strftime(datetime_up_edit,
                                                                        "%Y-%m-%d %H:%M:%S"))],
                                "len": interval_end_edit_index - interval_begin_edit_index,
                                "index": [interval_begin_edit_index, interval_end_edit_index],
                                "top_sensors": top_edit_T
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
                                                       PLOT_FEATURES, DROP_LIST, dict_kks, config,
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
        df_common = anomaly_time_df
        # if st.session_state.checked_method == "LSTM":
        #     col_list = ['loss']
        # if st.session_state.checked_method == "Potentials":
        #     col_list = ['P']
        col_list = ['target_value']
        fig_tab = get_view_streamlit.tab_plot(idx, df_common, merged_interval_list, col_list, interval_list,
                                              LEFT_SPACE, RIGHT_SPACE, config)
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
                                                                                                 dict_kks, config)
                legend_of_sensors.append(legend_of_sensor)
                palette_of_sensors.append(palette_of_sensor)
                try:
                    os.mkdir(f'{web_app_period_reports}/{tab_dir_name}')
                except Exception as e:
                    print(e)
                    logger.info('Reports dir exist!')
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
        # with col_close_tab:
        #     close_tab_button = st.button("Закрыть вкладку", key="close_tab_button_" + str(idx))
        #     if close_tab_button:
        #         st.session_state.opened_tab.remove(tab_name_list[idx])
        #         st.session_state.selection_interval = 0
        #         st.experimental_rerun()

    if report_sidebar_button:
        with st.sidebar:
            progress_bar = st.progress(0)
        get_pdf_report_streamlit.get_common_from_sidebar_report(anomaly_time_df, data_df, group_intervals,
                                                                added_intervals, interval_list, progress_bar,
                                                                web_app_group, web_app_period_reports,
                                                                LEFT_SPACE, RIGHT_SPACE,
                                                                PLOT_FEATURES, DROP_LIST, dict_kks, config,
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
        # selected_group_sidebar = st.selectbox("Группа", options=index_group,
        #                                       key="group_select_box_sidebar", label_visibility="visible", index=0)
        # if st.session_state.selected_group != selected_group_sidebar:
        #     st.session_state.selected_group = selected_group_sidebar
        selected_group_sidebar = st.selectbox("Группа", options=selector_index_group,
                                              key="group_select_box_sidebar", label_visibility="visible", index=0)
        if st.session_state.selected_group != selected_group_sidebar[:selected_group_sidebar.find(' ')]:
            st.session_state.selected_group = selected_group_sidebar[:selected_group_sidebar.find(' ')]
            # st.session_state.opened_tab = ["Главная"]
            st.session_state.selection_interval = 0
            st.experimental_rerun()
        logger.info(st.session_state.selected_group)
    st.markdown("<h5 style='text-align: left; color: #4562a1;'>"
                "Гистограмма распределения ошибки восстановления значений датчиков</h5>",
                unsafe_allow_html=True)
    fig_hist = get_view_streamlit.hist_plot(anomaly_time_df, config)

flag_radio = False

if selected_menu == "Настройки":
    st.write(selected_menu)
    left_col, right_col = st.columns(2)
    with left_col:
        left_number_input = st.number_input(label="Ширина отступа в 5-ти минутках слева", min_value=10,
                                            max_value=50000, step=1,
                                            value=st.session_state.LEFT_SPACE, key="left_number_input")
    with right_col:
        right_number_input = st.number_input(label="Ширина отступа в 5-ти минутках справа", min_value=10,
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