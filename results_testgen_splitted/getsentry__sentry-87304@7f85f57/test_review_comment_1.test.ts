import fs from 'fs';

describe('ProductSelection docs links should point to general product docs (not platform-specific)', () => {
  const filePath = '/workspace/static/app/components/onboarding/productSelection.tsx';

  it('uses general product/concepts docs links for Tracing/Profiling/Session Replay', () => {
    const src = fs.readFileSync(filePath, 'utf8');

    expect(
      src.includes('docLink="https://docs.sentry.io/concepts/key-terms/tracing/"')
    ).toBe(
      true,
      'Expected Tracing docLink to point to general docs: https://docs.sentry.io/concepts/key-terms/tracing/'
    );

    expect(
      src.includes(
        'docLink="https://docs.sentry.io/product/explore/profiling/getting-started/#continuous-profiling"'
      )
    ).toBe(
      true,
      'Expected Profiling docLink to point to general product docs: https://docs.sentry.io/product/explore/profiling/getting-started/#continuous-profiling'
    );

    expect(
      src.includes('docLink="https://docs.sentry.io/product/explore/session-replay/"')
    ).toBe(
      true,
      'Expected Session Replay docLink to point to general product docs: https://docs.sentry.io/product/explore/session-replay/'
    );

    // Ensure the old platform-specific links are not present anymore
    expect(
      src.includes('docLink="https://docs.sentry.io/platforms/javascript/guides/react/tracing/"')
    ).toBe(
      false,
      'Did not expect Tracing docLink to remain platform-specific (react tracing guide).'
    );

    expect(
      src.includes('docLink="https://docs.sentry.io/platforms/python/profiling/"')
    ).toBe(
      false,
      'Did not expect Profiling docLink to remain platform-specific (python profiling docs).'
    );

    expect(
      src.includes(
        'docLink="https://docs.sentry.io/platforms/javascript/guides/react/session-replay/"'
      )
    ).toBe(
      false,
      'Did not expect Session Replay docLink to remain platform-specific (react session replay guide).'
    );
  });
});