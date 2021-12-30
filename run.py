import pandas as pd
import numpy as np
import sklearn
import sklearn.neighbors
import configparser
config = configparser.ConfigParser()
file = config.read_file(open(r"links.cfg"))
sheet_ = config['SHEET']['id']

def get_dist():
    city_id = input("Enter city id: ") 
    sheet_id = input("Enter google sheet id: ") or sheet_
    sn ='stops'
    sn_2 = 'routes'
    stop_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sn}"
    route_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sn_2}"
    stops = pd.read_csv(stop_url)
    route = pd.read_csv(route_url)
    
    dtf = stops.loc[:,('stop_id', 'stop_name','zone_area_lga')]
    dtf['lat_rads']= stops['Lat-rads']
    dtf['lng_rads']= stops['Long-rads']
    dtf = dtf.dropna()
    
    places_X=dtf[['stop_name','stop_id','lat_rads','lng_rads']].copy()
    places_X=places_X.rename(columns={'stop_name':'origin_name','stop_id':'origin_id'})
    places_Y=dtf[['stop_name','stop_id','lat_rads','lng_rads']].copy()
    places_Y=places_Y.rename(columns={'stop_name':'dest_name','stop_id':'dest_id'})
    dist = sklearn.neighbors.DistanceMetric.get_metric('haversine')
    dist_matrix = (dist.pairwise
        (places_X[['lat_rads','lng_rads']],
         places_Y[['lat_rads','lng_rads']])*6371000
                  )
    df_dist_matrix = (
        pd.DataFrame(dist_matrix,index=places_X['origin_id'], 
                     columns=places_Y['dest_id'])
    )
    df_dist_incols = (
        pd.melt(df_dist_matrix.reset_index(),id_vars='origin_id')
    )
    #Rename this column to 'distance' for relevance.
    df_dist_incols= df_dist_incols.rename(columns={'value':'distance'})
    indexNames = df_dist_incols[df_dist_incols['distance']<0].index
    df_dist_incols.drop(indexNames, inplace=True)
    indexNames = df_dist_incols[df_dist_incols['distance']>=500].index
    df_dist_incols.drop(indexNames, inplace=True)
    df_dist_incols=df_dist_incols.sort_values(by=['distance'])
    drop_dup = df_dist_incols.drop_duplicates(subset= 'distance',keep="first")
    final_data = drop_dup.loc[:,('origin_id', 'dest_id','distance')]
    final_data["trip_key"] = drop_dup['origin_id']+'_'+drop_dup['dest_id']
    final_data = final_data.loc[:,('origin_id','dest_id','trip_key','distance')]
    routes = route.loc[:,('origin_id','dest_id','trip_key','t_dist')]
    routes = routes.rename(columns={'t_dist':'distance'})
    routes = routes.drop_duplicates(subset= 'trip_key',keep="first")
    routes = routes[routes.distance<=500]
    routes = routes.dropna()
    difference = pd.concat([final_data,routes]).drop_duplicates(keep=False)
    difference = difference[difference.distance>0]
    difference['checker'] = difference['trip_key'].isin(routes['trip_key'])
    difference = difference[difference.checker == False]
    difference = difference.loc[:,('origin_id','dest_id','trip_key','distance')]
    difference.to_csv(f"exports/{city_id}.csv",index=False)
    
    return "A peek of what your data looks\n",difference.head()

get_dist()