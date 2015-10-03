#!/usr/bin/python
from operator import itemgetter
import urllib
import httplib
import json
import logging
import logging.handlers
import os
import glob
import ConfigParser
import argparse

logging.basicConfig(level=logging.DEBUG,
                    format='%(levelname)-8s %(message)s')

# setup weekly log file
log_path = os.path.join(os.path.dirname(__file__), 'logs')
log_file = os.path.join(log_path, 'sonarr-episode-trimmer.log')
if not os.path.exists(log_path):
    os.mkdir(os.path.dirname(log_file))
file_handler = logging.handlers.TimedRotatingFileHandler(log_file, when='D', interval=7, backupCount=4)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
logging.getLogger('').addHandler(file_handler)


# make a request to the sonarr api
def api_request(action, params=None, method='GET', body=None):
    if params is None:
        params = {}

    params['apikey'] = CONFIG.get('API', 'key')

    url = "/api/%s?%s" % (action, urllib.urlencode(params))

    conn = httplib.HTTPConnection(CONFIG.get('API', 'url'))
    conn.request(method, url, body)
    resp = conn.getresponse()

    resp_body = resp.read()

    if resp.status < 200 or resp.status > 299:
        logging.error('%s %s', resp.status, resp.reason)
        logging.error(resp_body)

    return json.loads(resp_body)


def unmonitor_episode(episode):
    logging.info("Unmonitoring episode: season=%s, episode=%s, airdate=%s", episode['seasonNumber'],
                 episode['episodeNumber'], episode['airDate'])

    if not DEBUG:
        episode['monitored'] = False
        api_request('episode', method='PUT', body=json.dumps(episode))


# remove old episodes from a series
def clean_series(series_id, keep_episodes):
    # get the episodes for the series
    all_episodes = api_request('episode', {'seriesId': series_id})

    # filter only downloaded episodes
    episodes = [episode for episode in all_episodes if episode['hasFile']]

    # sort episodes
    episodes = sorted(episodes, key=itemgetter('seasonNumber', 'episodeNumber'))

    logging.debug("# of episodes downloaded: %s", len(episodes))
    logging.debug("# of episodes to delete: %s", len(episodes[:-keep_episodes]))

    # filter monitored episodes
    monitored_episodes = [episode for episode in all_episodes if episode['monitored']]
    logging.debug("# of episodes monitored: %s", len(monitored_episodes))
    monitored_episodes = sorted(monitored_episodes, key=itemgetter('seasonNumber', 'episodeNumber'))

    # unmonitor episodes older than the last one downloaded
    # do this to keep older episodes that failed to download, from being searched for
    logging.info("Unmonitoring old episodes:")
    if len(episodes) > 0 and len(monitored_episodes) > 0:
        try:
            for episode in monitored_episodes[:monitored_episodes.index(episodes[0])]:
                unmonitor_episode(episode)
        except ValueError:
            logging.warn("There is an episode with a file that is unmonitored")

    # process episodes
    for episode in episodes[:-keep_episodes]:
        logging.info("Processing episode: %s", episode['title'])

        # get information about the episode's file
        episode_file = api_request('episodefile/%s' % episode['episodeFileId'])

        # delete episode
        logging.info("Deleting file: %s", episode_file['path'])
        if not DEBUG:
            api_request('episodefile/%s' % episode_file['id'], method='DELETE')

        # delete any additional files
        path, ext = os.path.splitext(episode_file['path'])
        path = path.replace(SONARR_PATH, ADDITIONAL_FILES_PATH)
        for f in glob.glob(path + "*"):
            logging.info("Deleting file: %s", f)
            logging.debug(os.path.exists(f))
            if not DEBUG:
                try:
                    os.remove(f)
                except OSError, e:
                    logging.error("Could not delete: %s", e.filename)

        # mark the episode as unmonitored
        unmonitor_episode(episode)


if __name__ == '__main__':
    global CONFIG
    global DEBUG
    global ADDITIONAL_FILES_PATH
    global SONARR_PATH

    # parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action='store_true', help='Run the script in debug mode. No modifications to '
                                                             'the sonarr library or filesystem will be made.')
    parser.add_argument("--config", type=str, required=True, help='Path to the configuration file.')
    args = parser.parse_args()

    DEBUG = args.debug

    # load config file
    CONFIG = ConfigParser.SafeConfigParser()
    CONFIG.read(args.config)

    # determine base path for additional files
    rootfolder = api_request('rootfolder')
    SONARR_PATH = rootfolder[0]['path']
    try:
        ADDITIONAL_FILES_PATH = CONFIG.get('Config', 'path')
        logging.debug("Using config path for additional files: %s", ADDITIONAL_FILES_PATH)
    except ConfigParser.NoSectionError:
        ADDITIONAL_FILES_PATH = SONARR_PATH
        logging.debug("Using sonarr path for additional files: %s", ADDITIONAL_FILES_PATH)

    # get all the series in the library
    series = api_request('series')

    # build mapping of titles to series
    series = {x['cleanTitle']: x for x in series}

    for s in CONFIG.items('Series'):
        if s[0] in series:
            logging.info("Processing: %s", series[s[0]]['title'])
            clean_series(series[s[0]]['id'], int(s[1]))
        else:
            logging.warning("series '%s' from config not found in sonarr", s[0])
