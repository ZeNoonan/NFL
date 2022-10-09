import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
# import os
import base64 
import altair as alt
# import datetime as dt
from datetime import date, timedelta
# from st_aggrid import AgGrid
from st_aggrid import AgGrid, GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode, JsCode

st.set_page_config(layout="wide")

@st.cache
def read_csv_data(file):
    return pd.read_csv(file)

@st.cache
def read_data(file):
    return pd.read_excel(file)

df = read_data('C:/Users/Darragh/Documents/Python/NFL/nfl_historical_odds_24_09_22.xlsx')
df=df.copy()
df['Home Line Close']=df['Home Line Close'].fillna(df['Home Line Open'])
df['year'] = pd.DatetimeIndex(df['Date']).year
df['month'] = pd.DatetimeIndex(df['Date']).month
df['season_month'] = df['month'].map({9:1,10:2,11:3,12:4,1:5,2:6})
# NL_Raw_Clean['calendar_month']=NL_Raw_Clean['Per.'].map({1:9,2:10,3:11,4:12,5:1,6:2,7:3,8:4,9:5,10:6,11:7,12:8,19:8})
df['season_year'] = np.where((df['season_month'] < 5), df['year'], df['year']-1)
df['Home Team']=df['Home Team'].replace({'Washington Football Team':'Washington Commanders','Washington Redskins':'Washington Commanders','St. Louis Rams':'Los Angeles Rams',
'Oakland Raiders':'Las Vegas Raiders','San Diego Chargers':'Los Angeles Chargers'})
df['Away Team']=df['Away Team'].replace({'Washington Football Team':'Washington Commanders','Washington Redskins':'Washington Commanders','St. Louis Rams':'Los Angeles Rams',
'Oakland Raiders':'Las Vegas Raiders','San Diego Chargers':'Los Angeles Chargers'})
df=df.sort_values(by=['Date','Home Team']).reset_index().drop('index',axis=1)
df=df.reset_index().rename(columns={'index':'unique_id'})

# df=df.sort_values(by=['unique_id'],ascending=False)



df['avg_home_score']=df['Home Score'].expanding().mean()
df['avg_away_score']=df['Away Score'].expanding().mean()
cols_to_move=['Date','Home Team','Away Team','unique_id','Home Score','Away Score','avg_home_score','avg_away_score']
cols = cols_to_move + [col for col in df if col not in cols_to_move]
df=df[cols]


st.write('df data', df)
# NL_Raw_Clean['calendar_year']=NL_Raw_Clean['calendar_year']+2000
# NL_Raw_Clean=NL_Raw_Clean.rename(columns={'calendar_year':'year', 'calendar_month':'month'})

# df['']
# st.write(df.sort_values(by='Date'))
# for _ in df.groupby('season_year'):
#     pass

df_offensive_home=df.loc[:,['Date','Home Team', 'Home Score', 'season_year','unique_id','avg_home_score','avg_away_score','Home Line Close']].rename(columns={'Home Team':'team','Home Score':'score'})
df_offensive_home['home_away']=1
df_offensive_away=df.loc[:,['Date','Away Team','Away Score', 'season_year','unique_id','avg_home_score','avg_away_score','Home Line Close']].rename(columns={'Away Team':'team','Away Score':'score'})
df_offensive_away['home_away']=-1
df_offensive=pd.concat([df_offensive_home,df_offensive_away],axis=0).sort_values(by=['team','Date'],ascending=True).reset_index().drop('index',axis=1)
# df_groupby_scores=df_offensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).sum().reset_index().drop('level_2',axis=1)
# df_offensive['sum_score']=df_offensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).sum()\
#     .reset_index().drop(['level_2','team','season_year'],axis=1)
# df_offensive['mean_score']=df_offensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).mean()\
#     .reset_index().drop(['level_2','team','season_year'],axis=1)
df_offensive['avg_pts_scored_team_season']=df_offensive.groupby(['team','season_year'])['score'].expanding(min_periods=4).mean()\
    .reset_index().drop(['level_2','team','season_year'],axis=1)
df_offensive=df_offensive.rename(columns={'score':'pts_scored','mean_score':'4_game_pts_scored'}).sort_values(by=['team','Date'])

df_defensive_home=df.loc[:,['Date','Home Team', 'Away Score', 'season_year','unique_id','avg_home_score','avg_away_score','Home Line Close']].rename(columns={'Home Team':'team','Away Score':'score'})
df_defensive_home['home_away']=1
df_defensive_away=df.loc[:,['Date','Away Team','Home Score', 'season_year','unique_id','avg_home_score','avg_away_score','Home Line Close']].rename(columns={'Away Team':'team','Home Score':'score'})
df_defensive_away['home_away']=-1
df_defensive=pd.concat([df_defensive_home,df_defensive_away],axis=0).sort_values(by=['team','Date'],ascending=True).reset_index().drop('index',axis=1)
# df_groupby_scores=df_defensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).sum().reset_index().drop('level_2',axis=1)
# df_defensive['sum_score']=df_defensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).sum()\
#     .reset_index().drop(['level_2','team','season_year'],axis=1)
# df_defensive['mean_score']=df_defensive.groupby(['team','season_year'])['score'].rolling(window=4,min_periods=4, center=False).mean()\
#     .reset_index().drop(['level_2','team','season_year'],axis=1)
df_defensive['avg_pts_conceded_team_season']=df_defensive.groupby(['team','season_year'])['score'].expanding(min_periods=4).mean()\
    .reset_index().drop(['level_2','team','season_year'],axis=1)
