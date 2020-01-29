from typing import List
# webscraping
from bs4 import BeautifulSoup
import requests
# import pprint as pp
# date stuff
from datetime import datetime
from datetime import timedelta
from pytz import timezone

#google sheets integration
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# op.gg times are in kst korean standard time
format = "%Y-%m-%d %H:%M:%S %Z%z"


def update_summoner(url: str)->None:
    """
    uses selenium to click the update button for the given summoner
    """
    from selenium.webdriver import Chrome
    import time
    # import options so we can make our webdriver headless
    from selenium.webdriver.chrome.options import Options

    # instantiate Options object
    chrome_options = Options()
    # add the argument headless to that object
    chrome_options.add_argument("--headless")
    webdriver = "C:/Users/ColeR/Documents/chromedriver.exe"
    # pass in the options objct we created and the path to our chromedriver
    driver = Chrome(options=chrome_options, executable_path=webdriver)
    driver.get(url)
    button = driver.find_element_by_id('SummonerRefreshButton')
    button.click()
    # pause the program for 5 seconds to make sure the update goes through
    #time.sleep(10)
    driver.close()


#now_est:datetime
def get_game_day(game_time:datetime)-> str:
    """
    #TODO: change this to get the day the game occurred adjusted with the 2am rule
    gets the current day at time of running this script,
    if time is less than 3am we count it as previous day checks if it is the
    first day of the month.
    returns a string containing the adjusted date in the format YYYY-MM-DD
    Examples:
    >>> get_game_day(datetime.strptime("2020-01-25 19:31:57", "%Y-%m-%d %H:%M:%S"))
    '2020-01-25'
    >>> get_game_day(datetime.strptime("2020-01-25 01:31:57", "%Y-%m-%d %H:%M:%S"))
    '2020-01-24'
    >>> get_game_day(datetime.strptime("2020-02-01 01:31:57", "%Y-%m-%d %H:%M:%S"))
    '2020-01-31'
    """
    # this variable will hold the adjusted datetime.day value
    adj_cur_day = now_est
    cur_time = now_est.hour
    #print("current time " + str(cur_time))

    # since we will count games played until 3am as the previous day
    if cur_time <= 2:
        adj_cur_day -= timedelta(days=1)
    #print("current day " + str(adj_cur_day))
    return str(adj_cur_day.date())


def get_new_matches(url: str, last_check:str)-> int:
    """
    returns all the matches that have been played 30 minutes or less ago
    #TODO: when getting new matches also make a tally of the days w/l ratio

    #TODO: check if the game result was a remake, if it was a remake it shouldnt
    be added.
    """
    new_games = 0
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")

    # GameItemList is the div class that holds all the gameItemWraps
    results = soup.find(class_="GameItemList")

    # GameItemWrap is the div that holds all the game info
    matches = results.find_all('div', "GameItemWrap")
    print("last check was at: " + str(last_check))
    for match in matches:
        game_was_played = match.find("div", class_="TimeStamp")
        game_time = datetime.strptime(game_was_played.text, "%Y-%m-%d %H:%M:%S")

        # this is to adjust for the timechange of the 14 hours korea is ahead
        game_time_est = game_time - timedelta(hours=14)
        last_check_dt = datetime.strptime(last_check, "%Y-%m-%d %H:%M:%S")
        game_result = match.find('div', class_="GameResult").text.strip()

        # if a game has occurred since the last check increment new_games
        if game_time_est > last_check_dt:
            if game_result != "Remake":
                new_games += 1
                print("new game found! ")
                print("game time: " + str(game_time_est))
            # print(str(game_time.date()) + str(game_time.time()))
    return new_games


class Sheet:
    """

    """
    def __init__(self):
        """

        """
        scope = ["https://spreadsheets.google.com/feeds",
                'https://www.googleapis.com/auth/spreadsheets',
                "https://www.googleapis.com/auth/drive.file",
                "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(
        "client_secret.json", scope)
        client = gspread.authorize(creds)
        self.sheet = client.open("lol games/day").sheet1

    def update_gsheet(self, cur_day: str, new_games: int)->None:
        """
        cur_day: the current day the games are to be recorded into
        new_games: the number of new games found since the last check

        updates the google sheets database adds a 1 to the adjusted day where the
        game was played if a new game was found by get_new_matches
        """

        cur_cell = self.sheet.find(cur_day)
        todays_games = self.sheet.cell(cur_cell.row, cur_cell.col + 1).value
        if todays_games:
            self.sheet.update_cell(cur_cell.row, cur_cell.col + 1, str(int(todays_games) + new_games))
        else:
            self.sheet.update_cell(cur_cell.row, cur_cell.col + 1, str(new_games))


    def set_last_check(self, day, time):
        """
        update the special cell to be updated to store the current time.
        since that will have been the last check
        """
        self.sheet.update_cell(35, 1, day + " " + time)

    def get_last_check(self)->str:
        """
        get the date and time of the last check, the data from the cell in the sheet
        returns a string holding the date and time
        """
        return self.sheet.cell(35, 1).value

if __name__ == "__main__":
    sheet = Sheet()
    summoner_names = ["noskillzallluck", "hydrosq", "skillzy", "spearagirl"]
    # curr not in use by me ="lonely+fayze"

    now_utc = datetime.now(timezone("UTC"))
    now_est = now_utc.astimezone(timezone("America/Toronto"))
    now_korea = now_utc.astimezone(timezone("Asia/Seoul"))

    for summoner in summoner_names:
        url = "https://na.op.gg/summoner/userName=" + summoner
        update_summoner(url)
        cur_day = get_game_day(now_est)
        new_matches = get_new_matches(url, sheet.get_last_check())

        if new_matches:
            sheet.update_gsheet(cur_day, new_matches)

    sheet.set_last_check(str(now_est.date()), str(now_est.time()))
