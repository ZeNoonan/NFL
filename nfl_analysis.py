import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
import os
import base64

st.set_page_config(layout="wide")


@st.cache
def read_data(file):
    return pd.read_excel(file) 
data_2019 = read_data('C:/Users/Darragh/Documents/Python/NFL/NFL_2019_Data.xlsx').copy()
# data_2020=read_data('C:/Users/Darragh/Documents/Python/NFL/NFL_2020_Data_Adj_week_zero.xlsx').copy()
data_2020=read_data('C:/Users/Darragh/Documents/Python/NFL/NFL_2020_Data.xlsx').copy()
test_data_2020=read_data('C:/Users/Darragh/Documents/Python/NFL/NFL_2020_Data_Test.xlsx').copy()
odds_data = read_data('C:/Users/Darragh/Documents/Python/NFL/nfl_betting_odds.xlsx').copy()
team_names_id = read_data('C:/Users/Darragh/Documents/Python/NFL/nfl_teams.xlsx').copy()

# st.table(data.head())
def spread_workings(data):
    data['home_win']=data['Home Points'] - data['Away Points']
    data['home_win'] = np.where((data['Home Points'] > data['Away Points']), 1, np.where((data['Home Points'] < data['Away Points']),-1,0))
    data['home_cover']=(np.where(((data['Home Points'] + data['Spread']) > data['Away Points']), 1,
    np.where(((data['Home Points']+ data['Spread']) < data['Away Points']),-1,0)))
    data['home_cover']=data['home_cover'].astype(int)
    data['away_cover'] = -data['home_cover']
    data=data.rename(columns={'Net Turnover':'home_turnover'})
    data['away_turnover'] = -data['home_turnover']
    return data

def season_cover_workings(data,home,away,name,week_start):
    season_cover_df=(data.set_index('Week').loc[week_start:,:]).reset_index()
    home_cover_df = (season_cover_df.loc[:,['Week','Date','Home ID',home]]).rename(columns={'Home ID':'ID',home:name})
    away_cover_df = (season_cover_df.loc[:,['Week','Date','Away ID',away]]).rename(columns={'Away ID':'ID',away:name})
    season_cover=pd.concat([home_cover_df,away_cover_df],ignore_index=True)
    # season_cover_df = pd.melt(season_cover_df,id_vars=['Week', 'home_cover'],value_vars=['Home ID', 'Away ID']).set_index('Week').rename(columns={'value':'ID'}).\
    # drop('variable',axis=1).reset_index().sort_values(by=['Week','ID'],ascending=True)
    return season_cover.sort_values(by=['Week','Date','ID'],ascending=['True','True','True'])

def season_cover_2(season_cover_df,column_name):    
    # https://stackoverflow.com/questions/54993050/pandas-groupby-shift-and-cumulative-sum
    season_cover_df[column_name] = season_cover_df.groupby (['ID'])[column_name].transform(lambda x: x.cumsum().shift())
    season_cover_df=season_cover_df.reset_index().sort_values(by=['Week','Date','ID'],ascending=True).drop('index',axis=1)
    # Be careful with this if you want full season, season to date cover, for week 17, it is season to date up to week 16
    # if you want full season, you have to go up to week 18 to get the full 17 weeks, just if you want to do analysis on season covers
    return season_cover_df

def season_cover_3(data,column_sign,name):
    data[column_sign] = np.where((data[name] > 0), 1, np.where((data[name] < 0),-1,0))
    return data

def turnover_2(season_cover_df):    
    # https://stackoverflow.com/questions/53335567/use-pandas-shift-within-a-group
    season_cover_df['prev_turnover']=season_cover_df.groupby('ID')['turnover'].shift()
    return season_cover_df.sort_values(by=['ID','Week'],ascending=True)
    # return season_cover_df


spread=spread_workings(data_2020)
st.write('spread',spread)

