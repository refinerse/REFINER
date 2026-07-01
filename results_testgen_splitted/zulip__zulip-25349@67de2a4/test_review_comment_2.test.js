const fs = require("fs");

describe("scheduled_messages_overlay_ui uses data-scheduled-message-id (not data-message-id)", () => {
    test("code reads from data-scheduled-message-id and no longer uses data-message-id", () => {
        const code = fs.readFileSync(
            "/workspace/web/src/scheduled_messages_overlay_ui.js",
            "utf8",
        );

        expect(code.includes("data-scheduled-message-id")).toBe(
            true,
            "Expected scheduled_messages_overlay_ui.js to use the attribute name 'data-scheduled-message-id' to avoid confusion with real message IDs.",
        );

        expect(code.includes("data-message-id")).toBe(
            false,
            "Expected scheduled_messages_overlay_ui.js to not use 'data-message-id' for scheduled messages.",
        );
    });
});