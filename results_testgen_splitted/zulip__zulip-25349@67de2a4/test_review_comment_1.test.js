const fs = require("fs");

test("scheduled_messages.send_request_to_schedule_message defines success callback that accepts response data (fix typo/bug)", () => {
    const source = fs.readFileSync("/workspace/web/src/scheduled_messages.js", "utf8");

    // The review comment indicates the success callback previously had a typo/bug.
    // In the fixed version, success must accept `data` so it can use the server
    // response (e.g., `data.scheduled_message_id`) to render the banner row.
    expect(source).toMatch(
        /send_request_to_schedule_message\s*\([^)]*\)\s*\{\s*const\s+success\s*=\s*function\s*\(\s*data\s*\)/s,
    );
});