import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def get_home_fig_potentials(df_common, anomaly_interval, interval_list):
    col_list = ['target_value']
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
        if interval[0] <= 0:
            fig.add_vrect(
                x0=df_common.index[interval[0]],
                x1=df_common.index[interval[-1]],
                line_width=1, line_color="red", layer="below")
        else:
            fig.add_vrect(x0=df_common.index[interval[0]],
                          x1=df_common.index[interval[-1]],
                          line_width=1, line_color="red", layer="below")
    return fig


def get_tab_fig_potentials(df_common, merged_interval_list, interval_list, LEFT_SPACE, RIGHT_SPACE):
    col_list = ['target_value']

    interval_len = merged_interval_list[-1] - merged_interval_list[0] + 1
    if (interval_len > LEFT_SPACE) and (merged_interval_list[0] > LEFT_SPACE):
        left_space = interval_len
    else:
        if merged_interval_list[0] > LEFT_SPACE:
            left_space = LEFT_SPACE
        else:
            left_space = 0

    if (interval_len > RIGHT_SPACE) and (merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE)):
        right_space = interval_len
    else:
        if merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE):
            right_space = RIGHT_SPACE
        else:
            right_space = 0

    anomaly_tab_interval = [merged_interval_list[0] - left_space, merged_interval_list[-1] + right_space]

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
    if merged_interval_list in interval_list:
        if merged_interval_list[0] <= 0:
            fig.add_vrect(x0=df_common.index[merged_interval_list[0]],
                          x1=df_common.index[merged_interval_list[-1]], line_width=2, line_color="red", layer="below")
        else:
            fig.add_vrect(x0=df_common.index[merged_interval_list[0]],
                          x1=df_common.index[merged_interval_list[-1]], line_width=2, line_color="red", layer="below")
    return fig


