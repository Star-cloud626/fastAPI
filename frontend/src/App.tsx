import { useMemo, useState, type FormEvent } from 'react'
import './App.css'

type ValidationError = {
  row_index: number | null
  id: string | number | null
  column: string
  error_message: string
}

type ValidationResponse = {
  status: 'pass' | 'fail'
  errors: ValidationError[]
}

const defaultApiBase = 'http://localhost:8000'

function App() {
  const apiBaseUrl = useMemo(
    () => import.meta.env.VITE_API_BASE_URL || defaultApiBase,
    [],
  )
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [networkError, setNetworkError] = useState<string | null>(null)
  const [result, setResult] = useState<ValidationResponse | null>(null)

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setNetworkError(null)
    setResult(null)

    if (!file) {
      setNetworkError('Please choose a CSV file to validate.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setLoading(true)
    try {
      const response = await fetch(`${apiBaseUrl}/validate`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || 'Unexpected API error')
      }

      const payload: ValidationResponse = await response.json()
      setResult(payload)
    } catch (error) {
      setNetworkError(
        error instanceof Error
          ? `Request failed: ${error.message}`
          : 'Unable to reach the validation service.',
      )
    } finally {
      setLoading(false)
    }
  }

  const hasErrors = result?.status === 'fail' && result.errors.length > 0

  return (
    <div className="page">
      <header className="header">
        <div>
          <p className="eyebrow">Xovate Technical Task</p>
          <h1>CSV Data Validator</h1>
          <p className="subtitle">
            Upload a CSV file to validate required fields, email completeness,
            and age formatting/range rules.
          </p>
        </div>
        <div className="env">
          <span className="label">API Base:</span>
          <code>{apiBaseUrl}</code>
        </div>
      </header>

      <section className="card">
        <form onSubmit={handleSubmit} className="form">
          <div className="input-row">
            <label htmlFor="file">CSV file</label>
            <input
              id="file"
              name="file"
              type="file"
              accept=".csv,text/csv"   //only can see csv files
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <div className="actions">
            <button type="submit" disabled={loading}>
              {loading ? 'Validating…' : 'Validate'}
            </button>
          </div>
        </form>
        <div className="note">
          Use the sample files in the <code>data</code> folder
        </div>
      </section>

      {networkError && <div className="banner error">{networkError}</div>}

      {result?.status === 'pass' && (
        <div className="banner success">
          Validation Successful: Data is clean.
        </div>
      )}

      {hasErrors && (
        <section className="card">
          <div className="table-header">
            <h2>Validation Errors</h2>
            <p>{result?.errors.length} issue(s) found</p>
          </div>
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Row Number</th>
                  <th>Column</th>
                  <th>Error Description</th>
                </tr>
              </thead>
              <tbody>
                {result?.errors.map((error, idx) => (
                  <tr key={`${error.row_index}-${error.column}-${idx}`}>
                    <td>{error.id ?? '—'}</td>
                    <td>{error.row_index ?? '—'}</td>
                    <td>{error.column}</td>
                    <td>{error.error_message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  )
}

export default App
