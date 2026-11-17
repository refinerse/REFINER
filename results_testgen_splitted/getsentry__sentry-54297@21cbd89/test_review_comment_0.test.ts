import fs from 'fs';

describe('groupEventCarousel - GuideAnchor placement', () => {
  it('places the GuideAnchor inside EventNavigationDropdown (so it is feature-gated) and not in GroupEventCarousel', () => {
    const source = fs.readFileSync(
      '/workspace/static/app/views/issueDetails/groupEventCarousel.tsx',
      'utf8'
    );

    const dropdownFnStart = source.indexOf('function EventNavigationDropdown');
    expect(dropdownFnStart).toBeGreaterThan(
      -1,
      'Expected to find function EventNavigationDropdown in /workspace/static/app/views/issueDetails/groupEventCarousel.tsx'
    );

    const carouselFnStart = source.indexOf('export function GroupEventCarousel');
    expect(carouselFnStart).toBeGreaterThan(
      -1,
      'Expected to find export function GroupEventCarousel in /workspace/static/app/views/issueDetails/groupEventCarousel.tsx'
    );

    const dropdownBody = source.slice(dropdownFnStart, carouselFnStart);
    const carouselBody = source.slice(carouselFnStart);

    expect(dropdownBody).toContain(
      '<GuideAnchor target="issue_details_default_event" position="bottom">',
      'Expected GuideAnchor to be rendered inside EventNavigationDropdown so it only renders when the feature is enabled.'
    );

    expect(carouselBody).not.toContain(
      '<GuideAnchor target="issue_details_default_event" position="bottom">',
      'Did not expect GroupEventCarousel to render this GuideAnchor directly; it should be inside EventNavigationDropdown to ensure feature-gating.'
    );
  });
});