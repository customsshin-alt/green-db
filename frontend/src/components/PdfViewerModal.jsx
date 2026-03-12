import React, { useEffect } from 'react'

export default function PdfViewerModal({ file, onClose }) {
  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [onClose])

  if (!file) return null

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-ink-900/60 p-4"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label="PDF 미리보기"
    >
      <div
        className="flex max-h-[90vh] w-full max-w-4xl flex-col rounded-2xl bg-white shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex shrink-0 items-center justify-between border-b border-ink-200 px-4 py-3">
          <h3 className="truncate text-sm font-semibold text-ink-800" title={file.filename}>
            {file.filename}
          </h3>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-ink-500 hover:bg-ink-100 hover:text-ink-700"
            aria-label="닫기"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-4">
          {file.blobUrl ? (
            <iframe
              src={file.blobUrl}
              title={file.filename}
              className="h-[70vh] w-full rounded-lg border border-ink-200"
            />
          ) : (
            <div className="flex h-64 items-center justify-center rounded-lg border border-ink-200 bg-ink-50 text-ink-500">
              미리보기를 사용하려면 분리 실행 후 생성된 파일을 사용하세요.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
