export class Content {
  constructor() {
    this.type = null;
    this.data = null;
  }
}

export class Message {
  constructor(id, requestId, content) {
    this.id = id || Math.random().toString(36).substring(2);
    this.requestId = requestId;
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

  // Clone the message retaining the instance type
  clone() {
    const oldTimestamp = this.timestamp;
    const newMessage = new this.constructor(this.id, this.content);
    newMessage.timestamp = oldTimestamp;
    newMessage.requestId = this.requestId;

    return newMessage;
  }
}

export class UserMessage extends Message {
  constructor(id, requestId, content) {
    super(id, requestId, content);
    this.type = "user";
  }
}

export class AppMessage extends Message {
  constructor(id, requestId, content, replyTo) {
    super(id, requestId, content);
    this.type = "app";
    this.replyTo = replyTo;
  }
}

export class AppErrorMessage extends Message {
  constructor(id, requestId, content, replyTo) {
    super(id, requestId, content);
    this.type = "error";
    this.replyTo = replyTo;
  }
}

export class AgentMessage extends AppMessage {
  constructor(id, requestId, content, replyTo) {
    super(id, requestId, content, replyTo);
    this.subType = "agent";
  }
}

export class AgentStepMessage extends AppMessage {
  constructor(id, requestId, content, replyTo, isRunning = true) {
    super(id, requestId, content, replyTo);
    this.subType = "agent-step";
    this.isRunning = isRunning;
  }
}

export class AgentStepErrorMessage extends AppMessage {
  constructor(id, requestId, content, replyTo) {
    super(id, requestId, content, replyTo);
    this.subType = "agent-step-error";
  }
}

export class Messages {
  constructor() {
    this.messages = {}; // Dictionary of message id to message
  }

  add(message) {
    if (message.id) {
      if (this.messages.hasOwnProperty(message.id)) {
        let updatedMessage = this.messages[message.id].clone();
        updatedMessage.content = message.content;
        updatedMessage.hash = message.hash;

        if (message.hasOwnProperty("isRunning")) {
          updatedMessage.isRunning = message.isRunning;
        }

        this.messages[message.id] = updatedMessage;
      } else {
        this.messages[message.id] = message;
      }
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

  getContent(id) {
    return this.messages[id]?.content;
  }
}