with st.beta_expander('Season to date Cover'):
    spread_1 = season_cover_workings(spread,'home_cover','away_cover','cover',1)
    spread_2=season_cover_2(spread_1,'cover')
    spread_3=season_cover_3(spread_2,'cover_sign','cover')
    st.write('this is season to date cover')
    st.write(spread_3.sort_values(by=['ID','Week'],ascending=['True','True']))
    # st.write('Test workings')
    # st.write(test_data_2020)


with st.beta_expander('Last Game Turnover'):
    turnover=spread_workings(data_2020)
    turnover_1 = season_cover_workings(turnover,'home_turnover','away_turnover','turnover',-1)
    turnover_2=turnover_2(turnover_1)
    turnover_3=season_cover_3(turnover_2,'turnover_sign','prev_turnover')
    st.write('this is last game turnover')
    st.write(turnover_3.sort_values(by=['ID','Week'],ascending=['True','True']))

matrix_df=spread_workings(data_2020)
test_df = matrix_df.copy()
matrix_df['at_home'] = 1
matrix_df['at_away'] = -1
matrix_df['home_pts_adv'] = -3
matrix_df['away_pts_adv'] = 3
matrix_df['away_spread']=-matrix_df['Spread']
matrix_df=matrix_df.rename(columns={'Spread':'home_spread'})
matrix_df_1=matrix_df.loc[:,['Week','Home ID','Away ID','at_home','at_away','home_spread','away_spread','home_pts_adv','away_pts_adv']].copy()

with st.beta_expander('Games Played to be used in Matrix Multiplication'):
    first_qtr=matrix_df_1.copy()
    start=-3
    finish=0
    first_4=first_qtr[first_qtr['Week'].between(start,finish)].copy()
    def games_matrix_workings(first_4):
        group_week = first_4.groupby('Week')
        raw_data_2=[]
        game_weights = iter([-0.125, -0.25,-0.5,-1])
        for name, group in group_week:
            group['game_adj']=next(game_weights)
            raw_data_2.append(group)

        df3 = pd.concat(raw_data_2, ignore_index=True)
        adj_df3=df3.loc[:,['Home ID', 'Away ID', 'game_adj']].copy()
        test_adj_df3 = adj_df3.rename(columns={'Home ID':'Away ID', 'Away ID':'Home ID'})
        concat_df_test=pd.concat([adj_df3,test_adj_df3]).sort_values(by=['Home ID', 'game_adj'],ascending=[True,False])
        test_concat_df_test=concat_df_test.groupby('Home ID')['game_adj'].sum().abs().reset_index()
        test_concat_df_test['Away ID']=test_concat_df_test['Home ID']
        full=pd.concat([concat_df_test,test_concat_df_test]).sort_values(by=['Home ID', 'game_adj'],ascending=[True,False])
        full_stack=pd.pivot_table(full,index='Away ID', columns='Home ID',aggfunc='sum')
        # st.write('Check sum looks good all zero', full_stack.sum())
        full_stack=full_stack.fillna(0)
        full_stack.columns = full_stack.columns.droplevel(0)
        return full_stack

    full_stack=games_matrix_workings(first_4)
    st.write('Check sum if True all good', full_stack.sum().sum()==0)
    st.write('this is 1st part games played, need to automate this for every week')
    st.write(full_stack)


with st.beta_expander('CORRECT Testing reworking the DataFrame'):
    test_df['at_home'] = 1
    test_df['at_away'] = -1
    test_df['home_pts_adv'] = 3
    test_df['away_pts_adv'] = -3
    test_df['away_spread']=-test_df['Spread']
    test_df=test_df.rename(columns={'Spread':'home_spread'})
    test_df_1=test_df.loc[:,['Week','Home ID','Away ID','at_home','at_away','home_spread','away_spread','home_pts_adv','away_pts_adv']].copy()
    
    # st.write(test_df_1.sort_values(by=['ID','Week'],ascending=True))
    test_df_home=test_df_1.loc[:,['Week','Home ID','at_home','home_spread','home_pts_adv']].rename(columns={'Home ID':'ID','at_home':'home','home_spread':'spread','home_pts_adv':'home_pts_adv'}).copy()
    test_df_away=test_df_1.loc[:,['Week','Away ID','at_away','away_spread','away_pts_adv']].rename(columns={'Away ID':'ID','at_away':'home','away_spread':'spread','away_pts_adv':'home_pts_adv'}).copy()
    test_df_2=pd.concat([test_df_home,test_df_away],ignore_index=True)
    test_df_2=test_df_2.sort_values(by=['ID','Week'],ascending=True)
    test_df_2['spread_with_home_adv']=test_df_2['spread']+test_df_2['home_pts_adv']
    st.write(test_df_2)

