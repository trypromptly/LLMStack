// A simple wrapper over websockets

export class Ws {
  constructor(url, binaryType = null) {
    this.url = url;
    this.ws = null;
    this.binaryType = binaryType;
    this.onMessage = null;
    this.onClose = null;
    this.queue = []; // Queue to hold until messages are ready
  }

  status() {
    return this.ws.readyState;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    if (this.binaryType) {
      this.ws.binaryType = this.binaryType;
    }

    this.ws.onmessage = this.onMessage;
    this.ws.onopen = () => {
      // Send all the queued messages
      this.queue.forEach((msg) => {
        this.ws.send(msg);
      });
      this.queue = [];

      console.log(`Websocket connected: ${this.url}`);
    };
    this.ws.onclose = () => {
      console.log(`Websocket closed: ${this.url}`);
      if (this.onClose) {
        this.onClose();
      }
    };
  }

  // Adds message to the queue if the socket is not ready
  send(msg) {
    if (this.ws === null) this.connect();

    if (this.ws.readyState === WebSocket.CONNECTING) {
      this.queue.push(msg);
    } else if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(msg);
    } else {
      this.queue.push(msg);
      this.connect();
    }
  }

  close() {
    this.ws?.close();
  }

  setOnMessage(onMessage) {
    this.onMessage = onMessage;
  }

  setOnClose(onClose) {
    this.onClose = onClose;
  }
}
