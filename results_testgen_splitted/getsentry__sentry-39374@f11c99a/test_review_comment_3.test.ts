/**
 * @jest-environment node
 */

import fs from 'fs';

describe('groupReplays.spec.tsx review: make error count assertion more specific', () => {
  it('uses replay-table-count-errors testid assertions instead of generic getByText("1"/"4")', () => {
    const specPath =
      '/workspace/static/app/views/organizationGroupDetails/groupReplays/groupReplays.spec.tsx';
    const contents = fs.readFileSync(specPath, 'utf8');

    // Match the "after" version: specific assertions using a stable testid
    expect(contents).toContain("getAllByTestId('replay-table-count-errors')[0]");
    expect(contents).toContain("toHaveTextContent('1')");
    expect(contents).toContain("getAllByTestId('replay-table-count-errors')[1]");
    expect(contents).toContain("toHaveTextContent('4')");

    // Ensure the previous, overly-generic assertions are not present anymore
    expect(contents).not.toContain("getByText('1')");
    expect(contents).not.toContain("getByText('4')");
  });
});