def test_4(matrix_df_1):
    weights = np.array([0.125, 0.25,0.5,1])
    sum_weights = np.sum(weights)
    matrix_df_1['adj_spread']=matrix_df_1['spread_with_home_adv'].rolling(window=4, center=False).apply(lambda x: np.sum(weights*x), raw=False)
    return matrix_df_1


with st.beta_expander('CORRECT Power Ranking to be used in Matrix Multiplication'):
    # # https://stackoverflow.com/questions/9621362/how-do-i-compute-a-weighted-moving-average-using-pandas
    grouped = test_df_2.groupby('ID')
    # https://stackoverflow.com/questions/16974047/efficient-way-to-find-missing-elements-in-an-integer-sequence
    # https://stackoverflow.com/questions/62471485/is-it-possible-to-insert-missing-sequence-numbers-in-python
    ranking_power=[]
    for name, group in grouped:
        dfseq = pd.DataFrame.from_dict({'Week': range( -3,21 )}).merge(group, on='Week', how='outer').fillna(np.NaN)
        dfseq['ID']=dfseq['ID'].fillna(method='ffill')
        dfseq['home_pts_adv']=dfseq['home_pts_adv'].fillna(0)
        dfseq['spread']=dfseq['spread'].fillna(0)
        dfseq['spread_with_home_adv']=dfseq['spread_with_home_adv'].fillna(0)
        dfseq['home']=dfseq['home'].fillna(0)
        df_seq_1 = dfseq.groupby(['Week','ID'])['spread_with_home_adv'].sum().reset_index()
        update=test_4(df_seq_1)
        ranking_power.append(update)
    df_power = pd.concat(ranking_power, ignore_index=True)
    st.write('power ranking',df_power)

with st.beta_expander('CORRECT Power Ranking Matrix Multiplication'):
    # https://stackoverflow.com/questions/62775018/matrix-array-multiplication-whats-excel-doing-mmult-and-how-to-mimic-it-in#62775508
    inverse_matrix=[]
    power_ranking=[]
    list_inverse_matrix=[]
    list_power_ranking=[]
    power_df=df_power.loc[:,['Week','ID','adj_spread']].copy()
    games_df=matrix_df_1.copy()
    first=list(range(-3,18))
    last=list(range(0,21))
    for first,last in zip(first,last):
        # st.write('this is first',first)
        # st.write('this is last',last)
        first_section=games_df[games_df['Week'].between(first,last)]
        # st.write(first_section)
        full_game_matrix=games_matrix_workings(first_section)
        # st.write(full_game_matrix)
        adjusted_matrix=full_game_matrix.loc[0:30,0:30]
        # st.write('this is the last number',last)
        # st.write(adjusted_matrix)
        df_inv = pd.DataFrame(np.linalg.pinv(adjusted_matrix.values), adjusted_matrix.columns, adjusted_matrix.index)
        # st.write('this is the inverse matrix',df_inv, 'number', last)
        power_df_week=power_df[power_df['Week']==last].drop_duplicates(subset=['ID'],keep='last').set_index('ID').drop('Week',axis=1).rename(columns={'adj_spread':0}).loc[:30,:]
        result = df_inv.dot(pd.DataFrame(power_df_week))
        result.columns=['power']
        avg=(result['power'].sum())/32
        result['avg_pwr_rank']=(result['power'].sum())/32
        result['final_power']=result['avg_pwr_rank']-result['power']
        df_pwr=pd.DataFrame(columns=['final_power'],data=[avg])
        result=pd.concat([result,df_pwr],ignore_index=True)
        result['week']=last+1
        power_ranking.append(result)
    power_ranking_combined = pd.concat(power_ranking).reset_index().rename(columns={'index':'ID'})
    st.write('power ranking combined', power_ranking_combined)
    
