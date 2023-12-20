import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt

def parse_station_line(line):
    parts = line.split()
    
    # try to find the index, and otherwise try to find another index, and else raise error
    try:
        idx = parts.index('rka150d0')
    except ValueError:
        try:
            idx = parts.index('rre150d0')
        except ValueError:
            raise ValueError(f"Could not find 'rka150d0' in line: {line}")
        
    return {
        "stn": parts[0],
        "Name": " ".join(parts[1:idx]),
        "Parameter": parts[idx],
        "Data source": " ".join(parts[idx+1:-3]),
        "Longitude/Latitude": parts[-3],
        "Coordinates [km]": parts[-2],
        "Elevation [m]": parts[-1]
    }

def read_station_data_from_file(file_path):
    # Attempting to read the metadata file using 'ISO-8859-1' encoding
    try:
        with open(file_path, 'r', encoding='ISO-8859-1') as file:
            # read all lines from the file 
            lines = [next(file) for _ in range(100)]
        
    except Exception as e:
            lines = str(e)

    # Find the header line and skip all lines before it
    header_line_index = next(i for i, line in enumerate(lines) if line.startswith("stn       Name"))
    station_lines = lines[header_line_index + 1:]

    stations = [parse_station_line(line) for line in station_lines if line.strip()]
    return stations

def convert_to_dataframe(stations):
    
    # convert to pandas dataframe
    df = pd.DataFrame(stations)

    df['Longitude'] = df['Longitude/Latitude'].str.split('/').str[0]
    df['Latitude'] = df['Longitude/Latitude'].str.split('/').str[1]
    df['X'] = df['Coordinates [km]'].str.split('/').str[0]
    df['Y'] = df['Coordinates [km]'].str.split('/').str[1]
    
    # turn from e.g. 8°54' into decimal degrees
    df['Longitude'] = df['Longitude'].str.split('°').str[0].astype(float) + df['Longitude'].str.split('°').str[1].str.split("'").str[0].astype(float)/60
    df['Latitude'] = df['Latitude'].str.split('°').str[0].astype(float) + df['Latitude'].str.split('°').str[1].str.split("'").str[0].astype(float)/60

    return df

def read_precipitation_data(file_path):
    
    # Skipping initial blank lines and setting the delimiter to semicolon
    df = pd.read_csv(file_path, delimiter=';', skiprows=2)
    
    # time has 8 digits
    df = df[df['time'].astype(str).str.len() == 8]

    df[df.columns[2]] = pd.to_numeric(df[df.columns[2]], errors='coerce')
    df[df.columns[3]] = pd.to_numeric(df[df.columns[3]], errors='coerce')
    df[df.columns[4]] = pd.to_numeric(df[df.columns[4]], errors='coerce')

    df['time'] = df.time.astype(str)
    df['date'] = pd.to_datetime(df['time'], format='%Y%m%d')
    
    return df

def plot_stations(df):

        # create geodataframe
        geometry = [Point(xy) for xy in zip(df.Longitude, df.Latitude)]
        gdf = gpd.GeoDataFrame(df, geometry=geometry)

        # plot and zoom into Switzerland
        world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))
        ax = world.plot(color='white', edgecolor='black')
        gdf.plot(ax=ax, color='red', markersize=5, marker='x', label='stations')
        plt.xlim(5, 11)
        plt.ylim(45.5, 48)
        plt.show()

if __name__ == '__main__':

    metadata_files = ['/Users/marron31/Downloads/order117265/order_117265_legend.txt',
                      '/Users/marron31/Downloads/order117266/order_117266_legend.txt',
                      '/Users/marron31/Downloads/order117268/order_117268_legend.txt',]

    data_files = ['/Users/marron31/Downloads/order117265/order_117265_data.txt',
                  '/Users/marron31/Downloads/order117266/order_117266_data.txt',
                  '/Users/marron31/Downloads/order117268/order_117268_data.txt',]
         
    
    # read and append all metadata files using the function defined above
    stations = []
    for file_path in metadata_files:
        stations.extend(read_station_data_from_file(file_path))
    
    # convert to pandas dataframe
    df = convert_to_dataframe(stations)

    # read and append all data files using the function defined above
    data = []
    for file_path in data_files:
        data.append(read_precipitation_data(file_path))

    # concatenate all dataframes
    df_data = pd.concat(data)

    plot_stations(df)

    