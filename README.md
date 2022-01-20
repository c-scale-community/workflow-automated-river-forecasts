# use-case-high-res-land-surface-drought-analysis
Porting and deploying the High Resolution Land Surface Drought Analysis use case to C-SCALE

## File explanation

* `download_data.py` functionality to download ERA5 and SEAS5 data using the CDS API ([note that a key-file is required](https://cds.climate.copernicus.eu/api-how-to))
* `convert_data.py` functionality to convert downloaded data into suitable forcing input for a `wflow_sbm` model

## Usage
1. Firstly, download the ERA5 and SEAS5 data from the Climate Data Store. The script automatically downloads SEAS5 
data of the current month, and ERA5 data of the previous month. '--output_dir' sets the directory where the downloaded 
files are stored.
```
python download_data.py --output_dir "workdir"
```
2. Resample the downloaded data to the model grid. 
`--dir_downloads` refers to the directory with the downloaded data ('--output_dir' from the previous script), 
and `--output_dir` to the directory where the forcing files are exported to (currently set to the `wflow` model directory). 
See the script for the optional settings (location of model maps, ERA5 and SEAS5 elevation maps, and lapse rate value).
```
python convert_data.py --dir_downloads "workdir" --output_dir "wflow_rhine"
```

## Upload files to spider
```
rsync -W -e "ssh -i <<your private key>>" hrlsa.sif <<your surf email>>@spider.surfsara.nl:/project/hrlsa/<<target>>
```
