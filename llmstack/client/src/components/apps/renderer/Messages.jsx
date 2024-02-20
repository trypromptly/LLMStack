export class Content {
  constructor() {
    this.type = null;
    this.data = null;
  }
}

export class Message {
  constructor(id, content) {
    this.id = id || Math.random().toString(36).substring(2);
    this.type = null;
    this.content = null;
    this.timestamp = new Date();

    if (content) {
      this.content = content;
    }
  }
}

export class UserMessage extends Message {
  constructor(id, content) {
    super(id, content);
    this.type = "user";
  }
}

export class AppMessage extends Message {
  constructor(id, content, replyTo) {
    super(id, content);
    this.type = "app";
    this.replyTo = replyTo;
  }
}

export class Messages {
  constructor() {
    this.messages = {}; // Dictionary of message id to message
  }

  add(message) {
    if (message.id) {
      if (this.messages.hasOwnProperty(message.id)) {
        // If the message already exists, update the content
        this.messages[message.id].content = message.content;
      }

      this.messages[message.id] = message;
    }
  }

  // Returns a list of messages sorted by timestamp
  get(reverse = false) {
    return Object.values(this.messages).sort((a, b) => {
      if (reverse) {
        return b.timestamp - a.timestamp;
      }
      return a.timestamp - b.timestamp;
    });
  }

  clear() {
    this.messages = {};
  }
}
