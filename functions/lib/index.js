"use strict";
/**
 * JVC IT Support LINE Bot - Cloud Functions
 *
 * Main entry point for all Cloud Functions
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.processMessage = exports.lineWebhook = void 0;
// LINE Webhook Handler
var webhook_1 = require("./line/webhook");
Object.defineProperty(exports, "lineWebhook", { enumerable: true, get: function () { return webhook_1.lineWebhook; } });
// Support Processing Functions
var processor_1 = require("./support/processor");
Object.defineProperty(exports, "processMessage", { enumerable: true, get: function () { return processor_1.processMessage; } });
//# sourceMappingURL=index.js.map