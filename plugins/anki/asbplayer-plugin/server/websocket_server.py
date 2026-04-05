from __future__ import annotations

import json


def _log(msg: str) -> None:
    """Print debug message."""
    print(f"[asbplayer-plugin] {msg}")


try:
    from aqt.qt import QObject, pyqtSlot
    from PyQt6.QtWebSockets import QWebSocketServer, QWebSocket
    from PyQt6.QtNetwork import QHostAddress

    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False


if WEBSOCKETS_AVAILABLE:

    class AsbplayerWebSocketServer(QObject):
        """WebSocket server for asbplayer communication (one-click mining)."""

        def __init__(self, port: int, parent: QObject | None = None):
            super().__init__(parent)
            self._port = port
            self._server: QWebSocketServer | None = None
            self._client: QWebSocket | None = None

        def start(self) -> bool:
            """Start the WebSocket server. Returns True on success."""
            if self._server is not None:
                return True

            self._server = QWebSocketServer(
                "asbplayer-plugin", QWebSocketServer.SslMode.NonSecureMode, self
            )

            if not self._server.listen(QHostAddress.SpecialAddress.Any, self._port):
                _log(
                    f"Failed to listen on port {self._port}: {self._server.errorString()}"
                )
                self._server = None
                return False

            self._server.newConnection.connect(self._on_new_connection)
            _log(f"WebSocket server started on port {self._port}")
            return True

        def stop(self) -> None:
            """Stop the WebSocket server and disconnect the client."""
            if self._server is None:
                return

            if self._client is not None:
                self._client.close()
                self._client = None

            self._server.close()
            self._server = None
            _log("WebSocket server stopped")

        def has_clients(self) -> bool:
            """Return True if there is a connected client."""
            return self._client is not None

        def send_message(self, message: dict) -> None:
            """Send a JSON message to the connected client."""
            if self._client is None or not self._client.isValid():
                return

            json_str = json.dumps(message)
            self._client.sendTextMessage(json_str)

        @pyqtSlot()
        def _on_new_connection(self) -> None:
            """Handle new client connection, replacing any existing one."""
            if self._server is None:
                return

            client = self._server.nextPendingConnection()
            if client is None:
                return

            if self._client is not None:
                _log("Replacing existing client connection")
                self._client.close()

            self._client = client

            client.textMessageReceived.connect(self._on_text_message)
            client.disconnected.connect(self._on_client_disconnected)

            _log(f"Client connected: {client.peerAddress().toString()}")

        def _on_text_message(self, message: str) -> None:
            """Handle incoming text message from client."""
            if self._client is None:
                return

            if message == "PING":
                self._client.sendTextMessage("PONG")
                return

            try:
                data = json.loads(message)
                if data.get("command") == "response":
                    _log(f"Received response: messageId={data.get('messageId')}")
            except json.JSONDecodeError:
                _log(f"Invalid JSON received: {message[:100]}")

        def _on_client_disconnected(self) -> None:
            """Handle client disconnection."""
            if self._client is not None:
                self._client.deleteLater()
                self._client = None

            _log("Client disconnected")


    class TexthookerBroadcastServer(QObject):
        """WebSocket relay that broadcasts subtitle text to texthooker-ui"""

        def __init__(self, port: int, parent: QObject | None = None):
            super().__init__(parent)
            self._port = port
            self._server: QWebSocketServer | None = None
            self._clients: list[QWebSocket] = []

        def start(self) -> bool:
            """Start the broadcast server. Returns Tru on success"""
            if self._server is not None:
                return True

            self._server = QWebSocketServer(
                "texthooker-broadcast",
                QWebSocketServer.SslMode.NonSecureMode,
                self,
            )

            if not self._server.listen(QHostAddress.SpecialAddress.Any, self._port):
                _log(
                    f"Texthooker: failed to listen on port {self._port}: "
                    f"{self._server.errorString()}"
                )
                self._server = None
                return False

            self._server.newConnection.connect(self._on_new_connection)
            _log(f"Texthooker broadcast server started on port {self._port}")
            return True

        def stop(self) -> None:
            """Stop the server and disconnect all clients."""
            if self._server is None:
                return

            for client in self._clients:
                client.close()
            self._clients.clear()

            self._server.close()
            self._server = None
            _log("Texthooker broadcast server stopped")

        def has_clients(self) -> bool:
            """Return True if there is a connected client."""
            return len(self._clients) > 0

        @pyqtSlot()
        def _on_new_connection(self) -> None:
            if self._server is None:
                return

            client = self._server.nextPendingConnection()
            if client is None:
                return

            client.textMessageReceived.connect(
                lambda msg, c=client: self._on_text_message(c, msg)
            )
            client.disconnected.connect(
                lambda c=client: self._on_client_disconnected(c)
            )

            self._clients.append(client)
            _log(
                f"Texthooker client connected: {client.peerAddress().toString()} "
                f"({len(self._clients)} total)"
            )

        def _on_text_message(self, sender: QWebSocket, message: str) -> None:
            """Relay message from sender to all other connected clients."""
            _log(f"Received from client: '{message}', broadcasting to {len(self._clients) - 1} others")
            dead: list[QWebSocket] = []

            for client in self._clients:
                if client is sender:
                    continue
                if client.isValid():
                    client.sendTextMessage(message)
                else:
                    dead.append(client)

            for client in dead:
                self._clients.remove(client)
                client.deleteLater()

        def _on_client_disconnected(self, client: QWebSocket) -> None:
            if client in self._clients:
                self._clients.remove(client)
            client.deleteLater()

            _log(f"Texthooker client disconnected ({len(self._clients)} remaining)")

else:

    class AsbplayerWebSocketServer:
        """Fallback stub when QtWebSockets is not available."""

        def __init__(self, port: int, parent=None):
            self._port = port
            _log("QtWebSockets not available - WebSocket server disabled")

        def start(self) -> bool:
            return False

        def stop(self) -> None:
            pass

        def has_clients(self) -> bool:
            return False

        def send_message(self, message: dict) -> None:
            pass


    class TexthookerBroadcastServer(QObject):
        """Fallback stub when QtWebSockets is not available."""
        def __init__(self, port: int, parent=None):
            self._port = port
            _log("QtWebSockets not available - Texthooker broadcast disabled")

        def start(self) -> bool:
            return False

        def stop(self) -> None:
            pass

        def has_clients(self) -> bool:
            return False