def get_sensor_fig_potentials(df_common, df_sensors, top, merged_interval_list, interval_list, LEFT_SPACE, RIGHT_SPACE, PLOT_FEATURES):
    if top not in PLOT_FEATURES:
        col_sensors_list = [top] + PLOT_FEATURES
    else:
        col_sensors_list = [top]
        for plot_signal in PLOT_FEATURES:
            if plot_signal != top:
                col_sensors_list.append(plot_signal)

    interval_len = merged_interval_list[-1] - merged_interval_list[0] + 1
    if (interval_len > LEFT_SPACE) and (merged_interval_list[0] > LEFT_SPACE):
        left_space = interval_len
    else:
        if merged_interval_list[0] > LEFT_SPACE:
            left_space = LEFT_SPACE
        else:
            left_space = 0

    if (interval_len > RIGHT_SPACE) and (merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE)):
        right_space = interval_len
    else:
        if merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE):
            right_space = RIGHT_SPACE
        else:
            right_space = 0
    anomaly_sensors_interval = [merged_interval_list[0] - left_space, merged_interval_list[-1] + right_space]

    palette = px.colors.qualitative.Plotly

    legend_list = col_sensors_list
    #palette_list = palette[:6]
    palette_list = [palette[0], '#FF9900', '#66AA00', '#750D86', '#006400', '#6C4516']

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(
        showlegend=False
    )
    fig.add_trace(go.Scatter(
        x=df_sensors[legend_list[0]].iloc[
          anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
        y=df_sensors[legend_list[0]].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
        name="yaxis data", line={"color": palette_list[0], "width": 2}
    ))
    fig.update_layout(
        #xaxis=dict(domain=[0, 0.7]),
        #xaxis=dict(domain=[0, 0.9]),
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
        # fig.add_trace(go.Scatter(
        #     x=df_sensors[feature].iloc[
        #       anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
        #     y=df_sensors[feature].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
        #     name=feature, yaxis="y"+str(idx_feature), line={"dash": "dashdot", "width": 0.5,
        #                                                     "color": palette_list[idx_feature-1]}
        fig.add_trace(go.Scatter(
            x=df_sensors[feature].iloc[
              anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
            y=df_sensors[feature].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
            name=feature, yaxis="y" + str(idx_feature), line={"width": 1.5,
                                                              "color": palette_list[idx_feature - 1]}
        ))
        if idx_feature == 2 or idx_feature == 3:
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
            #fig.update_traces(selector=feature, line={"width": 0.1})
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
            #fig.update_traces(selector=feature, line={"width": 0.1})
        idx_feature += 1
    if merged_interval_list in interval_list:
        # Выделение красным прямоугольником
        if merged_interval_list[0] <= 0:
            fig.add_vrect(x0=df_sensors.index[merged_interval_list[0]],
                          x1=df_sensors.index[merged_interval_list[-1]],
                          line_width=2, line_color="red", layer="below")
        else:
            fig.add_vrect(x0=df_sensors.index[merged_interval_list[0]],
                          x1=df_sensors.index[merged_interval_list[-1]],
                          line_width=2, line_color="red", layer="below")
    fig.update_layout({"uirevision": "foo"}, overwrite=True)
    return fig, legend_list, palette_list


def get_another_sensor_fig_potentials(df_common, df_sensors, tops, merged_interval_list, interval_list, dict_kks, LEFT_SPACE, RIGHT_SPACE, PLOT_FEATURES, DROP_LIST):
    col_sensors_list = []
    for top in tops:
        if (top not in PLOT_FEATURES[:2]) and (top not in DROP_LIST):
            col_sensors_list.append(top)
    col_sensors_list.append(PLOT_FEATURES[0])
    col_sensors_list.append(PLOT_FEATURES[1])

    interval_len = merged_interval_list[-1] - merged_interval_list[0] + 1
    if (interval_len > LEFT_SPACE) and (merged_interval_list[0] > LEFT_SPACE):
        left_space = interval_len
    else:
        if merged_interval_list[0] > LEFT_SPACE:
            left_space = LEFT_SPACE
        else:
            left_space = 0

    if (interval_len > RIGHT_SPACE) and (merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE)):
        right_space = interval_len
    else:
        if merged_interval_list[-1] < (len(df_common) - RIGHT_SPACE):
            right_space = RIGHT_SPACE
        else:
            right_space = 0

    anomaly_sensors_interval = [merged_interval_list[0] - left_space, merged_interval_list[-1] + right_space]

    palette = px.colors.qualitative.Plotly

    legend_list = col_sensors_list
    #palette_list = palette[:6]
    palette_list = [palette[0], '#750D86', '#6C4516', '#FF9900', '#66AA00', '#006400']

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.update_layout(
        showlegend=False
    )
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
                                                              "color": palette_list[idx_feature - 1]}
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
    if merged_interval_list in interval_list:
        # Выделение красным прямоугольником

        fig.add_vrect(x0=df_common.index[merged_interval_list[0]],
                      x1=df_common.index[merged_interval_list[-1]],
                      line_width=2, line_color="red", layer="below")
    fig.update_layout({"uirevision": "foo"}, overwrite=True)

    col_others_list = []
    for key in dict_kks.keys():
        if (key not in col_sensors_list) and (key not in DROP_LIST):
            col_others_list.append(key)
    col_others_list.append(PLOT_FEATURES[0])
    col_others_list.append(PLOT_FEATURES[1])
    palette = px.colors.qualitative.Dark24

    legend_list = col_others_list
    # palette_list = palette[:6]
    palette_list = palette[:len(legend_list)]
    fig_others_list = []

    fig_others = make_subplots(specs=[[{"secondary_y": True}]])
    fig_others.update_layout(
        showlegend=False
    )
    fig_others.add_trace(go.Scatter(
        x=df_sensors[legend_list[0]].iloc[
          anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
        y=df_sensors[legend_list[0]].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
        name="yaxis data", yaxis="y", line={"color": palette_list[0], "width": 2}
    ))
    fig_others.update_layout(
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
        if idx_feature % 6 == 0:
            fig_others.update_layout({"uirevision": "foo"}, overwrite=True)
            if merged_interval_list in interval_list:
                # Выделение красным прямоугольником

                fig_others.add_vrect(x0=df_common.index[merged_interval_list[0]],
                                     x1=df_common.index[merged_interval_list[-1]],
                                     line_width=2, line_color="red", layer="below")
            fig_others_list.append(fig_others)
            fig_others = make_subplots(specs=[[{"secondary_y": True}]])
            fig_others.update_layout(
                showlegend=False
            )
            fig_others.add_trace(go.Scatter(
                x=df_sensors[legend_list[idx_feature-1]].iloc[
                  anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
                y=df_sensors[legend_list[idx_feature-1]].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
                name="yaxis data", yaxis="y", line={"color": palette_list[idx_feature-1], "width": 2}
            ))
            fig_others.update_layout(
                yaxis=dict(
                    title=feature,
                    titlefont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    ),
                    tickfont=dict(
                        size=14,
                        color=palette_list[idx_feature-1]
                    )
                )
            )
        else:
            fig_others.add_trace(go.Scatter(
                x=df_sensors[feature].iloc[
                  anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].index.to_list(),
                y=df_sensors[feature].iloc[anomaly_sensors_interval[0]:anomaly_sensors_interval[-1]].to_list(),
                name=feature, yaxis="y" + str(idx_feature), line={"width": 1.5,
                                                                      "color": palette_list[idx_feature-1]}
            ))
            if (feature == PLOT_FEATURES[0]) or (feature == PLOT_FEATURES[1]):
                fig_others.layout["yaxis" + str(idx_feature)] = dict(
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
                fig_others.layout["yaxis" + str(idx_feature)] = dict(
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
    fig_others.update_layout({"uirevision": "foo"}, overwrite=True)
    if merged_interval_list in interval_list:
        # Выделение красным прямоугольником

        fig_others.add_vrect(x0=df_common.index[merged_interval_list[0]],
                             x1=df_common.index[merged_interval_list[-1]],
                             line_width=2, line_color="red", layer="below")
    fig_others_list.append(fig_others)
    return fig, fig_others_list
