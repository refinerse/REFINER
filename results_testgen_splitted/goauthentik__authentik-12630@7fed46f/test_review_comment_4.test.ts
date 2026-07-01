const fs = require("fs");

describe("AuthenticatorEmailStageForm.ts style cleanup", () => {
    it("should not contain commented-out leftover imports in the @goauthentik/api import block", () => {
        const filePath =
            "/workspace/web/src/admin/stages/authenticator_email/AuthenticatorEmailStageForm.ts";

        const src = fs.readFileSync(filePath, "utf8");

        expect(src).not.toMatch(
            /(FlowsInstancesListRequest\s*,\s*\/\/|^\s*\/\/\s*Propertymappings|NotificationWebhookMapping)/m,
        );
    });
});