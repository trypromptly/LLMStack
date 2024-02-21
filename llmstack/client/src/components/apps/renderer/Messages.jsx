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
    this.hash = null;

    if (content) {
      this.content = content;
    }

    if (this.content && !this.hash) {
      this.hash = this._buildHash();
    }
  }

  _buildHash() {
    const stringified = JSON.stringify(
      this.content,
      Object.keys(this.content).sort(),
    );
    let hash = 0;
    for (let i = 0; i < stringified.length; i++) {
      const char = stringified.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return hash.toString();
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

        // Update the hash
        this.messages[message.id].hash = this.messages[message.id]._buildHash();
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
