const fs = require('fs');

describe('getGuidesContent: explain_new_default_event_issue_detail threshold', () => {
  test('dateThreshold is set to 2023-08-22 in getGuidesContent definition', () => {
    const source = fs.readFileSync(
      '/workspace/static/app/components/assistant/getGuidesContent.tsx',
      'utf8'
    );

    const idx = source.indexOf("guide: 'explain_new_default_event_issue_detail'");
    expect(idx).toBeGreaterThanOrEqual(
      0,
      "Expected guide 'explain_new_default_event_issue_detail' to exist in /workspace/static/app/components/assistant/getGuidesContent.tsx"
    );

    const window = source.slice(idx, idx + 500);

    expect(window).toContain(
      "dateThreshold: new Date('2023-08-22')",
      "Expected 'explain_new_default_event_issue_detail' to use dateThreshold new Date('2023-08-22')"
    );

    expect(window).not.toContain(
      "dateThreshold: new Date('2023-07-05')",
      "Did not expect 'explain_new_default_event_issue_detail' to still use the old dateThreshold new Date('2023-07-05')"
    );
  });
});