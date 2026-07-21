// 计算尚未翻译的 key:从 en 模块抽已译 key,与 codemod 抽出的 key 求差集。
const fs = require('fs')
const path = require('path')

const langDir = path.join(__dirname, '..', 'src', 'lang')
const have = new Set()
for (const f of ['en.js', 'en-backend.js', 'en-menu.js', 'en-datamanage.js', 'en-extra.js']) {
  const t = fs.readFileSync(path.join(langDir, f), 'utf8')
  const re = /^\s*'((?:[^'\\]|\\.)*)'\s*:/gm // 行首  'key':
  let m
  while ((m = re.exec(t))) have.add(m[1].replace(/\\'/g, "'").replace(/\\\\/g, '\\'))
}
const keys = new Set()
for (const f of process.argv.slice(2)) {
  for (const l of fs.readFileSync(f, 'utf8').split('\n')) if (l.trim()) keys.add(l)
}
const missing = [...keys].filter((k) => !have.has(k)).sort()
fs.writeFileSync('C:/tmp/keys_missing.txt', missing.join('\n'))
console.log('已译 key:', have.size, '| 本次包裹 key:', keys.size, '| 仍缺翻译:', missing.length)
