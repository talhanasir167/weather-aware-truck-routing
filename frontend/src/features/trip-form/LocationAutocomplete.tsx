import { useEffect, useState } from 'react'
import { geocode } from '../../api/client'
import type { GeocodeResult } from '../../api/types'

interface Props {
  label: string
  value: string
  onChange: (label: string, lat?: number, lon?: number) => void
  placeholder?: string
}

export function LocationAutocomplete({ label, value, onChange, placeholder }: Props) {
  const [results, setResults] = useState<GeocodeResult[]>([])
  const [open, setOpen] = useState(false)

  useEffect(() => {
    if (value.length < 3 && !value.includes(',')) {
      setResults([])
      return
    }
    const handle = setTimeout(() => {
      geocode(value)
        .then((r) => setResults(r.results))
        .catch(() => setResults([]))
    }, 350)
    return () => clearTimeout(handle)
  }, [value])

  return (
    <label className="field">
      <span>{label}</span>
      <input
        value={value}
        placeholder={placeholder}
        onChange={(e) => {
          onChange(e.target.value)
          setOpen(true)
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        autoComplete="off"
      />
      {open && results.length > 0 && (
        <ul className="autocomplete">
          {results.map((r) => (
            <li key={`${r.lat}-${r.lon}-${r.label}`}>
              <button
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  onChange(r.label, r.lat, r.lon)
                  setOpen(false)
                }}
              >
                {r.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  )
}
