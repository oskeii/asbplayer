from __future__ import annotations

import uuid

from aqt import mw, gui_hooks
from anki.notes import Note
from anki.decks import DeckId
from anki.collection import Collection, OpChanges

from .model.config import AddonConfig
from .server.websocket_server import (
    AsbplayerWebSocketServer,
    TexthookerBroadcastServer,
    _log
)

config: AddonConfig | None = None
server: AsbplayerWebSocketServer | None = None
texthooker_server: TexthookerBroadcastServer | None = None


def _on_add_note(self: Collection, note: Note, deck_id: DeckId) -> OpChanges:
    """Monkey-patched add_note that intercepts all note additions."""
    res: OpChanges = Collection._original_add_note(self, note, deck_id)
    mw.taskman.run_on_main(lambda: _handle_note_added(note))
    return res


def _handle_note_added(note: Note) -> None:
    """Handle note addition - send mine-subtitle command to asbplayer."""

    _log(f"_handle_note_added triggered for note id={note.id}")

    if server is None or config is None or not server.has_clients():
        return

    fields = {}
    for field_name in note.keys():
        fields[field_name] = note[field_name]

    message_id = str(uuid.uuid4())
    command = {
        "command": "mine-subtitle",
        "messageId": message_id,
        "body": {
            "fields": fields,
            "postMineAction": config.get_post_mine_action(),
        },
    }

    server.send_message(command)


def start_server() -> None:
    """Start the WebSocket servers (based on config flags)."""
    global server, texthooker_server

    if config is None:
        return

    # Mining server
    if config.is_asbbplayer_server_enabled() and server is None:
        _log(f"Starting asbplayer mining server on port {config.get_port()}")
        server = AsbplayerWebSocketServer(config.get_port())

        if not server.start():
            _log(f"Failed to start asbplayer mining server on port {config.get_port()}")
            server = None


    # Texthooker broadcast server
    if config.is_texthooker_server_enabled() and texthooker_server is None:
        port = config.get_texthooker_port()
        _log(f"Starting texthooker server on port {port}")
        texthooker_server = TexthookerBroadcastServer(port)

        if not texthooker_server.start():
            _log(f"Failed to start texthooker server on port {port}")
            texthooker_server = None



def stop_server() -> None:
    """Stop both WebSocket servers."""
    global server, texthooker_server

    if server is not None:
        server.stop()
        server = None

    if texthooker_server is not None:
        texthooker_server.stop()
        texthooker_server = None


def on_profile_loaded() -> None:
    """Called when a profile is loaded - start servers."""
    start_server()


def on_profile_will_close() -> None:
    """Called when profile is about to close - stop servers."""
    stop_server()


def _setup_hooks() -> None:
    """Set up monkey-patching for Collection.add_note."""
    Collection._original_add_note = Collection.add_note
    Collection.add_note = _on_add_note


config = AddonConfig(__name__)

_setup_hooks()

gui_hooks.profile_did_open.append(on_profile_loaded)
gui_hooks.profile_will_close.append(on_profile_will_close)

if mw.col is not None:
    start_server()
