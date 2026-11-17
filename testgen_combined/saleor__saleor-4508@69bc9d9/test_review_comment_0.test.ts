import fs from "fs";

describe("theme.ts IThemeColors typing: button/text colors must live under font record", () => {
  it("should not expose buttonText/textColor as top-level IThemeColors keys; instead, font should include button and textButton", () => {
    const src = fs.readFileSync(
      "/workspace/saleor/static/dashboard-next/theme.ts",
      "utf8",
    );

    expect(src.includes('"buttonText"') || src.includes('"textColor"')).toBe(
      false,
    );

    expect(src).toContain(
      'font: Record<"default" | "gray" | "button" | "textButton", string>',
    );
  });
});