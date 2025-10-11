def add_win_labels(df):
    df = df.copy()
    match_outcomes = {}
    for mid in df['matchId'].unique():
        match_slice = df[df['matchId'] == mid]
        team_100_avg_gold = match_slice[match_slice['teamId'] == 100]['gold_20'].mean()
        team_200_avg_gold = match_slice[match_slice['teamId'] == 200]['gold_20'].mean()
        match_outcomes[mid] = team_100_avg_gold > team_200_avg_gold
    df['win'] = df.apply(lambda row: match_outcomes[row['matchId']] if row['teamId'] == 100 else not match_outcomes[row['matchId']], axis=1)
    return df

def create_target_variables(df):
    df = add_win_labels(df)
    df['gold_growth'] = df['gold_20'] - df['gold_14']
    df['xp_growth'] = df['xp_20'] - df['xp_14']
    df['kda_14'] = (df['kills_14'] + df['assists_14']) / (df['deaths_14'] + 1)
    return df
