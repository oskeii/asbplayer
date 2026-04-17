export class TexthookerClient {
    private _socket?: WebSocket;
    private _url: string;
    private _reconnectInterval?: ReturnType<typeof setInterval>;

    async connect(url: string) {
        this._url = url;
        this.disconnect();

        this._reconnectInterval = setInterval(() => {
            if(!this._socket || this._socket.readyState === WebSocket.CLOSED) {
                this._tryConnect();
            }
        }, 5000);

        await this._tryConnect();
    }

    private _tryConnect(): Promise<void> {
        if (!this._url) return Promise.resolve();

        return new Promise((resolve) => {
            const socket = new WebSocket(this._url!);
            socket.onopen = () => {
                console.log('[texthooker] Connected!');
                this._socket = socket;
                resolve();
            };
            socket.onerror = (e) => {
                console.log('[texthooker] connection error:', e);
                resolve();
            };
            socket.onclose = () => {
                console.log('[texthooker] disconnected');
                if (this._socket === socket) {
                    this._socket = undefined;
                }
            };
            // Ignore incoming messages; this client only acts as sender
            socket.onmessage = () => {};
        });
    }

    sendSubtitle(text: string) {
        if (this._socket?.readyState === WebSocket.OPEN) {
            this._socket.send(text);
        }
    }

    disconnect() {
        if (this._reconnectInterval !== undefined) {
            clearInterval(this._reconnectInterval);
            this._reconnectInterval = undefined;
        }

        if (this._socket) {
            this._socket.close();
            this._socket = undefined;
        }
    }
}