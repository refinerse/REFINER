const fs = require("fs");

describe("AuthenticatorValidateStageWebCode icons are refined/consistent", () => {
    test("deviceIcon mappings for Email/SMS/TOTP/Static use the refined FontAwesome classes", () => {
        const src = fs.readFileSync(
            "/workspace/web/src/flow/stages/authenticator_validate/AuthenticatorValidateStageCode.ts",
            "utf8",
        );

        expect(src).toContain(
            'case DeviceClassesEnum.Email:\n                return "fa-envelope-o";',
        );
        expect(src).toContain(
            'case DeviceClassesEnum.Sms:\n                return "fa-mobile-alt";',
        );
        expect(src).toContain('case DeviceClassesEnum.Totp:\n                return "fa-clock";');
        expect(src).toContain(
            'case DeviceClassesEnum.Static:\n                return "fa-key";',
        );
    });
});