# HA Duneweaver

This is a custom component for Home Assistant that integrates with the Duneweaver API.
It provides two buttons to trigger the playing of a random and a fitting pattern on a Duneweaver device.

## Play Fitting Pattern

The fitting pattern is determined by the current date. If the date matches an entry in the `playlist_schedule.json` file, a random pattern from the playlist with the same name will be played. Therefore, you need to create fitting playlists in the Duneweaver app and name them according to the entries in the `playlist_schedule.json` file or modify the file to match your playlist names. If there is no match, we fall back to playing a random pattern.

## Play Random Pattern

The random pattern is selected from all available patterns in the Duneweaver app, regardless of the date or playlist.