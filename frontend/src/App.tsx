import { useState } from 'react'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

type EstadoBackend = 'sin verificar' | 'verificando...' | 'ok' | 'sin conexión'

function App() {
  const [estado, setEstado] = useState<EstadoBackend>('sin verificar')

  async function verificarBackend() {
    setEstado('verificando...')
    try {
      const res = await fetch(`${API_URL}/health`)
      const body = await res.json()
      setEstado(body.status === 'ok' ? 'ok' : 'sin conexión')
    } catch {
      setEstado('sin conexión')
    }
  }

  return (
    <main className="contenedor">
      <h1>Detector Híbrido de Estafas</h1>
      <p>
        Análisis automatizado de publicaciones de venta en marketplaces P2P mediante una
        arquitectura en cascada: heurísticas, machine learning local e IA multimodal.
      </p>
      <p className="fase">Fase 0 — esqueleto del proyecto</p>
      <button onClick={verificarBackend}>Verificar backend</button>
      <p>
        Estado del backend: <span data-estado={estado}>{estado}</span>
      </p>
    </main>
  )
}

export default App
