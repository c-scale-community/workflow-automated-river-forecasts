import cdsapi
import click
import os

@click.command()
@click.option('--year', required=True, type=str, help='Year of Era5 data')
@click.option('--month', required=True, type=str, help='Month of Era5 data')
@click.option('--output', required=True, type=str, help='Output path for nc file',)

def download_era5(month, year, output):
    """Download Era5 data."""
    c = cdsapi.Client()

    filename = f'ERA5_{year}_{month}.nc'
    output_path = os.path.join(output, filename)

    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type':'reanalysis',

            'variable': [
                'mean_sea_level_pressure',
                'surface_solar_radiation_downwards',
                '2m_temperature',
                'total_precipitation'
            ],
            'year':[
                year
            ],
            'area': '46.00/5.00/52.50/12.50',
            'month':[month],
            'day':[
                '01','02','03',
                '04','05','06',
                '07','08','09',
                '10','11','12',
                '13','14','15',
                '16','17','18',
                '19','20','21',
                '22','23','24',
                '25','26','27',
                '28','29','30',
                '31'
            ],
            'time':[
                '00:00','01:00','02:00',
                '03:00','04:00','05:00',
                '06:00','07:00','08:00',
                '09:00','10:00','11:00',
                '12:00','13:00','14:00',
                '15:00','16:00','17:00',
                '18:00','19:00','20:00',
                '21:00','22:00','23:00'
            ],
            'format':'netcdf'
        },

        output_path)

if __name__ == '__main__':
    download_era5()
    
