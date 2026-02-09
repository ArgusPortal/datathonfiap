import { useEffect } from 'react'

interface ShortcutConfig {
  key: string
  ctrl?: boolean
  shift?: boolean
  alt?: boolean
  handler: () => void
  description: string
}

/**
 * Global keyboard shortcuts hook.
 * Registers shortcuts and cleans up on unmount.
 */
export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const target = e.target as HTMLElement
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable
      ) {
        return
      }

      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? (e.ctrlKey || e.metaKey) : !(e.ctrlKey || e.metaKey)
        const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey
        const altMatch = shortcut.alt ? e.altKey : !e.altKey
        const keyMatch = e.key.toLowerCase() === shortcut.key.toLowerCase()

        if (ctrlMatch && shiftMatch && altMatch && keyMatch) {
          e.preventDefault()
          shortcut.handler()
          return
        }
      }
    }

    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [shortcuts])
}

/**
 * Get all registered shortcuts for display in a help modal.
 */
export const GLOBAL_SHORTCUTS: { key: string; label: string; description: string }[] = [
  { key: 'G D', label: 'g → d', description: 'Ir para Dashboard' },
  { key: 'G P', label: 'g → p', description: 'Ir para Predição' },
  { key: 'G S', label: 'g → s', description: 'Ir para Alunos' },
  { key: 'G M', label: 'g → m', description: 'Ir para Monitoramento' },
  { key: 'G I', label: 'g → i', description: 'Ir para Modelo' },
  { key: '?', label: '?', description: 'Mostrar atalhos' },
]
