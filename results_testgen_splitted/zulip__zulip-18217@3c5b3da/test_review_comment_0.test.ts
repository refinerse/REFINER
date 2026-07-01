import fs from "fs";

describe("message_edit structural change: add unread-messages confirmation flow", () => {
    test("edit_last_sent_message should include warn_user_about_unread_msgs confirmation helper", () => {
        const code = fs.readFileSync("/workspace/web/src/message_edit.ts", "utf8");

        expect(code).toContain("export function edit_last_sent_message");

        expect(code).toContain(
            "function warn_user_about_unread_msgs",
        );

        expect(code).toContain(
            "warn_user_about_unread_msgs(",
        );
    });
});