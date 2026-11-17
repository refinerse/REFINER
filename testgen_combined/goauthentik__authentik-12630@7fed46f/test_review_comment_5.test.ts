const fs = require("fs");

describe("AuthenticatorValidateStage Email device picker icon", () => {
    test("uses an envelope icon for Email device class (icon refined)", () => {
        const source = fs.readFileSync(
            "/workspace/web/src/flow/stages/authenticator_validate/AuthenticatorValidateStage.ts",
            "utf8",
        );

        // Sanity check: ensure the Email case exists in the switch so we're checking the right block.
        expect(source).toContain(
            "case DeviceClassesEnum.Email:",
        );

        // Key behavior: Email device should render an envelope icon.
        expect(source).toContain(
            '<i class="fas fa-envelope-o"></i>',
        );

        // Ensure the old (incorrect) mobile icon isn't used for Email.
        expect(source).not.toContain(
            'case DeviceClassesEnum.Email:\n                return html`<i class="fas fa-mobile-alt"></i>',
        );
    });
});