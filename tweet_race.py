import os
import json
from pathlib import Path
import requests
import tweepy
from dotenv import load_dotenv
from tweepy import Client
import re

# Mapping of racecourse names to Twitter handles
COURSE_HANDLES = {
    "Aintree":            "@AintreeRaces",
    "Ascot":              "@Ascot",
    "Bangor-on-Dee":      "@BangorRaces",
    "Bath":               "@BathRacecourse",
    "Beverley":           "@Beverley_Races",
    "Brighton":           "@BrightonRace",
    "Carlisle":           "@CarlisleRaces",
    "Cartmel":            "@CartmelRace",
    "Catterick":          "@CatterickRaces",
    "Chelmsford City":    "@ChelmsfordCRC",
    "Cheltenham":         "@CheltenhamRaces",
    "Chepstow":           "@Chepstow_Racing",
    "Chester":            "@ChesterRaces",
    "Doncaster":          "@DoncasterRaces",
    "Epsom Downs":        "@EpsomRacecourse",
    "Exeter":             "@ExeterRaces",
    "Fakenham":           "@FakenhamRC",
    "Fontwell Park":      "@FontwellPark",
    "Goodwood":           "@Goodwood_Races",
    "Great Yarmouth":     "@YarmouthRaces",
    "Hamilton Park":      "@HamiltonParkRC",
    "Haydock Park":       "@HaydockRaces",
    "Hereford":           "@HerefordRaces",
    "Hexham":             "@HexhamRaces",
    "Huntingdon":         "@Huntingdon_Race",
    "Kelso":              "@KelsoRacecourse",
    "Kempton Park":       "@kemptonparkrace",
    "Leicester":          "@LeicesterRaces",
    "Lingfield Park":     "@LingfieldPark",
    "Ludlow":             "@LudlowRaceClub",
    "Market Rasen":       "@MarketRasenRace",
    "Musselburgh":        "@MusselburghRace",
    "Newbury":            "@NewburyRacing",
    "Newcastle":          "@NewcastleRaces",
    "Newmarket":          "@NewmarketRace",
    "Newton Abbot":       "@NewtonAbbotRace",
    "Nottingham":         "@NottsRacecourse",
    "Perth":              "@PerthRacecourse",
    "Plumpton":           "@plumptonraces",
    "Pontefract":         "@ponteraces",
    "Redcar":             "@Redcarracing",
    "Ripon":              "@RiponRaces",
    "Salisbury":          "@salisburyraces",
    "Sandown Park":       "@Sandownpark",
    "Sedgefield":         "@SedgefieldRace",
    "Southwell":          "@Southwell_Races",
    "Stratford-on-Avon":  "@stratfordraces",
    "Taunton":            "@TauntonRacing",
    "Thirsk":             "@ThirskRaces",
    "Uttoxeter":          "@UttoxeterRaces",
    "Warwick":            "@WarwickRaces",
    "Wetherby":           "@WetherbyRaces",
    "Wincanton":          "@wincantonraces",
    "Windsor":            "@WindsorRaces",
    "Wolverhampton":      "@WolvesRaces",
    "Worcester":          "@WorcesterRaces",
    "York":               "@yorkracecourse",
}

# Load environment variables from a .env file
load_dotenv()

# Base URL for the Racing API
API_BASE = "https://api.theracingapi.com/v1"
# Credentials for the Racing API
USER = os.getenv("RACING_API_USER")
PASS = os.getenv("RACING_API_PASS")
# Default region code (e.g., "GB")
REGION = os.getenv("REGION", "GB")

# Twitter API credentials
TW_API_KEY = os.getenv("TW_API_KEY")
TW_API_SECRET = os.getenv("TW_API_SECRET")
TW_ACCESS_TOKEN = os.getenv("TW_ACCESS_TOKEN")
TW_ACCESS_SECRET = os.getenv("TW_ACCESS_SECRET")
TW_BEARER_TOKEN = os.getenv("TW_BEARER_TOKEN")

# File to persist posted race IDs
POSTED_FILE = Path("posted_ids.json")

def load_posted_ids():
    """
    Load the set of race IDs that have already been tweeted.
    Returns an empty set if the file does not exist.
    """
    if POSTED_FILE.exists():
        return set(json.loads(POSTED_FILE.read_text()))
    return set()


