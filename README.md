# YouTube Community Contributions Archiving Worker

Worker for the `Save Community Captions` project: Archiving unpublished YouTube community-contributions.

## Setup

To run these tools you will need to supply session cookies (SSID,HSID,SID) [see the
tutorial for more details](https://github.com/Data-Horde/ytcc-archive/wiki/Setup-Tutorial).

## Primary Usage

### Heroku⭐️⭐️⭐️ (Minimal Setup! Minimal Maintence!)
A wrapper repo for free and easy deployment and environment configuration, as well automatic updates every 24-27.6 hours is available. Deploy up to 5 instances of it to a free Heroku account (total max monthly runtime 550 hours) with no need for credit card verification by clicking the button below.

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/Data-Horde/ytcc-archive-heroku)

### Archiving Worker⭐️
After completing the above setup steps, simply run 
```bash
python3 worker.py
```

### Docker image⭐️⭐️

Stable Docker Image:
```bash
docker pull fusl/ytcc-archive
```

Run:
```bash
docker container run --restart=unless-stopped --network=host -d --tmpfs /grab/out --name=grab_ext-yt-communitycontribs -e HSID=XXX-e SID=XXX -e SSID=XXX -e TRACKER_USERNAME=Fusl -e PYTHONUNBUFFERED=1 fusl/ytcc-archive
```
## Bonus Features
### Export Captions and Titles/Descriptions Manually
Simply run `python3 exporter.py` followed by a list of space-separated YouTube video IDs, and all community-contributed captioning and titles/descriptions in all languages will be exported.

### Discover Videos Manually
Simply run `python3 discovery.py` followed by a list of space-separated YouTube video IDs and a list of discovered video, channel and playlist IDs will be printed, as well as whether caption contributions are enabled.

# Stats
See how much has been archived so far.

* https://atdash.meo.ws/d/attv2/archive-team-tracker-charts-v2?orgId=1&var-project=ext-yt-communitycontribs 
* https://tracker.archiveteam.org/ext-yt-communitycontribs/
