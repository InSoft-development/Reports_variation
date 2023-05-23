import streamlit as st

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd
import numpy as np
import scipy.stats


# отрисовка графика вероятности по всем периодам группы
@st.cache_data()
def home_plot(df_common, anomaly_interval, col_list, interval_list, config):
    fig = px.line(
        df_common.iloc[anomaly_interval[0]:anomaly_interval[-1]],
        x=df_common.iloc[anomaly_interval[0]:anomaly_interval[-1]].index.to_list(),
        y=col_list,
        width=10,
        color_discrete_sequence=["#3366CC"]
    )
    fig.layout.yaxis = {}
    fig.layout.xaxis = {}
    fig.update_layout(
        showlegend=False
    )
    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    for interval in interval_list:
        if (interval[0] - config["model"]["delta_tau_P"] * config["number_of_samples"]) <= 0:
            fig.add_vrect(
                x0=df_common.index[interval[0]],
                x1=df_common.index[interval[-1]],
                line_width=1, line_color="red", layer="below")
        else:
            fig.add_vrect(
                x0=df_common.index[interval[0] - config["model"]["delta_tau_P"] * config["number_of_samples"]],
                x1=df_common.index[interval[-1]],
                line_width=1, line_color="red", layer="below")
    st.plotly_chart(fig, config=dict(displayModeBar=False, scrollZoom=True), use_container_width=True)
    return fig


# отрисовка графика вероятности определенного периода
@st.cache_data
def tab_plot(idx, df_common, merged_interval_list, col_list, interval_list, LEFT_SPACE, RIGHT_SPACE, config):

    if merged_interval_list[idx][0] > LEFT_SPACE:
        left_space = LEFT_SPACE
    else:
        left_space = 0
    if merged_interval_list[idx][-1] < (len(df_common) - RIGHT_SPACE):
        right_space = RIGHT_SPACE
    else:
        right_space = 0
    anomaly_tab_interval = [merged_interval_list[idx][0] - left_space, merged_interval_list[idx][-1] + right_space]

    fig = px.line(
        df_common.iloc[anomaly_tab_interval[0]:anomaly_tab_interval[-1]],
        x=df_common.iloc[anomaly_tab_interval[0]:anomaly_tab_interval[-1]].index.to_list(),
        y=col_list,
        color_discrete_sequence=["#3366CC"]
    )
    fig.layout.yaxis = {}
    fig.layout.xaxis = {}
    fig.update_layout(
        showlegend=False,
    )
    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    if merged_interval_list[idx] in interval_list:
        if (merged_interval_list[idx][0] - config["model"]["delta_tau_P"] * config["number_of_samples"]) <= 0:
            fig.add_vrect(x0=df_common.index[merged_interval_list[idx][0]],
                          x1=df_common.index[merged_interval_list[idx][-1]], line_width=2, line_color="red", layer="below")
        else:
            fig.add_vrect(x0=df_common.index[merged_interval_list[idx][0] -
                                             config["model"]["delta_tau_P"] * config["number_of_samples"]],
                          x1=df_common.index[merged_interval_list[idx][-1]], line_width=2, line_color="red",
                          layer="below")
    st.plotly_chart(fig, config=dict(displayModeBar=False, scrollZoom=True), use_container_width=True)
    return fig


