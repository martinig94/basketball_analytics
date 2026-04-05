from euroleague_api import boxscore_data
from euroleague_api.boxscore_data import *
from euroleague_api.game_stats import *
from euroleague_api.play_by_play_data import *
from euroleague_api.player_stats import *
from euroleague_api.shot_data import *
from euroleague_api.team_stats import TeamStats
competition_code = "E"

start_season = 2020
end_season = 2026

teamstats = TeamStats(competition=competition_code)
xx=teamstats.get_team_stats(endpoint="traditional")