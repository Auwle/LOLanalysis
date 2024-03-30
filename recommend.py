import sqlite3
conn = sqlite3.connect(r"C:\Users\VINH\Desktop\lol analyst\lolanalysis.db")
cur = conn.cursor()

###############################################################################################
# This function is used to retrieve of head-to-head matchup ( same lane)
def HeadToHead():
    champ_name = input('Enter champion name:')
    
    # First SQL statement: Get the ID of the champion
    query0 = '''SELECT id as champ_id
               FROM Champs
               WHERE name = ?'''
    cur.execute(query0, (champ_name,))
    champ_id = cur.fetchone()[0]  # Fetch the champ_id value
    
    # Second SQL statement: Create temporary table ChampionMatches where show all the matches that champion participated
    query1 = '''
    CREATE TEMPORARY TABLE ChampionMatches AS
    SELECT *
    FROM Participants
    WHERE matchid IN 
    (
        SELECT matchid
        FROM Participants
        WHERE championid = ?
    )
    '''
    cur.execute(query1, (champ_id,))
    
    # Third SQL statement: Create temporary table HtH, get all the records in those matches of enemy champion in the same position
    query2 = '''
    CREATE TEMPORARY TABLE HtH AS
    SELECT id, championid, position, player
    FROM ChampionMatches
    WHERE position = 
    (
        SELECT position 
        FROM Participants 
        WHERE championid = ?
    )
    AND championid != ?
    '''
    cur.execute(query2, (champ_id, champ_id))
    
    # Fourth SQL statement: Calculate winrate, match >= 50 to have enough data for evidence
    query3 = '''
    SELECT championid, COUNT(championid) as match, AVG(WL) as winrate, name
    FROM
    (
        SELECT id, championid, CASE WHEN player = win THEN 0 ELSE 1 END as WL, name
        FROM
        (
            SELECT HtH.id, HtH.championid, HtH.player, Stats.win, Champs.name
            FROM HtH 
            INNER JOIN Stats ON HtH.id = Stats.id 
            INNER JOIN Champs ON HtH.championid = Champs.id
        )
    )
    GROUP BY championid
    HAVING match >= 50
    ORDER BY winrate DESC
    '''
    cur.execute(query3)
    
    # Fetch and print results
    rows = cur.fetchall()
    for row in rows:
        print(row)

    # Commit and close the connection
    conn.commit()

# Call the Champ function
    conn.close()

###############################################################################################
# These functions are used to get the best pick given ally and enemy combination
def Data():        # The first step: create a table that can contain winrate after calculation
    query = '''Create temporary table Data
            (
                championid int, 
                match int, 
                winrate float, 
                name varchar(15)
            )'''
    cur.execute(query)

def Champ(champ_name):
    # First SQL statement: Get the ID of the champion
    query0 = '''SELECT id as champ_id
               FROM Champs
               WHERE name = ?'''
    cur.execute(query0, (champ_name,))
    champ_id = cur.fetchone()[0]  # Fetch the champ_id value 
    return champ_id
   
def ChampionMatches(champ_id):
    query1 = ''' drop table if exists ChampionMatches'''
    cur.execute(query1)
    query1_1 = '''
    CREATE TEMPORARY TABLE ChampionMatches AS
    SELECT *
    FROM Participants
    WHERE matchid IN 
    (
        SELECT matchid
        FROM Participants
        WHERE championid = ?
    )
    '''
    cur.execute(query1_1, (champ_id,))

def Ally(champ_id):
    query2 = ''' drop table if exists Ally '''
    cur.execute(query2)
    query2_1 = '''create TEMPORARY table Ally as
                    SELECT * FROM ChampionMatches
                    WHERE (matchid, player) IN 
                    (
                        SELECT matchid, player
                        FROM ChampionMatches
                        WHERE championid = ?
                    );
                '''
    cur.execute(query2_1,(champ_id,))

def Enemy(champ_id):
    query2 = '''drop table if exists Enemy'''
    cur.execute(query2)
    query2_1 = '''create TEMPORARY table Enemy as
                    SELECT * FROM ChampionMatches
                    WHERE (matchid, player) IN 
                    (
                        SELECT matchid, player
                        FROM ChampionMatches
                        WHERE championid = ?
                    )
                    and player != 
                    (
                        select player from ChampionMatches
                        WHERE championid = ?
                    )
                '''
    cur.execute(query2_1,(champ_id,champ_id))
       
def CalculateWinrate(champ_id):
    query = 'drop table if exists HtH'
    cur.execute(query)

    query3 = '''
    CREATE TEMPORARY TABLE HtH AS
    SELECT id, championid, position, player
    FROM ChampionMatches
    WHERE championid != ?
    '''
    cur.execute(query3, (champ_id,))

    query4 = '''
    INSERT INTO Data 
    SELECT championid, COUNT(championid) as match, AVG(WL) as winrate, name
    FROM
    (
        SELECT id, championid, CASE WHEN player = win THEN 0 ELSE 1 END as WL, name
        FROM
        (
            SELECT HtH.id, HtH.championid, HtH.player, Stats.win, Champs.name
            FROM HtH 
            INNER JOIN Stats ON HtH.id = Stats.id 
            INNER JOIN Champs ON HtH.championid = Champs.id
        )
    )
    GROUP BY championid
    ORDER BY match DESC
    '''
    cur.execute(query4)

def Championwinrate():
    query5 = '''Select championid, avg(match), avg(winrate), name 
                from Data 
                group by name 
                order by avg(winrate) desc
            '''
    cur.execute(query5)
    rows = cur.fetchall()
    for row in rows:
        print(row)

    # Commit and close the connection
    conn.commit()

def RecommendChamp():
    while True:
        whose_turn = input('If Ally is picking pick, type 1; if Enemy is picking pick, type 2; your pick: type 3:')
        if whose_turn == '1':
            champ_name = input('Type ally champion:')
            champ_id = Champ(champ_name)
            ChampionMatches(champ_id)
            Ally(champ_id)
            CalculateWinrate(champ_id)
            continue
        if whose_turn == '2':
            champ_name = input('Type enemy champion:')
            champ_id = Champ(champ_name)
            ChampionMatches(champ_id)
            Enemy(champ_id)
            CalculateWinrate(champ_id)
            continue
        if whose_turn == '3':
            Championwinrate()
            break
        else: 
            question = input('Are you sure that you want to quit? Type Yes: ')
            if question.lower() == 'yes':
                break 
            else:
                continue

###############################################################################################
Data()
x = input('Type 1 for HeadToHead, type 2 for RecommendChamp:')
while True:
    if x == '1': 
        HeadToHead()
        continue
    if x == '2':
        RecommendChamp()
        break
    else: 
        conn.close()
        break

# not sure when to break and close connection =)