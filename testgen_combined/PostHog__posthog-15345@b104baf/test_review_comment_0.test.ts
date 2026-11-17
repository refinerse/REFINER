import fs from 'fs'

describe('PlayerMetaLinks documentation cleanup (no unfinished commented-out code)', () => {
    test('should not contain the unfinished commented-out JSX block starting with "// return ("', () => {
        const filePath = '/workspace/frontend/src/scenes/session-recordings/player/PlayerMetaLinks.tsx'
        const source = fs.readFileSync(filePath, 'utf8')

        expect(source.includes('// return (')).toBe(
            false
        )
    })
})

export {}