import io
import arcpy
import pandas as pd
import requests
from arcgis.features import GeoAccessor, GeoSeriesAccessor, FeatureSet
from arcgis.widgets import MapView
from zipfile import ZipFile
import os
from osgeo import ogr
from arcgis.geometry import SpatialReference
import sys

from arcgis import GIS
gis = GIS()

#starting with ndawn 
ndawn_link = r'https://ndawn.ndsu.nodak.edu/table.csv?station=78&station=220&station=223&station=93&station=183&station=70&variable=ddbst&dfy=&year=2024&ttype=daily&quick_pick=30_d&begin_date=2024-09-23&end_date=2024-09-23'

#call to the api
ndawn_response = requests.get(ndawn_link, stream=True).content

#save as dataframe, and cleaning csv a bit to make more readable
df1 = pd.read_csv(io.StringIO(ndawn_response.decode('utf-8')), skiprows=[0, 1, 2, 4], index_col=False)
df1

#our data is ready, but it isn't spatial yet so converting it to a spatially enabled df now-->
sedf = pd.DataFrame.spatial.from_xy(df=df1, x_column="Longitude", y_column="Latitude", sr=4326)

sedf.head()

#make a basic map, just wanted to verify that my points were contained in MN
basic_map = gis.map()

sedf.spatial.plot(
    map_widget=basic_map,
    renderer_type="s",
    symbol_type="simple",
    symbol_style="d",
    marker_size=10,
)

# Here we are showing it below
basic_map

#go from sedf to feature class here with a given directory-- ndawnfc shapefile will be created and placed in directory
sedf.spatial.to_featureclass(r'C:\Users\bende287\Documents\GIS5571\ndawnfc')

#assigning variable to URL for arc online rest api
arc_api_link = "https://arcgis.metc.state.mn.us/server/rest/services/GISLibrary/RoadCenterlines/FeatureServer/0/query?where=1%3D1&f=json"

#call to the api
arc_response = requests.get(arc_api_link, stream=True).json()

type(arc_response)

#going from dictionary to feature set here
fs = FeatureSet.from_dict(arc_response)

arc_rest = fs.sdf
arc_rest

#making sure to maintain the same projection throughout-- transforming the Arc Online API to WGS 84 (ndawn is already in this projection)
arc_rest.spatial.project(SpatialReference(4326))
arc_rest

#first call to mn geo's api
mn_geo_response = requests.get("https://gisdata.mn.gov/api/3/action/package_show?id=d199886f-474f-4fe0-aba4-c7071ab92a35")

#reading as a json
counties_json = mn_geo_response.json()

#search within json and pull out a dataset we can use
find_counties = counties_json['result']['resources'][0]['url']
print(find_counties)

#second request to get zipped dataset
counties_zip = "https://resources.gisdata.mn.gov/pub/gdrs/data/pub/us_mn_state_dot/bdry_counties/shp_bdry_counties.zip"
counties = requests.get(counties_zip, allow_redirects=True)

#open a new file and use the dot interface. write to put data in the file
open("C:\\Users\\bende287\Downloads\\shp_bdry_counties.zip", 'wb').write(counties.content)

#unzip file
with ZipFile("C:\\Users\\bende287\Downloads\\shp_bdry_counties.zip", 'r') as zip:
    zip.printdir()
    
    print('Extracting all files now..')
    zip.extractall("C:\\Users\\bende287\Downloads\\shp_bdry_counties.zip.zip")
    print('Done!')

#finding the shapefile among other files and reading the projected and geographic coordinate systems
shapeDriver = ogr.GetDriverByName("ESRI Shapefile")

shapeDataset = shapeDriver.Open("C:\\Users\\bende287\Downloads\\shp_bdry_counties.zip.zip\\County_Boundaries_in_Minnesota.shp")
shapeLayer = shapeDataset.GetLayer()
shapeSptRef = shapeLayer.GetSpatialRef()
print(shapeSptRef)
#geographic coordinate system and projection coordinate system are both NAD 83 --> note: would need to convert to WGS 84 to match others

# make it a spatially enabled df
df_gecommons = pd.DataFrame.spatial.from_featureclass(r"C:\Users\bende287\Downloads\shp_bdry_counties.zip.zip\County_Boundaries_in_Minnesota.shp")
#transform the projection to match the others
df_gecommons.spatial.project(SpatialReference(4326))

df_gecommons


#this performs the join between the mn geocommons dataset and the ndawn dataset (only two required to perform spatial join for assignment)
target_features = "C:\\Users\\bende287\Downloads\\shp_bdry_counties.zip.zip\\County_Boundaries_in_Minnesota.shp"
join_features = "C:\\Users\\bende287\\Documents\\GIS5571\\ndawnfc.shp"
out_feature_class = "C:\\Users\\bende287\\Documents\\GIS5571\\test"

arcpy.SpatialJoin_analysis(target_features, join_features, out_feature_class)



#save as a dataframe and print out head of the table
df_joined = pd.DataFrame.spatial.from_featureclass(r"C:\\Users\\bende287\\Documents\\GIS5571\\test")
df_joined.head()

#execute CreateFileGDB and save to given directory
out_name = "myfgdb.gdb"
arcpy.CreateFileGDB_management(r"C:\\Users\\bende287\\Documents\\GIS5571", out_name)


