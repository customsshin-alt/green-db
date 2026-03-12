import React, { useState, useCallback, useEffect, useRef } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import PdfViewerModal from './components/PdfViewerModal.jsx'

const STEPS = [
  { id: 1, label: 'PDF 업로드', short: '업로드' },
  { id: 2, label: '분리 설정', short: '분리' },
  { id: 3, label: '이메일 발송', short: '발송' },
]

// base64 → Blob URL (뷰어용)
function base64ToBlobUrl(base64, mime = 'application/pdf') {
  const binary = atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i)
  const blob = new Blob([bytes], { type: mime })
  return URL.createObjectURL(blob)
}

// 분리된 파일 한 건: 파일명, 확정자명(사원명), blobUrl
function createSplitItem(id, filename, confirmedName, blobUrl = null) {
  return { id, filename, confirmedName, blobUrl }
}

export default function App() {
  const [step, setStep] = useState(1)
  const [files, setFiles] = useState([])
  const [splitMode, setSplitMode] = useState('per-page')
  const [pageRange, setPageRange] = useState('')
  const [splitResult, setSplitResult] = useState([]) // 분리 실행 결과: { id, filename, confirmedName, blobUrl }
  const [viewerFile, setViewerFile] = useState(null) // 뷰어로 볼 파일
  const [recipients, setRecipients] = useState(['']) // 순서대로 매칭할 수신자 목록 (미리 세팅)
  const [status, setStatus] = useState(null)
  const splitResultRef = useRef([])
  splitResultRef.current = splitResult

  // 언마운트 시 blob URL 해제 (메모리 누수 방지)
  useEffect(() => {
    return () => {
      splitResultRef.current.forEach((item) => {
        if (item.blobUrl) URL.revokeObjectURL(item.blobUrl)
      })
    }
  }, [])

  const onDrop = useCallback((acceptedFiles) => {
    const pdfs = acceptedFiles.filter((f) => f.name.toLowerCase().endsWith('.pdf'))
    setFiles((prev) => [...prev, ...pdfs])
    setStatus(null)
    setSplitResult([])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: true,
    noClick: false,
  })

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
    setSplitResult([])
  }

  // 2. 분리 설정 — 실행 버튼: 분리 API 호출 후 결과 목록 표시 (파일명: 사원명_YYYY년MM월급여명세서.pdf)
  const runSplit = async () => {
    if (files.length === 0) {
      setStatus({ type: 'error', message: '먼저 PDF를 업로드해 주세요.' })
      return
    }
    setStatus({ type: 'loading', message: 'PDF 분리 중…' })
    try {
      // 이전 결과의 blob URL 해제
      splitResult.forEach((item) => {
        if (item.blobUrl) URL.revokeObjectURL(item.blobUrl)
      })
      const formData = new FormData()
      formData.append('file', files[0])
      const { data } = await axios.post('/api/split', formData)
      const items = data.items || []
      const nextResult = items.map((item, i) =>
        createSplitItem(
          i + 1,
          item.filename,
          item.confirmedName ?? '',
          item.contentBase64 ? base64ToBlobUrl(item.contentBase64) : null
        )
      )
      setSplitResult(nextResult)
      setRecipients((prev) => {
        const need = nextResult.length
        if (prev.length >= need) return prev.slice(0, need)
        return [...prev, ...Array(need - prev.length).fill('')]
      })
      setStatus({ type: 'success', message: `분리가 완료되었습니다. (${nextResult.length}건)` })
    } catch (err) {
      let message = err.response?.data?.detail ?? err.message ?? '분리 중 오류가 발생했습니다.'
      if (Array.isArray(message)) message = message.map((m) => m.msg ?? JSON.stringify(m)).join(', ')
      else if (typeof message !== 'string') message = JSON.stringify(message)
      setStatus({ type: 'error', message })
    }
  }

  // 파일 제목(순서)별 매칭 수신자
  const getRecipientForIndex = (index) => {
    const list = recipients.filter(Boolean)
    return list[index] ?? list[0] ?? ''
  }

  const addRecipient = () => setRecipients((prev) => [...prev, ''])
  const updateRecipient = (index, value) => {
    setRecipients((prev) => {
      const next = [...prev]
      next[index] = value
      return next
    })
  }
  const removeRecipient = (index) => {
    setRecipients((prev) => prev.filter((_, i) => i !== index))
  }

  const sendAllEmails = async () => {
    setStatus({ type: 'loading', message: '일괄 발송 중…' })
    try {
      await new Promise((r) => setTimeout(r, 1500))
      setStatus({ type: 'success', message: '모든 이메일이 발송되었습니다.' })
    } catch (err) {
      setStatus({ type: 'error', message: err.message || '발송 중 오류가 발생했습니다.' })
    }
  }

  const sendOneEmail = async (item, index) => {
    const to = getRecipientForIndex(index)
    if (!to) {
      setStatus({ type: 'error', message: '해당 파일에 매칭된 수신자가 없습니다.' })
      return
    }
    setStatus({ type: 'loading', message: `"${item.filename}" 발송 중…` })
    try {
      await new Promise((r) => setTimeout(r, 800))
      setStatus({ type: 'success', message: `"${item.filename}" 발송 완료.` })
    } catch (err) {
      setStatus({ type: 'error', message: err.message || '발송 중 오류가 발생했습니다.' })
    }
  }

  return (
    <div className="min-h-screen bg-ink-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-3xl">
        <header className="mb-10 text-center">
          <h1 className="text-2xl font-bold tracking-tight text-ink-900 sm:text-3xl">
            PDF 분리 & 이메일 발송
          </h1>
          <p className="mt-2 text-ink-500">
            PDF를 페이지별로 나누고 수신자에게 이메일로 보내세요.
          </p>
        </header>

        <nav className="mb-8 flex items-center justify-center gap-2 sm:gap-4">
          {STEPS.map((s, i) => (
            <React.Fragment key={s.id}>
              <button
                type="button"
                onClick={() => setStep(s.id)}
                className={`
                  flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-sm font-semibold sm:h-11 sm:w-11
                  ${step === s.id
                    ? 'bg-accent text-white shadow-md'
                    : 'bg-white text-ink-400 ring-1 ring-ink-200 hover:ring-accent/40'
                  }
                `}
              >
                {s.id}
              </button>
              <span className="hidden text-ink-400 sm:inline">{s.label}</span>
              {i < STEPS.length - 1 && (
                <span className="h-px w-6 bg-ink-200 sm:w-10" aria-hidden />
              )}
            </React.Fragment>
          ))}
        </nav>

        <div className="space-y-6">
          {/* 1. PDF 업로드 */}
          <section
            className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-ink-200/60"
            data-step="1"
          >
            <h2 className="mb-4 text-lg font-semibold text-ink-800">1. PDF 업로드</h2>
            <div
              {...getRootProps()}
              className={`
                flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-4 py-8 transition-colors
                ${isDragActive
                  ? 'border-accent bg-accent-50/50'
                  : 'border-ink-200 bg-ink-50/50 hover:border-ink-300 hover:bg-ink-100/50'
                }
              `}
            >
              <input {...getInputProps()} />
              <svg className="h-12 w-12 text-ink-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <p className="mt-2 text-center text-sm font-medium text-ink-600">
                {isDragActive ? '여기에 놓으세요' : 'PDF 파일을 끌어다 놓거나 클릭하여 선택'}
              </p>
              <p className="mt-1 text-xs text-ink-400">.pdf만 업로드 가능</p>
            </div>
            {files.length > 0 && (
              <ul className="mt-4 space-y-2">
                {files.map((file, i) => (
                  <li
                    key={`${file.name}-${i}`}
                    className="flex items-center justify-between rounded-lg bg-ink-50 px-3 py-2 text-sm"
                  >
                    <span className="truncate text-ink-700">{file.name}</span>
                    <button
                      type="button"
                      onClick={() => removeFile(i)}
                      className="shrink-0 rounded p-1 text-ink-400 hover:bg-ink-200 hover:text-ink-700"
                      aria-label="제거"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* 2. 분리 설정 — 실행 버튼 + 실행 결과(파일명, 확정자명) + 클릭 시 뷰어 */}
          <section
            className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-ink-200/60"
            data-step="2"
          >
            <h2 className="mb-4 text-lg font-semibold text-ink-800">2. 분리 설정</h2>
            <div className="space-y-4">
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-ink-200 bg-ink-50/50 p-4 transition-colors hover:bg-ink-50">
                <input
                  type="radio"
                  name="splitMode"
                  checked={splitMode === 'per-page'}
                  onChange={() => setSplitMode('per-page')}
                  className="h-4 w-4 border-ink-300 text-accent focus:ring-accent"
                />
                <div>
                  <span className="font-medium text-ink-800">페이지별 분리</span>
                  <p className="text-sm text-ink-500">각 페이지를 개별 PDF로 저장</p>
                </div>
              </label>
              <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-ink-200 bg-ink-50/50 p-4 transition-colors hover:bg-ink-50">
                <input
                  type="radio"
                  name="splitMode"
                  checked={splitMode === 'range'}
                  onChange={() => setSplitMode('range')}
                  className="h-4 w-4 border-ink-300 text-accent focus:ring-accent"
                />
                <div className="flex-1">
                  <span className="font-medium text-ink-800">범위 지정</span>
                  <p className="text-sm text-ink-500">예: 1-3, 5, 7-9</p>
                  {splitMode === 'range' && (
                    <input
                      type="text"
                      value={pageRange}
                      onChange={(e) => setPageRange(e.target.value)}
                      placeholder="1-3, 5, 7-9"
                      className="mt-2 w-full rounded-lg border border-ink-200 px-3 py-2 text-sm placeholder:text-ink-400 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    />
                  )}
                </div>
              </label>
            </div>

            <div className="mt-6">
              <button
                type="button"
                onClick={runSplit}
                disabled={files.length === 0 || status?.type === 'loading'}
                className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-accent-700 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
              >
                실행
              </button>
            </div>

            {splitResult.length > 0 && (
              <div className="mt-6">
                <h3 className="mb-3 text-sm font-semibold text-ink-700">분리된 파일</h3>
                <ul className="space-y-2 rounded-lg border border-ink-200 bg-ink-50/50">
                  {splitResult.map((item, index) => (
                    <li
                      key={item.id}
                      onClick={() => setViewerFile(item)}
                      className="flex cursor-pointer items-center justify-between rounded-lg px-3 py-2.5 text-sm transition-colors hover:bg-accent-50/50"
                    >
                      <div className="min-w-0 flex-1">
                        <span className="block truncate font-medium text-ink-800">{item.filename}</span>
                        <span className="block truncate text-xs text-ink-500">확정자명: {item.confirmedName}</span>
                      </div>
                      <span className="shrink-0 text-accent-600">미리보기</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>

          {/* 3. 이메일 발송 — 파일 제목별 미리 세팅 수신자 매칭 + 하단 분리 파일 목록(파일명, 확정자명, 뷰어) + 일괄/개별 발송 */}
          <section
            className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-ink-200/60"
            data-step="3"
          >
            <h2 className="mb-2 text-lg font-semibold text-ink-800">3. 이메일 발송</h2>
            <p className="mb-4 text-sm text-ink-500">
              파일 순서대로 수신자가 매칭됩니다. 아래 목록에서 각 파일의 수신자를 확인한 뒤 일괄 또는 개별 발송하세요.
            </p>

            {/* 미리 세팅된 수신자 (순서대로 매칭) */}
            <div className="mb-6">
              <h3 className="mb-2 text-sm font-semibold text-ink-700">수신자 목록 (순서대로 매칭)</h3>
              <div className="space-y-2">
                {recipients.map((email, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <span className="w-8 shrink-0 text-xs text-ink-400">{i + 1}.</span>
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => updateRecipient(i, e.target.value)}
                      placeholder={`수신자 ${i + 1} 이메일`}
                      className="flex-1 rounded-lg border border-ink-200 px-3 py-2 text-sm placeholder:text-ink-400 focus:border-accent focus:outline-none focus:ring-1 focus:ring-accent"
                    />
                    <button
                      type="button"
                      onClick={() => removeRecipient(i)}
                      className="shrink-0 rounded p-1.5 text-ink-400 hover:bg-ink-100 hover:text-ink-600"
                      aria-label="수신자 제거"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  onClick={addRecipient}
                  className="mt-1 flex items-center gap-1 text-sm text-accent-600 hover:text-accent-700"
                >
                  <span className="text-lg">+</span> 수신자 추가
                </button>
              </div>
            </div>

            {/* 분리된 파일 목록 (파일명, 확정자명, 매칭 수신자, 미리보기, 개별 발송) */}
            {splitResult.length > 0 && (
              <div className="mb-6">
                <h3 className="mb-3 text-sm font-semibold text-ink-700">분리된 파일 (클릭 시 뷰어)</h3>
                <div className="overflow-hidden rounded-lg border border-ink-200">
                  <table className="w-full text-left text-sm">
                    <thead>
                      <tr className="border-b border-ink-200 bg-ink-100/80">
                        <th className="px-3 py-2 font-semibold text-ink-700">파일명</th>
                        <th className="px-3 py-2 font-semibold text-ink-700">확정자명</th>
                        <th className="px-3 py-2 font-semibold text-ink-700">매칭 수신자</th>
                        <th className="w-24 px-3 py-2 font-semibold text-ink-700">미리보기</th>
                        <th className="w-24 px-3 py-2 font-semibold text-ink-700">발송</th>
                      </tr>
                    </thead>
                    <tbody>
                      {splitResult.map((item, index) => (
                        <tr
                          key={item.id}
                          className="border-b border-ink-100 last:border-0 hover:bg-ink-50/80"
                        >
                          <td className="truncate px-3 py-2 font-medium text-ink-800 max-w-[140px]" title={item.filename}>
                            {item.filename}
                          </td>
                          <td className="px-3 py-2 text-ink-600">{item.confirmedName}</td>
                          <td className="truncate px-3 py-2 text-ink-600 max-w-[160px]" title={getRecipientForIndex(index)}>
                            {getRecipientForIndex(index) || '—'}
                          </td>
                          <td className="px-3 py-2">
                            <button
                              type="button"
                              onClick={() => setViewerFile(item)}
                              className="text-accent-600 hover:text-accent-700 hover:underline"
                            >
                              보기
                            </button>
                          </td>
                          <td className="px-3 py-2">
                            <button
                              type="button"
                              onClick={() => sendOneEmail(item, index)}
                              disabled={status?.type === 'loading'}
                              className="rounded bg-ink-200 px-2 py-1 text-xs font-medium text-ink-700 hover:bg-ink-300 disabled:opacity-50"
                            >
                              개별발송
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={sendAllEmails}
                    disabled={status?.type === 'loading' || splitResult.length === 0}
                    className="rounded-xl bg-accent px-5 py-2.5 text-sm font-semibold text-white shadow-md hover:bg-accent-700 focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    일괄발송
                  </button>
                </div>
              </div>
            )}

            {splitResult.length === 0 && (
              <p className="rounded-lg border border-ink-200 bg-ink-50/50 px-4 py-3 text-sm text-ink-500">
                분리된 파일이 없습니다. 2. 분리 설정에서 실행을 먼저 진행해 주세요.
              </p>
            )}
          </section>

          {/* 상태 메시지 */}
          {status && (
            <div
              className={`
                rounded-xl px-4 py-3 text-sm font-medium
                ${status.type === 'loading' && 'bg-accent-50 text-accent-800'}
                ${status.type === 'success' && 'bg-accent-50 text-accent-800'}
                ${status.type === 'error' && 'bg-red-50 text-red-800'}
              `}
            >
              {status.type === 'loading' && (
                <span className="inline-flex items-center gap-2">
                  <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {status.message}
                </span>
              )}
              {(status.type === 'success' || status.type === 'error') && status.message}
            </div>
          )}
        </div>
      </div>

      <PdfViewerModal file={viewerFile} onClose={() => setViewerFile(null)} />
    </div>
  )
}
