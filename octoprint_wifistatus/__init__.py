# coding = utf-8

_pythonwifi_imported_ = False

import octoprint.plugin
import sys
import logging
from octoprint.util import RepeatedTimer

try:
    from .pythonwifi.iwlibs import Wireless, getWNICnames

    _pythonwifi_imported_ = True
except:
    pass


def __plugin_check__():
    if sys.platform.startswith("linux") and _pythonwifi_imported_:
        return True
    else:
        return False


class WiFiStatusPlugin(
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.AssetPlugin,
):
    def __init__(self):
        self._updateTimer = None

    def on_after_startup(self):
        self._logger.info("WiFiStatus loaded!")
        self.start_update_timer(10.0)

    def get_assets(self):
        return {
            "js": ["js/wifistatus.js"],
            "css": ["css/wifistatus.css"],
        }

    def start_update_timer(self, interval):
        self._updateTimer = RepeatedTimer(
            interval, self.update_wifi_status, run_first=True
        )
        self._updateTimer.start()
        self._logger.debug("WiFiStatus: started timer!")

    def update_wifi_status(self):
        self._logger.debug("WiFiStatus: timer fired!")
        try:
            wifi = None
            essid = None
            for interface in getWNICnames():
                wifi = Wireless(interface)
                essid = wifi.getEssid()
                if essid:
                    break
            else:
                interface = None

            net_data = {"interface": interface, "essid": essid}

            if not interface is None:
                net_data["bitrate"] = wifi.getBitrate()
                stat, qual, discard, missed_beacon = wifi.getStatistics()
                net_data["qual"] = qual.quality
                net_data["qual_max"] = wifi.getQualityMax().quality
                net_data["signal"] = qual.signallevel
                net_data["noise"] = qual.noiselevel
                net_data["ap_mac"] = wifi.getAPaddr()

            self._logger.debug(net_data)

            self._plugin_manager.send_plugin_message(self._identifier, net_data)
        except Exception as exc:
            self._logger.debug("WiFiStatus: timer exception: {}".format(exc.args))

    def get_update_information(self):
        return {
            "wifistatus": {
                "displayName": "WiFi Status Plugin",
                "displayVersion": self._plugin_version,
                # version check: github repository
                "type": "github_release",
                "user": "ManuelMcLure",
                "repo": "OctoPrint-WiFiStatus",
                "current": self._plugin_version,
                # update method: pip w/ dependency links
                "pip": "https://github.com/ManuelMcLure/OctoPrint-WiFiStatus/archive/{target_version}.zip",
            }
        }


__plugin_pythoncompat__ = ">=3.7,<4"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = WiFiStatusPlugin()

    # ~~ Softwareupdate hook

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
    }
