const fs = require("fs");

describe("scheduled_messages: scheduled_messages_data sorting behavior", () => {
    test("module implements unconditional sorting via sort_scheduled_messages_data()", () => {
        const code = fs.readFileSync("/workspace/web/src/scheduled_messages.js", "utf8");

        // The review comment asked to sort unconditionally; the "after" code introduces a dedicated
        // helper that always sorts after modifications.
        expect(code).toContain(
            "function sort_scheduled_messages_data()",
            "Expected scheduled_messages.js to define sort_scheduled_messages_data() to support unconditional sorting after updates/additions.",
        );

        expect(code).toContain(
            "sort_scheduled_messages_data();",
            "Expected scheduled_messages.js to call sort_scheduled_messages_data() (unconditionally sorting) after changing scheduled_messages_data.",
        );
    });
});