import fs from 'fs'

test('DashboardItem deleteWithUndo should include both id and name in object payload', () => {
    // Ensure module can be loaded (requirement: load module under test)
    expect(() => require('/workspace/frontend/src/scenes/dashboard/DashboardItem.tsx')).not.toThrow()

    const source = fs.readFileSync('/workspace/frontend/src/scenes/dashboard/DashboardItem.tsx', 'utf8')

    expect(source).toContain("data-attr={'dashboard-item-' + index + '-dropdown-delete'}")

    // Robustly assert that in the delete menu item's onClick handler, deleteWithUndo is called with object containing id and name.
    // This should FAIL on "before" (missing name) and PASS on "after".
    const deleteMenuItemIndex = source.indexOf("data-attr={'dashboard-item-' + index + '-dropdown-delete'}")
    expect(deleteMenuItemIndex).toBeGreaterThan(
        -1,
        'Could not find the delete dropdown menu item in DashboardItem.tsx'
    )

    const window = source.slice(deleteMenuItemIndex, deleteMenuItemIndex + 1200) // enough to include the handler body

    expect(window).toMatch(/deleteWithUndo\(\s*{\s*/m)
    expect(window).toMatch(/object:\s*{\s*[\s\S]*?\bid:\s*item\.id\b/m)
    expect(window).toMatch(
        /\bname:\s*item\.name\b/m,
        'Expected deleteWithUndo payload to include `name: item.name` for undo messaging'
    )
})