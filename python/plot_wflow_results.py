# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 18:09:23 2022

@author: Buitink
"""

import click
from datetime import date
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.legend_handler import HandlerTuple
import re


@click.command()
@click.option('--output_dir', required=True, type=str,
              default = "../../Data/model_output",
              help='Directory path where the model output resides, expects naming convention in' +
              'directory names within.',)
@click.option('--figure_out_dir', required=True, type=str,
              default = "../../Public",
              help='Directory path where the resulting figure will be saved.',)
@click.option('--filename_figure', required=True, type=str,
              default = "discharge_ts.png",
              help='Filename of the resulting figure.',)

# Optional settings
@click.option('--num_ensembles', default=51,
              type=int, help='Number of SEAS5 ensembles')
@click.option('--col_extract', default="Q_1",
              type=str, help='Name of the column to extract from the .csv file.')
@click.option('--start_date', default=None,
              required=False, type=str, help='Start of forecasting period (in YYYY_MM format)',)

def plot_discharge_ts(output_dir, figure_out_dir, filename_figure, num_ensembles, col_extract, start_date):
    """
    Plots discharge of all SEAS5 predictions in one large plot.

    args:
        output_dir (str): directory path where the model output resides, expects naming convention
            in directory names within.
        figure_out_dir (str): directory path where the resulting figure will be saved.
        filename_figure (str): filename of the resulting figure.
        num_ensembles (str): Number of SEAS5 ensembles.
        col_extract (str): Name of the column to extract from the .csv file.
        start_date (str): Start of forecasting period (in YYYY_MM format)
    """

    if not start_date:
        # Get current date, for month and year information
        current_date = date.today()
    else:
        current_date = parse(re.sub(r"_", r"-", start_date))

    previous_date = current_date - relativedelta(months=1)

    current_month = current_date.month
    current_year = current_date.year
    prev_month = previous_date.month
    prev_year = previous_date.year

    def month_to_str(month):
        strmonth = str(month)
        if len(strmonth) < 2:
            return "0" + strmonth
        else:
            return strmonth

    path_to_era_output = f"{output_dir}/run_ERA5_{prev_year}_{prev_month:02d}/output.csv"
    era_result = pd.read_csv(path_to_era_output, index_col=0, parse_dates=True)[col_extract]

    # Loop through the different ensemles
    for ens_idx in range(num_ensembles):
        path_to_seas_output = f"{output_dir}/run_SEAS5_ens{ens_idx}_{current_year}_{current_month:02d}/output.csv"

        # Loop through SEAS ensembles, create new dataframe if it is the first ensemble
        if ens_idx == 0:
            seas_result = pd.read_csv(path_to_seas_output, index_col=0, parse_dates=True)[col_extract]
            seas_result = pd.DataFrame(seas_result)
            seas_result.columns = [ens_idx]
        # Append to existing dataframe
        else:
            seas_result[ens_idx] = pd.read_csv(path_to_seas_output, index_col=0, parse_dates=True)[col_extract]

    # Create figure
    fig = plt.figure("Plot_discharge", clear=True, tight_layout=True, figsize=(8,5))
    ax = fig.subplots(1)

    # Extract date information
    xdate_era = era_result.index.to_pydatetime()
    xdate_seas = seas_result.index.to_pydatetime()

    ax.plot(xdate_era, era_result, color="black")
    for ens_idx in range(num_ensembles):
        ax.plot(xdate_seas, seas_result[ens_idx], c="black", alpha=0.5)

    ax.set_xlim(xdate_era[0], xdate_seas[-1])
    ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")

    # Format xdate
    months = mdates.MonthLocator(bymonthday=2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))

    fig.savefig(f"{figure_out_dir}/orig_{filename_figure}", dpi=300)


    # Calculate quantiles for SEAS5 results
    quantiles = np.arange(0.1, 1.0, 0.1)
    seas_quan = seas_result.quantile(quantiles, axis=1).T
    seas_mean = seas_result.mean(axis=1)
    # import pdb; pdb.set_trace()
    colors = ['#8c510a','#bf812d','#dfc27d','#f6e8c3','#c7eae5','#80cdc1','#35978f','#01665e']

    # Create figure
    fig = plt.figure("Plot_discharge_quantile", clear=True, tight_layout=True, figsize=(8,5))
    ax = fig.subplots(1)

    # Extract date information
    xdate_era = era_result.index.to_pydatetime()
    xdate_seas = seas_result.index.to_pydatetime()

    ax.plot(xdate_era, era_result, color="black", label="ERA5 hindcast")
    # Plot quantiles
    for idx, q in enumerate(quantiles[:-1]):
        ax.fill_between(
            x=xdate_seas,
            y1=seas_quan.iloc[:,idx],
            y2=seas_quan.iloc[:,idx+1],
            color=colors[idx])
    # Plot mean
    ax.plot(xdate_seas, seas_mean, ls="--", c="black", label="Mean SEAS5 ensemble")

    ax.set_xlim(xdate_era[0], xdate_seas[-1])
    ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")

    # Format xdate
    months = mdates.MonthLocator(bymonthday=2)
    ax.xaxis.set_major_locator(months)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))


    ## Add legend with custom colormap
    cmap_name = f"Quantile range ({quantiles[0]}$-${quantiles[-1]})"
    cmap = LinearSegmentedColormap.from_list("custom", colors, N=len(colors))
    cmaps_dict = {cmap.name: cmap(np.linspace(0, 1, len(colors)))}

    cmap_colors = cmap(np.linspace(0, 1, len(colors)))
    cmap_gradient = [patches.Patch(facecolor=c, edgecolor=c, label=cmap_name)
                        for c in cmap_colors]

    # Get current handles and labels
    handles, labels = ax.get_legend_handles_labels()
    # Append new info
    handles.append([cmap_gradient])
    labels.append(cmap_name)
    # Add legend to plot
    ax.legend(
        # handles=handles,
        # labels=labels,
        # fontsize=12,
        # loc=1,
        # handler_map={list: HandlerTuple(ndivide=None, pad=0)}
        )

    # save figure
    fig.savefig(f"{figure_out_dir}/{filename_figure}", dpi=300)


if __name__ == "__main__":
    plot_discharge_ts()
