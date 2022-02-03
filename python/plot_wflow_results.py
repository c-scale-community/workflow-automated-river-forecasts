# -*- coding: utf-8 -*-
"""
Created on Thu Jan 20 18:09:23 2022

@author: Buitink
"""

import click
from datetime import date
from dateutil.parser import parse
import pandas as pd
import matplotlib.pyplot as plt
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
              required=True, type=str, help='Start of forecasting period (in YYYY_MM format)',)

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
        current_month = current_date.month
        current_year = current_date.year
    
        # Set correct previous month and year values for ERA5 data download
        if current_month != 1:
            prev_month = current_month - 1
            prev_year = current_year
        else:
            prev_month = 12
            prev_year = current_year - 1
    else:
        previous_date = parse(re.sub(r"_", r"-", start_date))
        prev_month = previous_date.month
        prev_year = previous_date.year
    
    path_to_era_output = f"{output_dir}/run_ERA5_{prev_year}_{prev_month}/output.csv"
    era_result = pd.read_csv(path_to_era_output, index_col=0, parse_dates=True)[col_extract]

    # Loop through the different ensemles    
    for ens_idx in range(num_ensembles):
        path_to_seas_output = f"{output_dir}/run_SEAS5_ens{ens_idx}_{prev_year}_{prev_month}/output.csv"
              
        # Loop through SEAS ensembles, create new dataframe if it is the first ensemble
        if ens_idx == 0:
            seas_result = pd.read_csv(path_to_seas_output, index_col=0, parse_dates=True)[col_extract]
            seas_result = pd.DataFrame(seas_result)
            seas_result.columns = [ens_idx]
        # Append to existing dataframe    
        else:
            seas_result[ens_idx] = pd.read_csv(path_to_era_output, index_col=0, parse_dates=True)[col_extract]
    
    # Create figure
    fig = plt.figure("Plot_discharge", clear=True, tight_layout=True, figsize=(8,5))
    ax = fig.subplots(1)
    
    # Extract date information
    xdate_era = era_result.index.to_pydatetime()
    xdate_seas = seas_result.index.to_pydatetime()
    
    ax.plot(xdate_era, era_result, color="black")
    for ens_idx in range(num_ensembles):
        ax.plot(xdate_seas, seas_result[ens_idx], c="black", alpha=0.5)
    
    ax.set_ylabel("Discharge [m$^3$ s$^{-1}$]")
    
    fig.savefig(f"{figure_out_dir}/{filename_figure}", dpi=300)


if __name__ == "__main__":    
    plot_discharge_ts()