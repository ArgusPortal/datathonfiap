/**
 * ExportChartButton.tsx — Export de gráficos Nivo como PNG
 *
 * Botão reutilizável que captura o conteúdo SVG de um container
 * e exporta como imagem PNG. Compatível com qualquer chart Nivo.
 *
 * Uso: envolva o chart num <div ref={chartRef}> e passe a ref.
 */
import { useCallback, type RefObject } from 'react'
import { Download } from 'lucide-react'
import { Button } from '@/components/ui'

interface ExportChartButtonProps {
  /** Ref para o container DOM do chart */
  chartRef: RefObject<HTMLDivElement | null>
  /** Nome do arquivo exportado (sem extensão) */
  filename?: string
  /** Label do botão */
  label?: string
  /** Tamanho do botão */
  size?: 'sm' | 'default' | 'icon'
}

export function ExportChartButton({
  chartRef,
  filename = 'grafico-passos-magicos',
  label = 'PNG',
  size = 'sm',
}: ExportChartButtonProps) {
  const handleExport = useCallback(() => {
    const container = chartRef.current
    if (!container) return

    const svg = container.querySelector('svg')
    if (!svg) return

    // Clone the SVG to ensure we get the full rendering
    const clone = svg.cloneNode(true) as SVGSVGElement
    const { width, height } = svg.getBoundingClientRect()

    // Set explicit dimensions
    clone.setAttribute('width', String(width))
    clone.setAttribute('height', String(height))

    // Serialize to string
    const serializer = new XMLSerializer()
    const svgString = serializer.serializeToString(clone)
    const svgBlob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' })
    const url = URL.createObjectURL(svgBlob)

    // Create canvas and render
    const img = new Image()
    img.onload = () => {
      const scale = 2 // Retina quality
      const canvas = document.createElement('canvas')
      canvas.width = width * scale
      canvas.height = height * scale
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      // White background
      ctx.fillStyle = '#ffffff'
      ctx.fillRect(0, 0, canvas.width, canvas.height)
      ctx.scale(scale, scale)
      ctx.drawImage(img, 0, 0)

      // Download
      const a = document.createElement('a')
      a.download = `${filename}_${new Date().toISOString().slice(0, 10)}.png`
      a.href = canvas.toDataURL('image/png')
      a.click()

      URL.revokeObjectURL(url)
    }
    img.src = url
  }, [chartRef, filename])

  return (
    <Button
      variant="outline"
      size={size}
      onClick={handleExport}
      title="Exportar gráfico como PNG"
      className="gap-1.5"
    >
      <Download className="h-3 w-3" />
      {size !== 'icon' && label}
    </Button>
  )
}
