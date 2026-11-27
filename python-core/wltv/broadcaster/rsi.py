# -*- coding: utf-8 -*-

import requests
from lib import config, logger, utils
from lib.broadcaster_result import BroadcasterResult

HOST = "https://www.rsi.ch"
BASEURL = "https://il.srgssr.ch/integrationlayer/3.0/mediaComposition/byUrn/%s.json?onlyChapters=false&vector=portalplay"

mpd = config.getSetting("mpd")

def play(search):
    res = BroadcasterResult()

    url = ""
    license_url = ""
    preferred_protocol = "DASH" if mpd else "HLS"
    fallback_protocol = "HLS" if mpd else "DASH"

    try:
        json_data = requests.get("https://www.rsi.ch/play/v3/api/rsi/production/tv-livestreams").json()["data"]
    except Exception as e:
        logger.error(f"Failed to fetch mainline tv-livestreams: {e}")
        return res

    headers = utils.getBrowserHeaders(host=HOST)
    
    for item in json_data:
        if "title" in item and "livestreamUrn" in item:
            if search.lower() == item["title"].lower():
                livestream_urn = item["livestreamUrn"]
                streams_url = BASEURL % livestream_urn
                
                try:
                    media_data = requests.get(streams_url, headers=headers).json()
                    chapter_list = media_data.get("chapterList", [])
                    
                    if not chapter_list:
                        continue
                        
                    resource_list = chapter_list[0].get("resourceList", [])
                    found_resource = next(filter(lambda key: key.get("protocol") == preferred_protocol, resource_list), None)

                    if not found_resource:
                        found_resource = next(filter(lambda key: key.get("protocol") == fallback_protocol, resource_list), None)
                        if found_resource:
                            logger.info(f"Preferred protocol {preferred_protocol} missing for '{search}'. Using fallback: {fallback_protocol}")

                    if found_resource:
                        url = found_resource.get("url", "")
                        
                        actual_protocol = found_resource.get("protocol")
                        drm_type = "WIDEVINE" if actual_protocol == "DASH" else "FAIRPLAY"
                        
                        drm_list = found_resource.get("drmList", [])
                        drm = next(filter(lambda key: key.get("type") == drm_type, drm_list), None)
                        
                        if drm:
                            license_url = drm.get("licenseUrl", "")
                            
                except Exception as e:
                    logger.error(f"Error parsing stream resources for {search}: {e}")
                break

    if url:
        headers["Accept"] = "*/*"
        headers["Content-Type"] = "application/octet-stream"
        
        license_config = { 
            'license_server_url': license_url,
            'headers': utils.dict2querystring(headers),
            'post_data': 'R{SSM}',
            'response_data': 'R'
        }

        res.StreamHeaders = headers
        res.Url = url
        res.LicenseKey = '|'.join(license_config.values())
        res.ManifestUpdateParameter = "full"

    return res