with st.beta_expander('Adding Power Ranking to Matches'):
    matches_df = spread.copy()
    home_power_rank_merge=power_ranking_combined.loc[:,['ID','week','final_power']].copy().rename(columns={'week':'Week','ID':'Home ID'})
    away_power_rank_merge=power_ranking_combined.loc[:,['ID','week','final_power']].copy().rename(columns={'week':'Week','ID':'Away ID'})
    updated_df=pd.merge(matches_df,home_power_rank_merge,on=['Home ID','Week']).rename(columns={'final_power':'home_power'})
    updated_df=pd.merge(updated_df,away_power_rank_merge,on=['Away ID','Week']).rename(columns={'final_power':'away_power'})
    updated_df['calculated_spread']=updated_df['away_power']-updated_df['home_power']
    updated_df['spread_working']=updated_df['home_power']-updated_df['away_power']+updated_df['Spread']
    updated_df['power_pick'] = np.where(updated_df['spread_working'] > 0, 1,
    np.where(updated_df['spread_working'] < 0,-1,0))
    st.write(updated_df)

with st.beta_expander('Adding Season to Date Cover to Matches'):
    st.write('this is season to date cover', spread_3)
    stdc_home=spread_3.rename(columns={'ID':'Home ID'})
    stdc_home['cover_sign']=-stdc_home['cover_sign']
    stdc_away=spread_3.rename(columns={'ID':'Away ID'})
    updated_df=updated_df.drop(['away_cover'],axis=1)
    updated_df=updated_df.rename(columns={'home_cover':'home_cover_result'})
    updated_df=pd.merge(updated_df,stdc_home,on=['Week','Home ID'],how='left').rename(columns={'cover':'home_cover','cover_sign':'home_cover_sign'})
    updated_df=pd.merge(updated_df,stdc_away,on=['Week','Away ID'],how='left').rename(columns={'cover':'away_cover','cover_sign':'away_cover_sign'})
    st.write('check that STDC coming in correctly', updated_df)
    st.write('Check Total')
    st.write('home',updated_df['home_cover_sign'].sum())
    st.write('away',updated_df['away_cover_sign'].sum())   
    
with st.beta_expander('Adding Turnover to Matches'):
    st.write('this is turnovers', turnover_3)
    turnover_matches = turnover_3.loc[:,['Week','ID','prev_turnover', 'turnover_sign']].copy()
    turnover_home=turnover_matches.rename(columns={'ID':'Home ID'})
    
    turnover_away=turnover_matches.rename(columns={'ID':'Away ID'})
    turnover_away['turnover_sign']=-turnover_away['turnover_sign']
    updated_df=pd.merge(updated_df,turnover_home,on=['Week','Home ID'],how='left').rename(columns={'prev_turnover':'home_prev_turnover','turnover_sign':'home_turnover_sign'})
    updated_df=pd.merge(updated_df,turnover_away,on=['Week','Away ID'],how='left').rename(columns={'prev_turnover':'away_prev_turnover','turnover_sign':'away_turnover_sign'})
    # TEST Workings
    # st.write('check that Turnover coming in correctly', updated_df[updated_df['Week']==18])
    # st.write('Check Total')
    # st.write('home',updated_df['home_turnover_sign'].sum())
    # st.write('away',updated_df['away_turnover_sign'].sum())
    # turnover_excel=test_data_2020.loc[:,['Week','Home ID','Home Team', 'Away ID', 'Away Team','excel_home_prev_turnover','excel_away_prev_turnover','excel_home_turnover_sign','excel_away_turnover_sign']].copy()
    # test_turnover=pd.merge(updated_df,turnover_excel)
    # test_turnover['test_1']=test_turnover['home_prev_turnover']-test_turnover['excel_home_prev_turnover']
    # test_turnover['test_2']=test_turnover['away_prev_turnover']-test_turnover['excel_away_prev_turnover']
    # st.write(test_turnover[test_turnover['test_1']!=0])
    # st.write(test_turnover[test_turnover['test_2']!=0])
    # st.write(test_turnover)