df_defensive=df_defensive.rename(columns={'score':'pts_conceded','mean_score':'4_game_pts_conceded'}).sort_values(by=['team','Date'])

# st.write('df offensive 1', df_offensive)
# st.write('df defence 1', df_defensive)
df_new=pd.merge(df_offensive,df_defensive,how='outer')
# st.write('after merge', df_new)
df_new['team_cum_sum_pts']=df_new.groupby(['team'])['pts_scored'].cumsum()
df_new['team_cum_sum_games']=df_new.groupby(['team'])['pts_scored'].cumcount()+1
df_new['rolling_avg_team_pts_scored']=df_new['team_cum_sum_pts'] / df_new['team_cum_sum_games']
df_new=df_new.sort_values(by=['Date','unique_id','team'])
df_new['date_avg_pts_rolling']=df_new['pts_scored'].expanding().mean()
# st.write('just checking the average pts scored in every match', df_new)
# st.write('sorted by date avg score by date',df_new)
df_new=df_new.sort_values(by=['team','Date'],ascending=True)

df_new=df_new.sort_values(by=['home_away','Date','unique_id','team'],ascending=True)
# st.write('after sorting CHECK THIS OUT',df_new)
df_home=df_new[df_new['home_away']==1].sort_values(by=['Date','unique_id'],ascending=True)
df_home['home_pts_avg']=df_home['pts_scored'].expanding().mean()
df_away=df_new[df_new['home_away']==-1].sort_values(by=['Date','unique_id'],ascending=True)
df_away['away_pts_avg']=df_away['pts_scored'].expanding().mean()
df_new=pd.concat([df_home,df_away],ignore_index=True)
# df_new['home_pts_avg_']=df_new['pts_scored'].expanding().mean()
# df_new['away_pts_avg_']=df_new['pts_scored'].expanding().mean()



df_new=df_new.sort_values(by=['unique_id','home_away'],ascending=[True,False])
# st.write('df before', df_new)
# df_new['away_pts_avg']=df_new['away_pts_avg'].shift(-1)
df_new['avg_away_score']=df_new['avg_away_score'].fillna(method='ffill')
df_new['avg_home_score']=df_new['avg_home_score'].fillna(method='ffill')
df_new['home_adv']=df_new['avg_home_score']-df_new['avg_away_score']
cols_to_move=['Date','team','season_year','Home Line Close','unique_id','pts_scored','pts_conceded','home_adv','date_avg_pts_rolling','avg_pts_scored_team_season',
'avg_pts_conceded_team_season','home_pts_avg','away_pts_avg','avg_home_score','avg_away_score','home_away']
cols = cols_to_move + [col for col in df_new if col not in cols_to_move]
df_new=df_new[cols]
df_new=df_new.loc[:,['Date','team','season_year','unique_id','Home Line Close','pts_scored','pts_conceded','home_adv','date_avg_pts_rolling','avg_pts_scored_team_season',
'avg_pts_conceded_team_season','home_away']]
# st.write('df update', df_new)

# st.write('df after concat', df_new.sort_values(by=['home_away','Date'],ascending=True))

# st.write('sort out team names', df_new['team'].unique())
st.write('checking rolling team scores', df_new.sort_values(by=['team','Date']))
st.write('just checking the home adv calc keep it there to sense check', df_new.sort_values(by=['Date','unique_id','team']))
df_home_1=df_new[df_new['home_away']==1].rename(columns={'pts_scored':'home_pts_scored','pts_conceded':'home_pts_conceded','team':'home_team',
'avg_pts_scored_team_season':'home_avg_pts_scored_team_season','avg_pts_conceded_team_season':'home_avg_pts_conceded_team_season','date_avg_pts_rolling':'home_date_avg_pts_rolling'})\
    .set_index(['unique_id']).drop('home_away',axis=1).copy()
df_away_1=df_new[df_new['home_away']==-1].rename(columns={'pts_scored':'away_pts_scored','pts_conceded':'away_pts_conceded','team':'away_team',
'avg_pts_scored_team_season':'away_avg_pts_scored_team_season','avg_pts_conceded_team_season':'away_avg_pts_conceded_team_season','date_avg_pts_rolling':'away_date_avg_pts_rolling'})\
    .set_index(['unique_id']).drop(['home_adv','home_away'],axis=1).copy()
# st.write('df home', df_home_1, 'away', df_away_1)
# df_combined=pd.concat([df_home_1,df_away_1],axis=0)
df_combined=pd.merge(df_home_1.reset_index(),df_away_1.reset_index(),on=['unique_id','Date','season_year'],how='outer')

df_combined['away_defensive_rating']=df_combined['away_avg_pts_conceded_team_season'] / df_combined['away_date_avg_pts_rolling']
df_combined['projected_team_a_pts']= df_combined['home_avg_pts_scored_team_season'] * df_combined['away_defensive_rating']
df_combined['home_defensive_rating']=df_combined['home_avg_pts_conceded_team_season'] / df_combined['away_date_avg_pts_rolling']
df_combined['projected_team_b_pts']= df_combined['away_avg_pts_scored_team_season'] * df_combined['home_defensive_rating']
df_combined['projected_team_a_pts']= df_combined['projected_team_a_pts'] + (df_combined['home_adv']/2)
df_combined['projected_team_b_pts']= df_combined['projected_team_b_pts'] - (df_combined['home_adv']/2)
df_combined['proj_spread'] = df_combined['projected_team_b_pts'] - df_combined['projected_team_a_pts']

st.write('df_comb', df_combined)
st.write('The home-away date avg pts rolling is the average points scored in every match so we can see what the avg pts scored and conceded is both will be same')
