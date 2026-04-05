# asbplayer Plugin Configuration

Configure the WebSocket server for one-click mining with asbplayer.
And/Or, configure the Texthooker Websocket server for broadcasting subtitles.

## Settings
- **enableAsbplayerServer**: Enable the WebSocket server for one-click mining
  (default: `true`). When enabled, asbplayer can connect on the configured
  `port` to receive mining commands.
- **port**: WebSocket server port for one-click mining (default: `8766`).
  Must match asbplayer's "WebSocket Server URL" setting. The URL format is
  `ws://127.0.0.1:<port>/ws`.

- **postMineAction**: Action to perform after mining a word:
    - `0` = None
    - `1` = Open Anki dialog
    - `2` = Update last card (default)
    - `3` = Export card

- **texthookerPort**: Port for the texthooker broadcast server (default:
  `8767`). Both asbplayer and texthooker-ui connect to this port.
  In texthooker-ui, set the WebSocket URL to `ws://localhost:8767`.

The two servers are fully independent. You can enable either, both, or
neither.