with st.beta_expander('Betting Slip Matches'):
    betting_matches=updated_df.loc[:,['Week','Date','Home ID','Home Team','Away ID', 'Away Team','Spread','Home Points','Away Points',
    'home_power','away_power','home_cover','away_cover','home_turnover_sign','away_turnover_sign','home_cover_sign','away_cover_sign','power_pick','home_cover_result']]
    st.write('check for duplicate home cover', betting_matches)
    betting_matches['total_factor']=betting_matches['home_turnover_sign']+betting_matches['away_turnover_sign']+betting_matches['home_cover_sign']+\
    betting_matches['away_cover_sign']+betting_matches['power_pick']
    betting_matches['bet_on'] = np.where(betting_matches['total_factor']>2,betting_matches['Home Team'],np.where(betting_matches['total_factor']<-2,betting_matches['Away Team'],''))
    betting_matches['bet_sign'] = (np.where(betting_matches['total_factor']>2,1,np.where(betting_matches['total_factor']<-2,-1,0)))
    betting_matches['bet_sign'] = betting_matches['bet_sign'].astype(float)
    betting_matches['home_cover'] = betting_matches['home_cover'].astype(float)
    st.write('this is bet sign',betting_matches['bet_sign'].dtypes)
    st.write('this is home cover',betting_matches['home_cover'].dtypes)
    betting_matches['result']=betting_matches['home_cover_result'] * betting_matches['bet_sign']
    st.write('testing sum of betting result',betting_matches['result'].sum())

    # this is for graphing anlaysis on spreadsheet
    betting_matches['bet_sign_all'] = (np.where(betting_matches['total_factor']>0,1,np.where(betting_matches['total_factor']<-0,-1,0)))
    betting_matches['result_all']=betting_matches['home_cover_result'] * betting_matches['bet_sign_all']
    st.write('testing sum of betting all result',betting_matches['result_all'].sum())
    # st.write('testing factor')
    # st.write(betting_matches['total_factor'].sum())
    # cols_to_move=[]
    # cols = cols_to_move + [col for col in data_4 if col not in cols_to_move]
    # data_5=data_4[cols]
    st.write(betting_matches)

with st.beta_expander('Historical odds'):
    # st.write(odds_data)
    odds_data=odds_data.loc[:,['Date','Home Team','Away Team','Home Score','Away Score','Home Line Close']].copy()
    team_names_id=team_names_id.rename(columns={'Team':'Home Team'})
    odds_data=pd.merge(odds_data,team_names_id,on='Home Team').rename(columns={'ID':'Home ID'}).sort_values(by='Date',ascending=False)
    team_names_id=team_names_id.rename(columns={'Home Team':'Away Team'})
    odds_data=pd.merge(odds_data,team_names_id,on='Away Team').rename(columns={'ID':'Away ID','Home Score':'Home Points','Away Score':'Away Points'}).sort_values(by='Date',ascending=False)
    st.write(odds_data.dtypes)
    st.write(odds_data)
    st.write(odds_data[odds_data['Away ID'].isna()])

