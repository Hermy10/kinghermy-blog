import { execSync } from 'child_process'
import { statSync } from 'fs'

export function remarkModifiedTime() {
	return function (tree, file) {
		const filepath = file.history[0]
		let lastModified

		try {
			const result = execSync(
				`git log -1 --pretty="format:%cI" "${filepath}"`,
				{ stdio: ['ignore', 'pipe', 'ignore'] }
			)
			lastModified = result.toString().trim()
		} catch (_error) {
			try {
				const stats = statSync(filepath)
				lastModified = stats.mtime.toISOString()
			} catch {
				// leave undefined if we cannot read git or file metadata
			}
		}

		if (lastModified) {
			file.data.astro.frontmatter.lastModified = lastModified
		}
	}
}
