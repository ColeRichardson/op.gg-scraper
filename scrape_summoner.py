from bs4 import BeautifulSoup
import requests
import pprint as pp
from datetime import datetime
from pytz import timezone
now = datetime.now()
print(now)
#op.gg times are in kst korean standard time
URL = "https://na.op.gg/summoner/userName=noskillzallluck"

page = requests.get(URL)
soup = BeautifulSoup(page.content, "html.parser")
#id="SummonerLayoutContent
results = soup.find(class_="GameItemList")
#GameItemList
matches = results.find_all('div', "GameItemWrap")
#pp.pprint(matches)
x = []
format = "%Y-%m-%d %H:%M:%S %Z%z"
now_utc = datetime.now(timezone("UTC"))
#print(now_utc.strftime(format))
now_korea = now_utc.astimezone(timezone("Asia/Seoul"))
#print(now_korea.strftime(format))
#print(now_utc.country_timezones["kr"])
for match in matches:
    game_result = match.find('div', class_="GameResult")
    game_was_played = match.find("div", class_="TimeStamp")
    #print(game_result)
    time = game_was_played.text
    dtTime = datetime.strptime(time, "%Y-%m-%d %H:%M:%S")
    #print(dtTime.strftime(format))
    #print(game_was_played.text)
    time_since = now_korea.replace(tzinfo=None) - dtTime
    print(time_since.seconds/60)
    x.append(game_result)



#print(x)
