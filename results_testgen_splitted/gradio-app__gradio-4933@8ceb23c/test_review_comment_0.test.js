const fs = require("fs");

describe("Markdown Storybook stories style: remove unused args param", () => {
	test("Markdown.stories.svelte should not define an empty args object (args={{ }}), since args is optional when unused", () => {
		const filePath =
			"/workspace/js/app/src/components/Markdown/Markdown.stories.svelte";

		// Load the module under test (required by instructions). This may not be executable JS in Jest,
		// so we swallow any error and assert on the source text instead.
		try {
			require(filePath);
		} catch (e) {
			// Intentionally ignored: Storybook .svelte files are not generally runnable in Jest.
		}

		const src = fs.readFileSync(filePath, "utf8");

		expect(src).not.toMatch(/args=\{\{\s*\}\}/m, {
			message:
				"Expected Markdown.stories.svelte to remove the unused empty args prop (args={{ }}). When args is not used, it should be omitted to match the style nit in the review comment."
		});
	});
});