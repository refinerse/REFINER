const fs = require("fs");

describe("AuthenticatorEmailStage null-safe email rendering", () => {
    test("renderEmailOTPInput() guards challenge.email with ifDefined()", () => {
        const source = fs.readFileSync(
            "/workspace/web/src/flow/stages/authenticator_email/AuthenticatorEmailStage.ts",
            "utf8",
        );

        expect(source).toContain(
            "${ifDefined(this.challenge.email)}",
            "Expected renderEmailOTPInput() to render email using ${ifDefined(this.challenge.email)} to avoid rendering null/undefined from the API.",
        );
    });
});