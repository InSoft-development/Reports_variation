import datetime
import json
import os

import streamlit as st
from loguru import logger
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

import get_fig_streamlit


styles = getSampleStyleSheet()  # Стили для отчетов по умолчанию


# форматирование текста отчета Times New Roman
def StringGuy(text):
    return f'<font name="TNR">{text}</font>'


# форматирование текста легенды
def StringGuy_legend(text, color):
    return f'<font name="TNR">{text[:text.index(":")]}' \
           f'</font><font name="TNR" color={color}>{text[text.index(":"):]}</font>'


# форматирование обычного абзаца
def ParagGuy(text, style=styles['Normal']):
    return Paragraph(StringGuy(text), style)


# форматирование абзаца легенды
def ParagGuy_legend(text, color, style=styles['Normal']):
    return Paragraph(StringGuy_legend(text, color), style)


def get_common_report(fig_home, df_common, data_df, merged_interval_list, interval_list, tab_name_list,
                      WEB_APP_REPORTS, web_app_group, web_app_period_reports,  merged_top_list,
                      LEFT_SPACE, RIGHT_SPACE, PLOT_FEATURES, DROP_LIST, dict_kks, config, home_text, tab_text):
    progress_report_bar = st.progress(value=0)
    fig_home.write_image(f'{WEB_APP_REPORTS}/home_img.png', engine="kaleido", width=900, height=800)

    headline_style = styles["Heading1"]
    headline_style.alignment = TA_CENTER
    headline_style.fontSize = 24
    headline_style.textColor = "#4562a1"

    subheadline_style = styles["Heading2"]
    subheadline_style.textColor = "#4562a1"

    pdfmetrics.registerFont(TTFont('TNR', 'times.ttf', 'UTF-8'))
    if st.session_state.PDF_check_radio_button == "Альбомная":
        doc = SimpleDocTemplate(f'{web_app_group}/common_report.pdf',
                                pagesize=landscape(letter), rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.25
    else:
        doc = SimpleDocTemplate(f'{web_app_group}/common_report.pdf',
                                pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.0
    Story = []

    Story.append(ParagGuy(f'Метод {st.session_state.checked_method}', headline_style))
    Story.append(ParagGuy("Отчет по всем периодам группы " + str(st.session_state.selected_name), headline_style))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy(home_text, subheadline_style))
    Story.append(Spacer(1, 12))

    path_tab_img = f'{WEB_APP_REPORTS}/home_img.png'
    im = Image(path_tab_img, 8 * inch * scale, 4 * inch * scale)
    Story.append(im)

    Story.append(ParagGuy("Найденные и добавленные периоды", subheadline_style))
    count = 1
    for period in tab_name_list[1:]:
        # ptext = str(count) + ") " + period[1:-1]
        ptext = str(count) + ") " + period[
                                    1:period.index(";") - 3] + " " + "&nbsp" * 2 + "÷" + "&nbsp" * 2 + " " + period[
                                                                                                             period.index(
                                                                                                                 ";") + 1:-4]
        Story.append(ParagGuy(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        count += 1
    Story.append(PageBreak())

    count = 1
    for period in tab_name_list[1:]:
        progress_report_bar.progress(int(count / len(tab_name_list) * 100))
        # Story.append(ParagGuy(f'Период {period[1:-1]}', headline_style))
        Story.append(ParagGuy(
            f'Период {period[1:period.index(";") - 3]} &nbsp&nbsp÷&nbsp&nbsp {period[period.index(";") + 1:-4]}'
            , headline_style))
        Story.append(Spacer(1, 12))
        Story.append(ParagGuy(tab_text, subheadline_style))
        Story.append(Spacer(1, 12))

        tab_dir_name = period[1:-1].replace(':', '-').replace('/', '-').replace(" ", "_").replace(";", "--")
        try:
            os.mkdir(f'{web_app_period_reports}/{tab_dir_name}')
        except Exception as e:
            print(e)
            logger.info('Reports dir exist!')
        tab_fig = get_fig_streamlit.get_tab_fig_potentials(df_common, merged_interval_list[count], interval_list,
                                                           LEFT_SPACE, RIGHT_SPACE, config)
        tab_fig.write_image(f'{web_app_period_reports}/{tab_dir_name}/tab_img.png', engine="kaleido")
        path_tab_fig = f'{web_app_period_reports}/{tab_dir_name}/tab_img.png'
        im = Image(path_tab_fig, 8 * inch * scale, 4 * inch * scale)
        Story.append(im)

        Story.append(ParagGuy("Сигналы, внесшие наибольший вклад:", subheadline_style))
        Story.append(Spacer(1, 12))

        for top in merged_top_list[count]:
            if top not in DROP_LIST:
                ptext = top + " (" + dict_kks[top] + ")"
                Story.append(ParagGuy(ptext, styles["Normal"]))
                Story.append(Spacer(1, 12))

        Story.append(PageBreak())

        for top in merged_top_list[count]:
            if top not in DROP_LIST:
                ptext = top + " (" + dict_kks[top] + ")"
                Story.append(ParagGuy(ptext, subheadline_style))

                df_sensors = data_df
                sensor_fig, legend_list, palette_list = \
                    get_fig_streamlit.get_sensor_fig_potentials(df_common, df_sensors, top, merged_interval_list[count],
                                                                interval_list,
                                                                LEFT_SPACE, RIGHT_SPACE, PLOT_FEATURES, config)
                sensor_fig.write_image(f'{web_app_period_reports}/{tab_dir_name}/'
                                       f'sensor_img_{top}.png', engine="kaleido", width=1200, height=1000)

                path_sensor_fig = f'{web_app_period_reports}/{tab_dir_name}/sensor_img_{top}.png'
                im = Image(path_sensor_fig, 7 * inch * scale, 4 * inch * scale)
                Story.append(im)

                pallete_count = 0
                for leg in legend_list:
                    if pallete_count == 0:
                        ptext = "Основной сигнал: " + leg + " (" + dict_kks[leg] + ")"
                        Story.append(ParagGuy_legend(ptext, palette_list[0], styles["Normal"]))
                        Story.append(Spacer(1, 12))
                    else:
                        ptext = "Дополнительный сигнал: " + leg + " (" + dict_kks[leg] + ")"
                        Story.append(ParagGuy_legend(ptext, palette_list[pallete_count],
                                                     styles["Normal"]))
                        Story.append(Spacer(1, 12))
                    pallete_count += 1
                Story.append(PageBreak())
        count += 1
    doc.build(Story)
    progress_report_bar.progress(value=100)
    progress_report_bar.empty()
    logger.info("New report has been created")
    st.write("Новый отчет создан")


def get_common_from_sidebar_report(anomaly_time_df, data_df,
                                   group_intervals, added_intervals, interval_list, progress_bar,
                                   web_app_group, web_app_period_reports, LEFT_SPACE, RIGHT_SPACE,
                                   PLOT_FEATURES, DROP_LIST, dict_kks, config, home_text, tab_text):
    tab_name_list = ["Главная"]
    df_common = anomaly_time_df
    anomaly_interval = [0, len(df_common)]
    try:
        f = open(group_intervals, 'r')
        j = json.load(f)
    except Exception as e:
        print(e)
        logger.error(e)
    try:
        with open(added_intervals, 'r', encoding='utf8') as f:
            added = json.load(f)
    except FileNotFoundError as e:
        msg = f'The file {added_intervals} hasn\'t found. ' \
              f'Please add file {added_intervals}'
        logger.error(e)
        st.error(msg)
        st.stop()

    interval_added_list = []
    top_added_list = []
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

    fig_home = get_fig_streamlit.get_home_fig_potentials(df_common, anomaly_interval, interval_list, config)
    fig_home.write_image(f'{web_app_group}/home_img.png', engine="kaleido", width=900, height=800)

    styles = getSampleStyleSheet()
    headline_style = styles["Heading1"]
    headline_style.alignment = TA_CENTER
    headline_style.fontSize = 24
    headline_style.textColor = "#4562a1"

    subheadline_style = styles["Heading2"]
    subheadline_style.textColor = "#4562a1"

    pdfmetrics.registerFont(TTFont('TNR', 'times.ttf', 'UTF-8'))
    if st.session_state.PDF_check_radio_button == "Альбомная":
        doc = SimpleDocTemplate(f'{web_app_group}/common_report.pdf',
                                pagesize=landscape(letter), rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.25
    else:
        doc = SimpleDocTemplate(f'{web_app_group}/common_report.pdf',
                                pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.0
    Story = []
    Story.append(ParagGuy(f'Метод {st.session_state.checked_method}', headline_style))
    Story.append(ParagGuy("Отчет по всем периодам группы " + str(st.session_state.selected_name), headline_style))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy(home_text, subheadline_style))
    Story.append(Spacer(1, 12))

    path_tab_img = f'{web_app_group}/home_img.png'
    im = Image(path_tab_img, 8 * inch * scale, 4 * inch * scale)
    Story.append(im)

    Story.append(ParagGuy("Найденные и добавленные периоды", subheadline_style))
    count = 1
    for period in tab_name_list[1:]:
        ptext = str(count) + ") " + period[
                                    1:period.index(";") - 3] + " " + "&nbsp" * 2 + "÷" + "&nbsp" * 2 + " " + period[
                                                                                                             period.index(
                                                                                                                 ";") + 1:-4]
        Story.append(ParagGuy(ptext, styles["Normal"]))
        Story.append(Spacer(1, 12))
        count += 1
    Story.append(PageBreak())

    count = 1
    for period in tab_name_list[1:]:
        with st.sidebar:
            progress_bar.progress(value=int(count / len(tab_name_list) * 100))
        Story.append(ParagGuy(
            f'Период {period[1:period.index(";") - 3]} &nbsp&nbsp÷&nbsp&nbsp {period[period.index(";") + 1:-4]}'
            , headline_style))
        Story.append(Spacer(1, 12))
        Story.append(ParagGuy(tab_text, subheadline_style))
        Story.append(Spacer(1, 12))

        tab_dir_name = period[1:-1].replace(':', '-').replace('/', '-').replace(" ", "_").replace(";", "--")
        try:
            os.mkdir(f'{web_app_period_reports}/{tab_dir_name}')
        except Exception as e:
            print(e)
            logger.info('Reports dir exist!')
        tab_fig = get_fig_streamlit.get_tab_fig_potentials(df_common, merged_interval_list[count], interval_list,
                                                           LEFT_SPACE, RIGHT_SPACE, config)
        tab_fig.write_image(f'{web_app_period_reports}/{tab_dir_name}/tab_img.png', engine="kaleido")
        path_tab_fig = f'{web_app_period_reports}/{tab_dir_name}/tab_img.png'
        im = Image(path_tab_fig, 8 * inch * scale, 4 * inch * scale)
        Story.append(im)

        Story.append(ParagGuy("Сигналы, внесшие наибольший вклад:", subheadline_style))
        Story.append(Spacer(1, 12))

        for top in merged_top_list[count]:
            if top not in DROP_LIST:
                ptext = top + " (" + dict_kks[top] + ")"
                Story.append(ParagGuy(ptext, styles["Normal"]))
                Story.append(Spacer(1, 12))

        Story.append(PageBreak())
        df_sensors = data_df
        for top in merged_top_list[count]:
            if top not in DROP_LIST:
                ptext = top + " (" + dict_kks[top] + ")"
                Story.append(ParagGuy(ptext, subheadline_style))

                sensor_fig, legend_list, palette_list = \
                    get_fig_streamlit.get_sensor_fig_potentials(df_common, df_sensors, top, merged_interval_list[count],
                                                                interval_list,
                                                                LEFT_SPACE, RIGHT_SPACE, PLOT_FEATURES, config)
                sensor_fig.write_image(f'{web_app_period_reports}/{tab_dir_name}/'
                                       f'sensor_img_{top}.png', engine="kaleido", width=1200, height=1000)

                path_sensor_fig = f'{web_app_period_reports}/{tab_dir_name}/sensor_img_{top}.png'
                im = Image(path_sensor_fig, 7 * inch * scale, 4 * inch * scale)
                Story.append(im)

                pallete_count = 0
                for leg in legend_list:
                    if pallete_count == 0:
                        ptext = "Основной сигнал: " + leg + " (" + dict_kks[leg] + ")"
                        Story.append(ParagGuy_legend(ptext, palette_list[0], styles["Normal"]))
                        Story.append(Spacer(1, 12))
                    else:
                        ptext = "Дополнительный сигнал: " + leg + " (" + dict_kks[leg] + ")"
                        Story.append(ParagGuy_legend(ptext, palette_list[pallete_count],
                                                     styles["Normal"]))
                        Story.append(Spacer(1, 12))
                    pallete_count += 1
                Story.append(PageBreak())

        # Предложения по графикам от Саши
        # sensor_another_fig, sensor_other_fig_list = get_fig_streamlit.get_another_sensor_fig_potentials(df_common, df_sensors,
        #                                                                                      merged_top_list[count],
        #                                                                                      merged_interval_list[
        #                                                                                          count],
        #                                                                                      interval_list,
        #                                                                                      dict_kks,
        #                                                                                      LEFT_SPACE,
        #                                                                                      RIGHT_SPACE,
        #                                                                                      PLOT_FEATURES, DROP_LIST,
        #                                                                                      config)
        # sensor_another_fig.write_image(f'{web_app_group}/sensor_another_fig_{count}.png',
        #                                engine="kaleido", width=1200, height=1000)
        # naming_temp = 0
        # for fig_others in sensor_other_fig_list:
        #     fig_others.write_image(f'{web_app_group}/sensor_other_fig_{count}_{naming_temp}.png',
        #                            engine="kaleido", width=1200, height=1000)
        #     naming_temp += 1
        #
        #
        # # sensor_other_fig.write_image(f'{WEB_APP_REPORTS}/sensor_other_fig_{count}.png',
        # #                                engine="kaleido", width=1200, height=1000)
        count += 1
    doc.build(Story)
    logger.info("New report has been created")


def get_period_report(idx, tab_name_list, tab_dir_name, web_app_period_reports,
                      signal_checked_name_list, signal_checkbox_list, legend_of_sensors, palette_of_sensors,
                      merged_top_list, dict_kks, tab_text):
    headline_style = styles["Heading1"]
    headline_style.alignment = TA_CENTER
    headline_style.fontSize = 24
    headline_style.textColor = "#4562a1"

    subheadline_style = styles["Heading2"]
    subheadline_style.textColor = "#4562a1"

    pdfmetrics.registerFont(TTFont('TNR', 'times.ttf', 'UTF-8'))
    if st.session_state.PDF_check_radio_button == "Альбомная":
        doc = SimpleDocTemplate(f'{web_app_period_reports}/report_{tab_dir_name}.pdf',
                                pagesize=landscape(letter), rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.25
    else:
        doc = SimpleDocTemplate(f'{web_app_period_reports}/report_{tab_dir_name}.pdf',
                                pagesize=letter, rightMargin=72, leftMargin=72, topMargin=72,
                                bottomMargin=18)
        scale = 1.0

    Story = []

    Story.append(ParagGuy(f'Метод {st.session_state.checked_method}', headline_style))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy("Группа " + str(st.session_state.selected_name), headline_style))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy(
        f'Период {tab_name_list[idx][1:tab_name_list[idx].index(";") - 3]}'
        f' &nbsp&nbsp÷&nbsp&nbsp {tab_name_list[idx][tab_name_list[idx].index(";") + 1:-4]}'
        , headline_style))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy(tab_text, subheadline_style))
    Story.append(Spacer(1, 12))

    path_tab_img = f'{web_app_period_reports}/{tab_dir_name}/tab_img.png'
    im = Image(path_tab_img, 8 * inch * scale, 4 * inch * scale)
    Story.append(im)

    Story.append(ParagGuy("Выбранные сигналы, внесшие наибольший вклад:", subheadline_style))
    Story.append(Spacer(1, 12))
    for i in range(0, len(signal_checked_name_list)):
        if signal_checkbox_list[i] and (signal_checked_name_list[i] in merged_top_list[idx]):
            ptext = signal_checked_name_list[i] + " (" + dict_kks[signal_checked_name_list[i]] + ")"
            Story.append(ParagGuy(ptext, styles["Normal"]))
            Story.append(Spacer(1, 12))
    Story.append(Spacer(1, 12))
    Story.append(ParagGuy("Остальные выбранные сигналы группы:", subheadline_style))
    Story.append(Spacer(1, 12))
    for i in range(0, len(signal_checked_name_list)):
        if signal_checkbox_list[i] and (signal_checked_name_list[i] not in merged_top_list[idx]):
            ptext = signal_checked_name_list[i] + " (" + dict_kks[signal_checked_name_list[i]] + ")"
            Story.append(ParagGuy(ptext, styles["Normal"]))
            Story.append(Spacer(1, 12))
    Story.append(PageBreak())
    jdx = 0
    leg_index = 0
    for j in signal_checked_name_list:
        if signal_checkbox_list[jdx]:
            ptext = j + " (" + dict_kks[j] + ")"
            Story.append(ParagGuy(ptext, subheadline_style))
            path_tab_img = f'{web_app_period_reports}/{tab_dir_name}/sensor_img_{str(idx)}_{str(jdx)}.png'
            im = Image(path_tab_img, 7 * inch * scale, 4 * inch * scale)
            Story.append(im)
            pallete_count = 0
            for leg in legend_of_sensors[leg_index]:

                if leg == signal_checked_name_list[jdx]:
                    ptext = "Основной сигнал: " + leg + " (" + dict_kks[leg] + ")"
                    Story.append(ParagGuy_legend(ptext, palette_of_sensors[leg_index][0], styles["Normal"]))
                    Story.append(Spacer(1, 12))
                else:
                    ptext = "Дополнительный сигнал: " + leg + " (" + dict_kks[leg] + ")"
                    Story.append(ParagGuy_legend(ptext, palette_of_sensors[leg_index][pallete_count], styles["Normal"]))
                    Story.append(Spacer(1, 12))
                pallete_count += 1
            leg_index += 1
            Story.append(PageBreak())
        jdx += 1
    doc.build(Story)
    logger.info("New period report has been created")
