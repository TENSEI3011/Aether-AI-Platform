/**
 * Frontend Utility Helpers
 */

/**
 * Format a date string to a readable format
 */
export function formatDate(dateStr) {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    })
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text, maxLength = 100) {
    if (!text) return ''
    return text.length > maxLength ? text.slice(0, maxLength) + '...' : text
}