# отрисовка многоосевых графиков
def sensor_plot(idx, jdx, df_common, df_sensors, merged_interval_list, interval_list, signal_checked_name_list,
                PLOT_FEATURES, LEFT_SPACE, RIGHT_SPACE, dict_kks, config):
    if signal_checked_name_list[jdx] not in PLOT_FEATURES:
        col_sensors_list = [signal_checked_name_list[jdx]] + PLOT_FEATURES
    else:
        col_sensors_list = [signal_checked_name_list[jdx]]
        for plot_signal in PLOT_FEATURES:
            if plot_signal != signal_checked_name_list[jdx]:
                col_sensors_list.append(plot_signal)

    if merged_interval_list[idx][0] > LEFT_SPACE:
        left_space = LEFT_SPACE
    else:
        left_space = 0
    if merged_interval_list[idx][-1] < (len(df_common) - RIGHT_SPACE):
        right_space = RIGHT_SPACE
    else:
        right_space = 0
    anomaly_sensors_interval = [merged_interval_list[idx][0] - left_space, merged_interval_list[idx][-1] + right_space]

    fig_container = st.empty()

    legend_list = []
    palette_list = []
    palette = px.colors.qualitative.Plotly
    palette = [palette[0], '#FF9900', '#66AA00', '#750D86', '#006400', '#6C4516']
    main_description_markdown = "<p>Основной сигнал: "
    main_colored_markdown = "<b style='text-align: left; color: "+palette[0]+";'>"+col_sensors_list[0] + \
                            " ("+dict_kks[col_sensors_list[0]]+")</b></p>"
    col_check, col_description, col_placeholder = st.columns([1, 38, 1])
    with col_check:
        main_signal_legend = st.checkbox(main_description_markdown+main_colored_markdown,
                                         value=True, key="legend_checkbox_main" + str(idx) + "_" + str(jdx),
                                         label_visibility="collapsed")
    with col_description:
        st.markdown(main_description_markdown+main_colored_markdown, unsafe_allow_html=True)

    if main_signal_legend:
        legend_list.append(col_sensors_list[0])
        palette_list.append(palette[0])

    color_index = 1
    for feature in col_sensors_list[1:]:
        other_description_markdown = "<p>Дополнительный сигнал: "
        other_colored_markdown = "<b style='text-align: left; color: "+palette[color_index]+";'>" +\
                                 feature + " (" + dict_kks[feature]+")</b></p>"
        col_check, col_description, col_placeholder = st.columns([1, 38, 1])
        with col_check:
            other_signal_legend = st.checkbox(other_description_markdown+other_colored_markdown,
                                              value=True,
                                              key="legend_checkbox_" + feature + str(idx) + "_" + str(jdx),
                                              label_visibility="collapsed")
        with col_description:
            st.markdown(other_description_markdown+other_colored_markdown, unsafe_allow_html=True)
        if other_signal_legend:
            legend_list.append(feature)
            palette_list.append(palette[color_index])
        color_index += 1
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(
        showlegend=False
    )
    if main_signal_legend:
        fig.add_trace(go.Scatter(
            x=df_sensors[legend_list[0]].iloc[
              anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
            y=df_sensors[legend_list[0]].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
            name="yaxis data", line={"color": palette_list[0], "width": 2}
        ))
        fig.update_layout(
            yaxis=dict(
                title=legend_list[0],
                titlefont=dict(
                    size=14,
                    color=palette_list[0]
                ),
                tickfont=dict(
                    size=14,
                    color=palette_list[0]
                )
            )
        )
        idx_feature = 2
        for feature in legend_list[1:]:
            fig.add_trace(go.Scatter(
                x=df_sensors[feature].iloc[
                  anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
                y=df_sensors[feature].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
                name=feature, yaxis="y"+str(idx_feature), line={"width": 1.5,
                                                                "color": palette_list[idx_feature-1]}
            ))
            if (feature == PLOT_FEATURES[0]) or (feature == PLOT_FEATURES[1]):
                fig.layout["yaxis" + str(idx_feature)] = dict(
                    title=feature,
                    titlefont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    ),
                    tickfont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    ),
                    overlaying="y",
                    side="right",
                    anchor="free",
                    autoshift=True,
                    showline=True,
                    showgrid=False,
                    zeroline=False,
                    ticks='outside',
                    tickwidth=0.5,
                    tickcolor='black',
                    title_standoff=5
                )
            else:
                fig.layout["yaxis" + str(idx_feature)] = dict(
                    title=feature,
                    titlefont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    ),
                    tickfont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    ),
                    overlaying="y",
                    side="left",
                    autoshift=True,
                    anchor="free",
                    showline=True,
                    showgrid=False,
                    zeroline=False,
                    ticks='outside',
                    tickwidth=0.5,
                    tickcolor=palette_list[idx_feature-1],
                    title_standoff=5,
                    layer="below traces"
                )
            idx_feature += 1
    else:
        if len(legend_list) == 0:
            st.error("Отметьте сигнал")
        else:
            fig.add_trace(go.Scatter(
                x=df_sensors[legend_list[0]].iloc[
                  anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
                y=df_sensors[legend_list[0]].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
                name="yaxis data", line={"color": palette_list[0], "width": 2}
            ))
            fig.update_layout(
                yaxis=dict(
                    title=legend_list[0],
                    titlefont=dict(
                        size=14,
                        color=palette_list[0]
                    ),
                    tickfont=dict(
                        size=14,
                        color=palette_list[0]
                    )
                )
            )
            idx_feature = 2
            for feature in legend_list[1:]:
                fig.add_trace(go.Scatter(
                    x=df_sensors[feature].iloc[
                      anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
                    y=df_sensors[feature].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
                    name=feature, yaxis="y" + str(idx_feature), line={"width": 1.5,
                                                                      "color": palette_list[idx_feature-1]}
                ))
                if (feature == PLOT_FEATURES[0]) or (feature == PLOT_FEATURES[1]):
                    fig.layout["yaxis" + str(idx_feature)] = dict(
                        title=legend_list[1],
                        titlefont=dict(
                            size=14,
                            color=palette_list[idx_feature - 1]
                        ),
                        tickfont=dict(
                            size=14,
                            color=palette_list[idx_feature - 1]
                        ),
                        overlaying="y",
                        side="right",
                        showline=True,
                        showgrid=False,
                        zeroline=False,
                        ticks='outside',
                        tickwidth=1,
                        tickcolor='black',
                        title_standoff=5
                    )
                else:
                    fig.layout["yaxis" + str(idx_feature)] = dict(
                        title=feature,
                        titlefont=dict(
                            size=14,
                            color=palette_list[idx_feature - 1]
                        ),
                        tickfont=dict(
                            size=14,
                            color=palette_list[idx_feature - 1]
                        ),
                        overlaying="y",
                        side="left",
                        autoshift=True,
                        anchor="free",
                        showline=True,
                        showgrid=False,
                        zeroline=False,
                        ticks='outside',
                        tickwidth=1,
                        tickcolor=palette_list[idx_feature-1],
                        title_standoff=5
                    )
                idx_feature += 1

    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    if merged_interval_list[idx] in interval_list:
        # Выделение красным прямоугольником
        if (merged_interval_list[idx][0] - config["model"]["delta_tau_P"]*config["number_of_samples"]) <= 0:
            fig.add_vrect(x0=df_sensors.index[merged_interval_list[idx][0]],
                          x1=df_sensors.index[merged_interval_list[idx][-1]],
                          line_width=2, line_color="red", layer="below")
        else:
            fig.add_vrect(x0=df_sensors.index[merged_interval_list[idx][0] -
                                             config["model"]["delta_tau_P"] * config["number_of_samples"]],
                          x1=df_sensors.index[merged_interval_list[idx][-1]],
                          line_width=2, line_color="red", layer="below")
    fig_container.plotly_chart(fig, config=dict(displayModeBar=False, scrollZoom=True), use_container_width=True)
    return fig, legend_list, palette_list


# отрисовка гистрограммы
@st.cache_data
def hist_plot(anomaly_time_df, config):
    data_train = anomaly_time_df.iloc[1:len(anomaly_time_df):100, :]
    hist = np.histogram(data_train['potential'].values, bins=100)
    dist = scipy.stats.rv_histogram(hist)
    d = np.arange(min(data_train['potential']), max(data_train['potential']), 0.001)
    potentials = 100 * dist.pdf(d)
    probabilities = 100 * (1 - dist.cdf(d))

    df = pd.DataFrame(data={'potential': d, 'probability': probabilities}, index=None)
    temp = df.index[(df['probability'] < config['model']['P_pr'] * 100 + 1)].tolist()
    ind = temp[0]

    fig = px.line(
        x=d,
        y=[probabilities, potentials],
        width=10
    )
    fig.update_layout(
        showlegend=False
    )
    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    fig.add_vline(d[ind], line_width=1, line_color="red")

    st.plotly_chart(fig, config=dict(displayModeBar=False, scrollZoom=True), use_container_width=True)
    return fig
