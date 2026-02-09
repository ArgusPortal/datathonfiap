/**
 * CounterUp.tsx — Animação de contagem numérica progressiva
 *
 * Inspirado nos "Impact Cards" do site passosmagicos.org.br que exibem
 * números grandes como "1.250 crianças" e "120 universitários".
 *
 * Utiliza a lib react-countup que opera via requestAnimationFrame,
 * garantindo 60fps mesmo em hardware modesto.
 *
 * Props:
 *  - end: valor final do contador
 *  - duration: duração da animação em segundos (padrão: 2)
 *  - prefix/suffix: texto antes/depois do número (ex: "R$" ou "%")
 *  - decimals: casas decimais (padrão: 0)
 */
import CountUp from 'react-countup'

interface CounterUpProps {
  end: number
  duration?: number
  prefix?: string
  suffix?: string
  decimals?: number
  className?: string
  separator?: string
}

export function CounterUpNumber({
  end,
  duration = 2,
  prefix = '',
  suffix = '',
  decimals = 0,
  className = '',
  separator = '.',
}: CounterUpProps) {
  return (
    <CountUp
      end={end}
      duration={duration}
      prefix={prefix}
      suffix={suffix}
      decimals={decimals}
      separator={separator}
      decimal=","
      enableScrollSpy
      scrollSpyOnce
    >
      {({ countUpRef }) => (
        <span ref={countUpRef} className={className} />
      )}
    </CountUp>
  )
}