def save_posted_ids(ids):
    """
    Save the set of race IDs to a JSON file for persistence.

    Parameters:
    - ids (set): A set of race_id strings to save.
    """
    POSTED_FILE.write_text(json.dumps(list(ids)))


def get_results_by_date(date, region):
    """
    Query the Racing API for race results on a specific date, filtering by region.

    Parameters:
    - date (str): The date in YYYY-MM-DD format for which to fetch results.
    - region (str): The region code to filter results (e.g., 'GB').

    Returns:
    - List[dict]: A list of result objects matching the specified region.
    """
    url = f"{API_BASE}/results"
    response = requests.get(
        url,
        auth=(USER, PASS),
        params={
            "start_date": date,
            "end_date":   date
        }
    )
    response.raise_for_status()

    data = response.json().get("results", [])
    # Filter results by the specified region
    return [r for r in data if r.get("region") == region]


def format_tweet(race):
    """
    Construct the text for a tweet announcing race results.

    Parameters:
    - race (dict): A race object containing keys 'course', 'off', 'race_id', and 'runners'.

    Returns:
    - str: The formatted tweet text.
    """
    course = race['course']
    # Look up the Twitter handle for the course, defaulting to the course name
    handle = COURSE_HANDLES.get(course, course)
    header = f"{race['off']} at {handle}"  # Race off time and course handle/name

    # Select the top 3 finishers, sorted by position
    runners = sorted(race["runners"], key=lambda x: int(x["position"]))[:3]
    lines = [header, ""]

    for r in runners:
        # Remove any parentheses content from the horse name
        horse = re.sub(r"\s*\([^)]*\)", "", r["horse"]).strip()
        # Choose starting price (SP) if available
        sp = r.get("sp") or r.get("sp_dec") or ""
        lines.append(f"{r['position']}. {horse} {sp}")

    lines.append("")
    lines.append(
        "Sign up for early access to the UK's best #horseracing tipping platform > https://punting.io"
    )
    return "\n".join(lines)


def post_tweet(text):
    """
    Publish a tweet using the Twitter API client.

    Parameters:
    - text (str): The tweet content.

    Returns:
    - tweepy.Response: The response object from creating the tweet.
    """
    client = Client(
        consumer_key=TW_API_KEY,
        consumer_secret=TW_API_SECRET,
        access_token=TW_ACCESS_TOKEN,
        access_token_secret=TW_ACCESS_SECRET
    )

    return client.create_tweet(text=text)


def main():
    """
    Main entry point for the script:
    1. Determine today's date (UTC).
    2. Load previously posted race IDs.
    3. Fetch today's race results for the configured region.
    4. For each new race result, format and send a tweet (up to a limit).
    5. Persist the updated list of posted race IDs.
    """
    from datetime import datetime, timezone

    # Format today's date in UTC for the API
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    posted = load_posted_ids()
    new_posted = set(posted)

    max_per_run = 5  # Maximum number of tweets to send in one run
    sent_count = 0

    # Fetch and filter race results
    races = get_results_by_date(today, REGION)

    for race in races:
        rid = race["race_id"]
        if rid in posted:
            continue

        # Format the tweet text
        tweet_text = format_tweet(race)
        try:
            resp = post_tweet(tweet_text)
            tweet_id = resp.data["id"]
            print(f"Posted tweet {tweet_id} for race {rid}")
            new_posted.add(rid)
            sent_count += 1

            # Stop early if we've reached the per-run tweet limit
            if sent_count >= max_per_run:
                print(
                    f"Reached {max_per_run} tweets this run, stopping early to avoid rate limits."
                )
                break
        except Exception as e:
            err_msg = str(e)
            print(f"Error posting race {rid}: {err_msg}")
            # Handle duplicate content errors by marking the race as posted
            if "duplicate content" in err_msg.lower():
                print(f"Skipping race {rid}: tweet already exists.")
                new_posted.add(rid)
            # Handle rate limit errors (HTTP 429)
            elif "too many requests" in err_msg.lower() or "429" in err_msg:
                print("Rate limit hit (429). Stopping further tweets in this run.")
                break
            else:
                print(f"Unhandled error for race {rid}: {err_msg}")

    # Save the updated set of posted IDs
    save_posted_ids(new_posted)


if __name__ == "__main__":
    main()
