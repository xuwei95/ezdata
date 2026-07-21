/**
 * i18n codemod:只改 .vue 的 <template> 块,把中文文本节点与常见属性包成 $t(...),并抽取 key。
 * 幂等:已包裹的(文本含 {{ }}、属性以 : 开头)不会再包。JS/校验/ElMessage 不碰(需手工)。
 *
 * 用法:
 *   node scripts/i18n-codemod.cjs <dir> --dry     # 预览(不写盘)
 *   node scripts/i18n-codemod.cjs <dir>           # 应用 + 抽 key 到 /tmp/i18n_keys.txt
 */
const fs = require('fs')
const path = require('path')
const { parse } = require('@vue/compiler-sfc')

// 常见"值为可见文案"的属性(值含中文才转 :attr="$t(...)")
const ATTRS = [
  'placeholder', 'label', 'title', 'content', 'description',
  'confirm-button-text', 'cancel-button-text', 'active-text', 'inactive-text', 'empty-text',
]

const args = process.argv.slice(2)
const dry = args.includes('--dry')
const targetDir = args.find((a) => !a.startsWith('--'))
if (!targetDir) {
  console.error('需要传入目录,如: node scripts/i18n-codemod.cjs src/views/dataManage')
  process.exit(1)
}

const keys = new Set()
let filesChanged = 0
let textWrapped = 0
let attrWrapped = 0

const escKey = (s) => s.replace(/\\/g, '\\\\').replace(/'/g, "\\'")

function transformTemplate(tpl) {
  let out = tpl
  // 1) 属性:attr="中文" → :attr="$t('中文')";前面不是 : / - / 字母(避免 :placeholder、v-xxx 二次包)
  const attrRe = new RegExp(`(?<![:\\w-])(${ATTRS.join('|')})="([^"{}]*[\\u4e00-\\u9fa5][^"{}]*)"`, 'g')
  out = out.replace(attrRe, (m, a, val) => {
    const v = val.trim().replace(/\s+/g, ' ') // 折叠空白/换行,避免 $t 键含换行(单引号串不能跨行)
    keys.add(v)
    attrWrapped++
    return `:${a}="$t('${escKey(v)}')"`
  })
  // 2) 文本节点:>中文< → >{{ $t('中文') }}<;排除含 { } < > 者(天然避开插值/标签/已包裹)
  const textRe = /(>)([^<>{}]*[一-龥][^<>{}]*)(<)/g
  out = out.replace(textRe, (m, lt, txt, gt) => {
    const v = txt.trim().replace(/\s+/g, ' ') // 折叠空白/换行,避免 $t 键含换行(单引号串不能跨行)
    if (!v) return m
    // 前后空白折叠为单个换行/空格,保持排版但不影响 key
    const pre = /^\s/.test(txt) ? ' ' : ''
    const post = /\s$/.test(txt) ? ' ' : ''
    keys.add(v)
    textWrapped++
    return `${lt}${pre}{{ $t('${escKey(v)}') }}${post}${gt}`
  })
  return out
}

function processFile(file) {
  const src = fs.readFileSync(file, 'utf8')
  let descriptor
  try {
    ;({ descriptor } = parse(src))
  } catch (e) {
    console.warn('  跳过(解析失败)', file, e.message)
    return
  }
  if (!descriptor.template) return
  const { start, end } = descriptor.template.loc
  const tpl = src.slice(start.offset, end.offset)
  const newTpl = transformTemplate(tpl)
  if (newTpl === tpl) return
  const newSrc = src.slice(0, start.offset) + newTpl + src.slice(end.offset)
  if (!dry) fs.writeFileSync(file, newSrc, 'utf8')
  filesChanged++
  console.log('  changed', path.relative(process.cwd(), file))
}

function walk(dir) {
  for (const name of fs.readdirSync(dir)) {
    const p = path.join(dir, name)
    const st = fs.statSync(p)
    if (st.isDirectory()) walk(p)
    else if (name.endsWith('.vue')) processFile(p)
  }
}

walk(targetDir)
console.log(`\n${dry ? '[DRY] ' : ''}文件改动 ${filesChanged} | 文本包裹 ${textWrapped} | 属性包裹 ${attrWrapped} | 去重 key ${keys.size}`)
if (!dry) {
  fs.writeFileSync('/tmp/i18n_keys.txt', [...keys].sort().join('\n'), 'utf8')
  console.log('抽取的 key → /tmp/i18n_keys.txt')
}
