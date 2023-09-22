// A simple wrapper over websockets

export class Ws {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.onMessage = null;
    this.queue = []; // Queue to hold until messages are ready
  }

  status() {
    return this.ws.readyState;
  }

  connect() {
    this.ws = new WebSocket(this.url);
    this.ws.onmessage = this.onMessage;
    this.ws.onopen = () => {
      // Send all the queued messages
      this.queue.forEach((msg) => {
        this.ws.send(msg);
      });
      this.queue = [];
    };
    this.ws.onclose = () => {
      console.log("Websocket closed");
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
    this.ws.close();
  }

  setOnMessage(onMessage) {
    this.onMessage = onMessage;
  }
}
