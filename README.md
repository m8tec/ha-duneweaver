# HA Dune Weaver

This is a custom component for Home Assistant that integrates with the [Dune Weaver](https://github.com/tuanchris/dune-weaver) API.
It provides two buttons to trigger the playing of a random and a fitting pattern on a Dune Weaver device.

## Play Fitting Pattern

The fitting pattern is determined by the current date. If the date matches an entry in the `playlist_schedule.json` file, a random pattern from the playlist with the same name will be played. Therefore, you need to create fitting playlists on the Dune Weaver device and name them according to the entries in the `playlist_schedule.json` file or modify the file to match your playlist names. If there is no match, we fall back to playing a random pattern.

## Play Random Pattern

The random pattern is selected from all available patterns on the Dune Weaver device, regardless of the date or playlist.