# Sonarr Episode Trimmer

## FORKED FROM https://gitlab.com/spoatacus/sonarr-episode-trimmer
## Quickly changed some code to make it work with latest release of Sonarr, probably not that stable.

A script for use with Sonarr that allows you to set the number of episodes of a show that you would like to keep.
Useful for shows that air daily.

The script sorts the episodes you have for a show by the season and episode number, and then deletes the oldest episodes
past the threshold you set.


## Configuration

Configuration is pretty straight forward as this sample config file shows. The keys under the Series section are the
"cleanTitle" returned from the https://github.com/Sonarr/Sonarr/wiki/Series[Sonarr API]. The values are the number of
episodes you would like to keep for the show. Add a key/value pair for each show you want to clean.

-------------------------------------
[API]
url = localhost:8989
url_base = /sonarr
key = XXXXX

[Series]
thedailyshow = 10
midnight = 10
thetonightshowstarringjimmyfallon = 10
conan2010 = 10
latenightwithsethmeyers = 10
thelatelateshowwithjamescorden = 10
thelateshowwithstephencolbert = 10
-------------------------------------


## Usage
-------
usage: sonarr-episode-trimmer.py [-h] [--debug] --config CONFIG
                                 [--list-series] [--custom-script]

optional arguments:
  -h, --help       show this help message and exit
  --debug          Run the script in debug mode. No modifications to the
                   sonarr library or filesystem will be made.
  --config CONFIG  Path to the configuration file.
  --list-series    Get a list of shows with their 'cleanTitle' for use in the
                   configuration file
  --custom-script  Run in 'Custom Script' mode. This mode is meant for adding
                   the script to sonarr as a 'Custom Script'. It will run
                   anytime a new episode is downloaded, but will only cleanup
                   the series of the downloaded episode.
-------


### Sonarr Custom Script
The easiest way to use the script is to set it up as a custom script inside sonarr. This method will run the script
anytime sonarr processes a new episode.

. Go to the settings page
. Click on the *Connect* tab
. Hit the *+* sign
. Choose *Custom Script*
. Fill in the settings +
![sonarr custom script](docs/images/sonarr_custom_script.png)
** *Name*: sonarr-episode-trimmer
** *On Grab*: No
** *On Download*: Yes
** *On Upgrade*: No
** *On Rename*: No
** *Path*: use the absolute path to the script
** *Arguments*: `--config /absolute/path/to/config/file --custom-script`
. Click the *Test* button. *NOTE*: This will not run the script, just verify that sonarr can find the script.
. Click *Save*