with st.beta_expander('Pro Football Ref'):
    # def fbref_scraper():
    #     test = pd.read_html('https://www.pro-football-reference.com/years/2019/games.htm')[0]
    #     test.to_pickle('C:/Users/Darragh/Documents/Python/NFL/nfl_2019.pkl')
    #     return test  
        
    # test=fbref_scraper()
    nfl_2020=pd.read_pickle('C:/Users/Darragh/Documents/Python/NFL/nfl_2019.pkl')
    # st.write('This is before cleaning',nfl_2020)
    nfl_2020=nfl_2020.rename(columns={'Unnamed: 5':'at_venue'})
    nfl_2020['Home Team']=np.where(nfl_2020['at_venue']=='@',nfl_2020['Loser/tie'],nfl_2020['Winner/tie'])
    nfl_2020['at_venue']=nfl_2020['at_venue'].replace({np.nan:'stay'})
    nfl_2020['Away Team']=np.where(nfl_2020['at_venue']=='@',nfl_2020['Winner/tie'],nfl_2020['Loser/tie'])
    nfl_2020['Home Points']=np.where(nfl_2020['at_venue']=='@',nfl_2020['Pts.1'],nfl_2020['Pts'])
    nfl_2020['Away Points']=np.where(nfl_2020['at_venue']=='@',nfl_2020['Pts'],nfl_2020['Pts.1'])
    nfl_2020['Home Turnover']=(np.where(nfl_2020['at_venue']=='@',nfl_2020['TOL'],nfl_2020['TOW']))
    nfl_2020['Away Turnover']=(np.where(nfl_2020['at_venue']=='@',nfl_2020['TOW'],nfl_2020['TOL']))
    nfl_2020=nfl_2020[nfl_2020['Week'].str.contains('Week')==False].copy()
    nfl_2020['Home Turnover']=pd.to_numeric(nfl_2020['Home Turnover'])
    nfl_2020['Away Turnover']=pd.to_numeric(nfl_2020['Away Turnover'])
    nfl_2020['Home Points']=pd.to_numeric(nfl_2020['Home Points'])
    nfl_2020['Away Points']=pd.to_numeric(nfl_2020['Away Points'])
    nfl_2020['Date']=pd.to_datetime(nfl_2020['Date'])
    nfl_2020['Week'] = nfl_2020['Week'].replace({'WildCard':18,'Division':19,'ConfChamp':20,'SuperBowl':21})
    nfl_2020['Week']=pd.to_numeric(nfl_2020['Week'])
    fb_ref_2020=nfl_2020.loc[:,['Week','Day','Date','Time','Home Team', 'Away Team', 'Home Points','Away Points','Home Turnover','Away Turnover']]
    fb_ref_2020['Turnover'] = fb_ref_2020['Home Turnover'] - fb_ref_2020['Away Turnover']
    st.write(fb_ref_2020.dtypes)
    st.write('before the merge',fb_ref_2020.head())
    st.write('Check and see if this is working right')
    season_pro = pd.merge(fb_ref_2020,odds_data,on=['Date','Home Team','Away Team', 'Home Points','Away Points'], how='left')
    st.write('After MERGE sorted by week and date default',season_pro.head(3))
    st.write(season_pro.dtypes)
    st.write('Next is to set up 2020 to see how it performed, set up functions so that previous years can be run')
    # sorted_season=season_pro.sort_values(by=['Week','Home ID', 'Away ID'], ascending=[True,True,True])
    # sorted_season=sorted_season.rename(columns={'Home Team': 'Home_Team','Away Team': 'Away_Team','Away Points': 'Away_Pts',
    # 'Home Points': 'Home_Pts','Away Points': 'Away_Pts',})
    # st.write(sorted_season)
    # db=updated_df.loc[:,['Week','Date','Home Team', 'Away Team','Home ID','Away ID','Spread','Home Points','Away Points','home_turnover']].sort_values(by=['Week','Home ID'],ascending=[True,True]).copy()
    # st.write('this is workings',db.head(3))
    # test_workings=pd.merge(sorted_season,db,on=['Week','Home ID', 'Away ID'],how = 'outer')
    # test_workings['check_home_pts'] = test_workings['Home_Pts']-test_workings['Home Points']
    # test_workings['check_away_pts'] = test_workings['Away_Pts']-test_workings['Away Points']
    # test_workings['check_turnover'] = test_workings['Turnover'] - test_workings['home_turnover']
    # test_workings['check_spread']=test_workings['Spread'] - test_workings['Home Line Close']
    # st.write('combined ready for testing', test_workings)