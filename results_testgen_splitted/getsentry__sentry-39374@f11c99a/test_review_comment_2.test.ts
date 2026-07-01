/**
 * @jest-environment node
 */
import fs from 'fs';

describe('Code review: prefer descriptive test name over comment', () => {
  it('uses the descriptive test name "should query the events endpoint with the passed in replayIds" (and not the old generic name)', () => {
    const filePath =
      '/workspace/static/app/views/organizationGroupDetails/groupReplays/groupReplays.spec.tsx';
    const source = fs.readFileSync(filePath, 'utf8');

    expect(source).toContain(
      "it('should query the events endpoint with the passed in replayIds'"
    );

    expect(source).not.toContain("it('Should have correct queries in the events endpoint'");
  });
});