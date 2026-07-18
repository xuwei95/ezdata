/**
 * 复制文本到剪贴板(健壮版):
 * 1) 安全上下文(https / localhost)优先用 navigator.clipboard;
 * 2) 否则(http://IP 访问时 navigator.clipboard 为 undefined)降级到 textarea + execCommand。
 * 返回 Promise<boolean>,成功 true。
 */
export async function copyToClipboard(text) {
  const str = text == null ? '' : String(text)
  // 安全上下文才有 navigator.clipboard;http://IP 下为 undefined
  if (navigator.clipboard && window.isSecureContext) {
    try {
      await navigator.clipboard.writeText(str)
      return true
    } catch (e) {
      // 权限/焦点等异常时继续走降级
    }
  }
  return fallbackCopy(str)
}

function fallbackCopy(input) {
  const el = document.createElement('textarea')
  const prevFocus = document.activeElement
  el.value = input
  el.setAttribute('readonly', '')
  el.style.contain = 'strict'
  el.style.position = 'absolute'
  el.style.left = '-9999px'
  el.style.fontSize = '12pt' // 防 iOS 缩放
  document.body.append(el)
  const selection = document.getSelection()
  const originalRange = selection.rangeCount > 0 && selection.getRangeAt(0)
  el.select()
  el.selectionStart = 0
  el.selectionEnd = input.length
  let ok = false
  try { ok = document.execCommand('copy') } catch (e) { ok = false }
  el.remove()
  if (originalRange) { selection.removeAllRanges(); selection.addRange(originalRange) }
  if (prevFocus && prevFocus.focus) prevFocus.focus()
  return ok
}

export default copyToClipboard
